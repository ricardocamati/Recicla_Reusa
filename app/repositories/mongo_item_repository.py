from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection

from app.exceptions import ConflitoEstadoError, ReferenciaAtivaError
from app.models.item import EventoHistorico, Item
from app.schemas.item import FiltrosItem


class MongoItemRepository:
    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        *,
        criar_indices: bool = True,
        colecao_interesses: Collection[dict[str, Any]] | None = None,
    ) -> None:
        self._colecao = colecao
        self._colecao_interesses = colecao_interesses
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
    ) -> list[Item]:
        dados = filtros.model_dump()
        dados.pop("cidade", None)
        consulta: dict[str, Any] = {
            campo: valor for campo, valor in dados.items() if valor is not None
        }
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

    def buscar_por_id(self, item_id: str) -> Item | None:
        object_id = self._converter_id(item_id)
        if object_id is None:
            return None
        documento = self._colecao.find_one({"_id": object_id})
        return self._para_modelo(documento) if documento else None

    def atualizar(self, item: Item, *, status_esperado: str | None = None) -> Item:
        if item.id is None:
            raise ValueError("Item sem identificador não pode ser atualizado")
        self._normalizar_datas(item)
        filtro: dict[str, Any] = {"_id": ObjectId(item.id)}
        if self._colecao_interesses is not None:
            atual = self._colecao.find_one(filtro, {"destino": 1})
            if (atual is not None and atual.get("destino") != item.destino
                    and self._colecao_interesses.count_documents({"item_id": ObjectId(item.id)})):
                raise ConflitoEstadoError()
        if status_esperado is not None:
            filtro["status"] = status_esperado
        # Campos internos de seleção pertencem ao ciclo de interesses.
        # Uma edição comum não pode apagá-los por substituição do documento.
        resultado = self._colecao.update_one(filtro, {"$set": self._para_documento(item)})
        if status_esperado is not None and resultado.matched_count == 0:
            raise ConflitoEstadoError()
        return item

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
