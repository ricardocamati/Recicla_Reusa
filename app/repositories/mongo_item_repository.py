import re
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError, InvalidOperation, PyMongoError

from app.exceptions import ConflitoEstadoError, FluxoItemError, ReferenciaAtivaError
from app.models.item import EventoHistorico, Item
from app.models.notificacao import EventoNotificacao
from app.repositories.notificacao_documento import montar_documento, registrar
from app.schemas.item import FiltrosItem


class MongoItemRepository:
    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        *,
        criar_indices: bool = True,
        colecao_interesses: Collection[dict[str, Any]] | None = None,
        colecao_notificacoes: Collection[dict[str, Any]] | None = None,
    ) -> None:
        self._colecao = colecao
        self._colecao_interesses = colecao_interesses
        self._colecao_notificacoes = colecao_notificacoes
        if criar_indices:
            self.criar_indices()

    def criar_indices(self) -> None:
        self._colecao.create_index("proprietario_id", name="item_proprietario")
        self._colecao.create_index("categoria", name="item_categoria")
        self._colecao.create_index("condicao", name="item_condicao")
        self._colecao.create_index("destino", name="item_destino")
        self._colecao.create_index("status", name="item_status")

    def criar(self, item: Item) -> Item:
        self._normalizar_datas(item)
        resultado = self._colecao.insert_one(self._para_documento(item))
        item.id = str(resultado.inserted_id)
        return item

    def listar(
        self,
        filtros: FiltrosItem,
        *,
        proprietario_ids: set[str] | None = None,
        offset: int = 0,
        limite: int = 20,
        somente_catalogo: bool = False,
    ) -> list[Item]:
        dados = filtros.model_dump()
        for campo in ("cidade", "texto", "preco_min", "preco_max", "incluir_reservados"):
            dados.pop(campo, None)
        consulta: dict[str, Any] = {
            campo: valor for campo, valor in dados.items() if valor is not None
        }
        if filtros.texto:
            termo = re.escape(filtros.texto.strip())
            consulta["$or"] = [
                {"titulo": {"$regex": termo, "$options": "i"}},
                {"descricao": {"$regex": termo, "$options": "i"}},
            ]
        faixa: dict[str, Any] = {}
        if filtros.preco_min is not None:
            faixa["$gte"] = filtros.preco_min
        if filtros.preco_max is not None:
            faixa["$lte"] = filtros.preco_max
        if faixa:
            consulta["valor"] = faixa
        if somente_catalogo:
            consulta["destino"] = {"$ne": "descarte"}
            consulta["status"] = (
                {"$in": ["disponivel", "reservado"]}
                if filtros.incluir_reservados
                else "disponivel"
            )
        if proprietario_ids is not None:
            object_ids = [
                object_id
                for usuario_id in proprietario_ids
                if (object_id := self._converter_id(usuario_id)) is not None
            ]
            if not object_ids:
                return []
            consulta["proprietario_id"] = {"$in": object_ids}
        documentos = (
            self._colecao.find(consulta)
            .sort("data_adicao", -1)
            .skip(offset)
            .limit(limite)
        )
        return [self._para_modelo(documento) for documento in documentos]

    def listar_por_proprietario(
        self,
        proprietario_id: str,
        statuses: tuple[str, ...],
        *,
        offset: int = 0,
        limite: int = 20,
    ) -> list[Item]:
        object_id = self._converter_id(proprietario_id)
        if object_id is None:
            return []
        documentos = (
            self._colecao.find(
                {"proprietario_id": object_id, "status": {"$in": list(statuses)}}
            )
            .sort("data_adicao", -1)
            .skip(offset)
            .limit(limite)
        )
        return [self._para_modelo(documento) for documento in documentos]

    def buscar_por_id(self, item_id: str) -> Item | None:
        object_id = self._converter_id(item_id)
        if object_id is None:
            return None
        documento = self._colecao.find_one({"_id": object_id})
        return self._para_modelo(documento) if documento else None

    def atualizar(
        self,
        item: Item,
        *,
        status_esperado: str | None = None,
        notificacao: EventoNotificacao | None = None,
    ) -> Item:
        if item.id is None:
            raise ValueError("Item sem identificador não pode ser atualizado")
        self._normalizar_datas(item)
        object_id = ObjectId(item.id)
        filtro: dict[str, Any] = {"_id": object_id}
        if status_esperado is not None:
            filtro["status"] = status_esperado
        # Campos internos de seleção pertencem ao ciclo de interesses.
        # Uma edição comum não pode apagá-los por substituição do documento.
        documento = self._para_documento(item)

        if notificacao is not None and self._colecao_notificacoes is not None:
            self._atualizar_com_avisos(item, object_id, filtro, documento, notificacao)
            return item

        if self._colecao_interesses is not None:
            atual = self._colecao.find_one(filtro, {"destino": 1})
            if (atual is not None and atual.get("destino") != item.destino
                    and self._colecao_interesses.count_documents({"item_id": object_id})):
                raise ConflitoEstadoError()
        resultado = self._colecao.update_one(filtro, {"$set": documento})
        if status_esperado is not None and resultado.matched_count == 0:
            raise ConflitoEstadoError()
        return item

    def _atualizar_com_avisos(
        self,
        item: Item,
        object_id: ObjectId,
        filtro: dict[str, Any],
        documento: dict[str, Any],
        notificacao: EventoNotificacao,
    ) -> None:
        """Grava a transição e os avisos na mesma transação."""

        def operacao(session):
            if self._colecao_interesses is not None:
                atual = self._colecao.find_one(
                    {"_id": object_id}, {"destino": 1}, session=session
                )
                if (atual is not None and atual.get("destino") != item.destino
                        and self._colecao_interesses.count_documents(
                            {"item_id": object_id}, session=session
                        )):
                    raise ConflitoEstadoError()
            resultado = self._colecao.update_one(
                filtro, {"$set": documento}, session=session
            )
            if filtro.get("status") is not None and resultado.matched_count == 0:
                raise ConflitoEstadoError()
            self._avisar_interessados(session, item, notificacao)

        with self._colecao.database.client.start_session() as sessao:
            try:
                sessao.with_transaction(operacao)
            except (PyMongoError, ConfigurationError, InvalidOperation, NotImplementedError) as erro:
                raise FluxoItemError(
                    503, "Operação temporariamente indisponível"
                ) from erro

    def _avisar_interessados(self, session, item: Item, evento: EventoNotificacao) -> None:
        if self._colecao_interesses is None or self._colecao_notificacoes is None:
            return
        documentos = self._colecao_interesses.find(
            {
                "item_id": ObjectId(item.id),
                "status": {"$in": ["pendente", "selecionado"]},
            },
            {"usuario_id": 1},
            session=session,
        )
        for documento in documentos:
            registro = montar_documento(
                usuario_id=str(documento["usuario_id"]),
                item_id=item.id or "",
                interesse_id=str(documento["_id"]),
                evento=evento,
                instante=item.data_modificacao,
            )
            registrar(self._colecao_notificacoes, registro, session=session)

    def excluir(self, item_id: str) -> None:
        object_id = self._converter_id(item_id)
        if object_id is not None:
            if (self._colecao_interesses is not None
                    and self._colecao_interesses.count_documents({"item_id": object_id})):
                raise ReferenciaAtivaError()
            self._colecao.delete_one({"_id": object_id})

    @staticmethod
    def _converter_id(item_id: str) -> ObjectId | None:
        try:
            return ObjectId(item_id)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    def _para_documento(item: Item) -> dict[str, Any]:
        documento = asdict(item)
        documento.pop("id")
        try:
            documento["proprietario_id"] = ObjectId(documento["proprietario_id"])
        except (InvalidId, TypeError) as erro:
            raise ValueError("proprietario_id deve ser um ObjectId válido") from erro
        for evento in documento["historico"]:
            try:
                evento["responsavel_id"] = ObjectId(evento["responsavel_id"])
            except (InvalidId, TypeError) as erro:
                raise ValueError("responsavel_id deve ser um ObjectId válido") from erro
        for campo in ("ponto_coleta_id", "beneficiario_id", "comprador_id"):
            if documento.get(campo) is not None:
                try:
                    documento[campo] = ObjectId(documento[campo])
                except (InvalidId, TypeError) as erro:
                    raise ValueError(f"{campo} deve ser um ObjectId válido") from erro
        return documento

    @classmethod
    def _normalizar_datas(cls, item: Item) -> None:
        item.data_adicao = cls._normalizar_data(item.data_adicao)
        item.data_modificacao = cls._normalizar_data(item.data_modificacao)
        for evento in item.historico:
            evento.data_evento = cls._normalizar_data(evento.data_evento)

    @staticmethod
    def _normalizar_data(instante: datetime) -> datetime:
        instante_utc = (
            instante.replace(tzinfo=UTC)
            if instante.tzinfo is None
            else instante.astimezone(UTC)
        )
        return instante_utc.replace(microsecond=instante_utc.microsecond // 1000 * 1000)

    @staticmethod
    def _para_modelo(documento: dict[str, Any]) -> Item:
        dados = dict(documento)
        dados.pop("interesse_aceito_id", None)
        dados.pop("_lock_interesses", None)
        dados["id"] = str(dados.pop("_id"))
        dados["proprietario_id"] = str(dados["proprietario_id"])
        dados["data_adicao"] = MongoItemRepository._normalizar_data(dados["data_adicao"])
        dados["data_modificacao"] = MongoItemRepository._normalizar_data(dados["data_modificacao"])
        dados.setdefault("especificacoes", {})
        for campo in ("ponto_coleta_id", "beneficiario_id", "comprador_id"):
            valor = dados.get(campo)
            dados[campo] = str(valor) if valor is not None else None
        dados["historico"] = [
            EventoHistorico(
                etapa=evento["etapa"],
                status=evento["status"],
                data_evento=MongoItemRepository._normalizar_data(evento["data_evento"]),
                responsavel_id=str(evento["responsavel_id"]),
                observacao=evento.get("observacao"),
            )
            for evento in dados.get("historico", [])
        ]
        return Item(**dados)
