from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError, DuplicateKeyError, InvalidOperation, PyMongoError

from app.exceptions import EncaminhamentoError
from app.models.encaminhamento import Encaminhamento, EventoEncaminhamento
from app.models.notificacao import EventoNotificacao
from app.repositories.notificacao_documento import montar_documento, registrar

ATIVO = "entrega_prevista"
ENCERRADOS = ("cancelado", "nao_recebido", "recebido")


class MongoEncaminhamentoRepository:
    """Tentativas de entrega de descarte em um ponto de coleta."""

    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        colecao_itens: Collection[dict[str, Any]],
        colecao_pontos: Collection[dict[str, Any]],
        *,
        criar_indices: bool = True,
        colecao_notificacoes: Collection[dict[str, Any]] | None = None,
    ) -> None:
        self._colecao = colecao
        self._colecao_itens = colecao_itens
        self._colecao_pontos = colecao_pontos
        self._colecao_notificacoes = colecao_notificacoes
        if criar_indices:
            self.criar_indices()

    def criar_indices(self) -> None:
        self._colecao.create_index("item_id", name="encaminhamento_item")
        self._colecao.create_index(
            [("ponto_id", 1), ("status", 1)], name="encaminhamento_ponto_status"
        )
        self._colecao.create_index(
            "item_id",
            name="encaminhamento_ativo_unico",
            unique=True,
            partialFilterExpression={"status": ATIVO},
        )

    # ---------------------------------------------------------------- leitura

    def buscar_por_id(self, encaminhamento_id: str) -> Encaminhamento | None:
        oid = self._id(encaminhamento_id)
        documento = self._colecao.find_one({"_id": oid}) if oid else None
        return self._para_modelo(documento) if documento else None

    def listar(
        self,
        usuario_id: str,
        *,
        escopo: str = "autor",
        ponto_id: str | None = None,
        item_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[Encaminhamento]:
        filtro: dict[str, Any] = {}
        if escopo == "operador":
            pontos = [
                str(doc["_id"])
                for doc in self._colecao_pontos.find(
                    {"responsavel_id": self._id_required(usuario_id, 400, "Usuário inválido")},
                    {"_id": 1},
                )
            ]
            if ponto_id is not None:
                if ponto_id not in pontos:
                    raise EncaminhamentoError(403, "Ponto não pertence a este operador")
                pontos = [ponto_id]
            filtro["ponto_id"] = {"$in": [ObjectId(p) for p in pontos]}
        else:
            filtro["autor_id"] = self._id_required(usuario_id, 400, "Usuário inválido")
            if ponto_id is not None:
                filtro["ponto_id"] = self._id_required(ponto_id, 400, "Ponto inválido")
        if item_id is not None:
            filtro["item_id"] = self._id_required(item_id, 400, "Item inválido")
        if status is not None:
            filtro["status"] = status
        cursor = (
            self._colecao.find(filtro)
            .sort([("data_modificacao", -1), ("_id", -1)])
            .skip(max(offset, 0))
            .limit(min(max(limite, 1), 100))
        )
        return [self._para_modelo(doc) for doc in cursor]

    def listar_previstos_do_ponto(self, ponto_id: str) -> list[dict[str, Any]]:
        oid = self._id(ponto_id)
        if oid is None:
            return []
        return list(self._colecao.find({"ponto_id": oid, "status": ATIVO}))

    def avisar_ponto_inativado(self, ponto_id: str, instante: datetime) -> int:
        """Avisa autores com entrega prevista que o ponto foi desativado."""
        if self._colecao_notificacoes is None:
            return 0
        oid = self._id(ponto_id)
        if oid is None:
            return 0
        ponto = self._colecao_pontos.find_one({"_id": oid})
        avisados = 0
        for tentativa in self._colecao.find({"ponto_id": oid, "status": ATIVO}):
            item = self._colecao_itens.find_one({"_id": tentativa["item_id"]})
            if item is None:
                continue
            self._avisar(
                None,
                item,
                ponto or {},
                tipo="ponto_inativado",
                titulo="Ponto desativado",
                mensagem="O ponto de coleta da sua entrega foi desativado; escolha outro ponto.",
                evento=f"encaminhamento:{tentativa['_id']}:ponto_inativado",
                instante=instante,
                destinatario=tentativa["autor_id"],
            )
            avisados += 1
        return avisados

    # ------------------------------------------------------------- comandos

    def criar(
        self,
        item_id: str,
        autor_id: str,
        ponto_id: str,
        instante: datetime,
    ) -> Encaminhamento:
        item_oid = self._id_required(item_id, 404, "Item não encontrado")
        autor_oid = self._id_required(autor_id, 400, "Usuário inválido")
        ponto_oid = self._id_required(ponto_id, 404, "Ponto de coleta não encontrado")

        def operacao(session):
            item = self._colecao_itens.find_one({"_id": item_oid}, session=session)
            if item is None:
                raise EncaminhamentoError(404, "Item não encontrado")
            if item.get("proprietario_id") != autor_oid:
                raise EncaminhamentoError(403, "Somente o proprietário encaminha o item")
            if item.get("destino") != "descarte":
                raise EncaminhamentoError(400, "Somente descarte é encaminhado a ponto")
            if item.get("status") != "aguardando_ponto":
                raise EncaminhamentoError(409, "Item não está aguardando um ponto")
            ponto = self._colecao_pontos.find_one({"_id": ponto_oid}, session=session)
            if ponto is None:
                raise EncaminhamentoError(404, "Ponto de coleta não encontrado")
            if not ponto.get("ativo", True):
                raise EncaminhamentoError(409, "Ponto de coleta está inativo")
            if item.get("categoria") not in (ponto.get("categorias_aceitas") or []):
                raise EncaminhamentoError(409, "Ponto não aceita a categoria do item")
            if self._colecao.find_one({"item_id": item_oid, "status": ATIVO}, session=session):
                raise EncaminhamentoError(409, "Item já possui entrega prevista")

            doc = {
                "_id": ObjectId(),
                "item_id": item_oid,
                "autor_id": autor_oid,
                "ponto_id": ponto_oid,
                "status": ATIVO,
                "motivo": None,
                "historico": [
                    {
                        "status": ATIVO,
                        "data_evento": instante,
                        "ator_id": autor_oid,
                        "motivo": None,
                    }
                ],
                "data_adicao": instante,
                "data_modificacao": instante,
            }
            self._colecao.insert_one(doc, session=session)
            self._mover_item(
                session, item, ATIVO, autor_oid, instante, ponto_oid=ponto_oid
            )
            self._avisar(
                session,
                item,
                ponto,
                tipo="entrega_prevista",
                titulo="Entrega prevista",
                mensagem="Uma entrega foi prevista no seu ponto de coleta.",
                evento=f"encaminhamento:{doc['_id']}:prevista",
                instante=instante,
                destinatario=ponto.get("responsavel_id"),
            )
            return self._para_modelo(doc)

        return self._transacao(operacao)

    def executar(
        self,
        encaminhamento_id: str,
        acao: str,
        usuario_id: str,
        instante: datetime,
        *,
        motivo: str | None = None,
        novo_ponto_id: str | None = None,
    ) -> Encaminhamento:
        if acao == "cancelar":
            return self._encerrar(encaminhamento_id, usuario_id, instante, status="cancelado")
        if acao == "trocar":
            return self._trocar(encaminhamento_id, usuario_id, instante, novo_ponto_id, motivo)
        if acao == "receber":
            return self._receber(encaminhamento_id, usuario_id, instante)
        if acao == "nao_recebido":
            return self._nao_recebido(encaminhamento_id, usuario_id, instante, motivo)
        raise EncaminhamentoError(400, "Ação desconhecida")

    # ---------------------------------------------------------- implementação

    def _encerrar(self, encaminhamento_id, usuario_id, instante, *, status: str) -> Encaminhamento:
        oid = self._id_required(encaminhamento_id, 404, "Encaminhamento não encontrado")
        autor_oid = self._id_required(usuario_id, 400, "Usuário inválido")

        def operacao(session):
            doc = self._colecao.find_one({"_id": oid}, session=session)
            if doc is None:
                raise EncaminhamentoError(404, "Encaminhamento não encontrado")
            if doc.get("autor_id") != autor_oid:
                raise EncaminhamentoError(403, "Somente o autor cancela a entrega")
            if doc.get("status") != ATIVO:
                raise EncaminhamentoError(409, "Entrega já encerrada")
            item = self._colecao_itens.find_one({"_id": doc["item_id"]}, session=session)
            self._atualizar_tentativa(session, doc, status, autor_oid, instante, None)
            self._mover_item(session, item, "aguardando_ponto", autor_oid, instante, ponto_oid=None)
            return self._para_modelo(doc)

        return self._transacao(operacao)

    def _trocar(self, encaminhamento_id, usuario_id, instante, novo_ponto_id, motivo):
        if not novo_ponto_id:
            raise EncaminhamentoError(400, "Troca exige novo ponto")
        oid = self._id_required(encaminhamento_id, 404, "Encaminhamento não encontrado")
        autor_oid = self._id_required(usuario_id, 400, "Usuário inválido")
        novo_oid = self._id_required(novo_ponto_id, 404, "Ponto de coleta não encontrado")

        def operacao(session):
            doc = self._colecao.find_one({"_id": oid}, session=session)
            if doc is None:
                raise EncaminhamentoError(404, "Encaminhamento não encontrado")
            if doc.get("autor_id") != autor_oid:
                raise EncaminhamentoError(403, "Somente o autor troca o ponto")
            if doc.get("status") != ATIVO:
                raise EncaminhamentoError(409, "Entrega já encerrada")
            if doc.get("ponto_id") == novo_oid:
                raise EncaminhamentoError(409, "Item já está previsto neste ponto")
            item = self._colecao_itens.find_one({"_id": doc["item_id"]}, session=session)
            ponto = self._colecao_pontos.find_one({"_id": novo_oid}, session=session)
            if ponto is None:
                raise EncaminhamentoError(404, "Ponto de coleta não encontrado")
            if not ponto.get("ativo", True):
                raise EncaminhamentoError(409, "Ponto de coleta está inativo")
            if item.get("categoria") not in (ponto.get("categorias_aceitas") or []):
                raise EncaminhamentoError(409, "Ponto não aceita a categoria do item")

            self._atualizar_tentativa(session, doc, "cancelado", autor_oid, instante, motivo)
            novo = {
                "_id": ObjectId(),
                "item_id": doc["item_id"],
                "autor_id": autor_oid,
                "ponto_id": novo_oid,
                "status": ATIVO,
                "motivo": None,
                "historico": [
                    {
                        "status": ATIVO,
                        "data_evento": instante,
                        "ator_id": autor_oid,
                        "motivo": motivo,
                    }
                ],
                "data_adicao": instante,
                "data_modificacao": instante,
            }
            self._colecao.insert_one(novo, session=session)
            self._mover_item(session, item, ATIVO, autor_oid, instante, ponto_oid=novo_oid)
            self._avisar(
                session,
                item,
                ponto,
                tipo="entrega_prevista",
                titulo="Entrega prevista",
                mensagem="Uma entrega foi prevista no seu ponto de coleta.",
                evento=f"encaminhamento:{novo['_id']}:prevista",
                instante=instante,
                destinatario=ponto.get("responsavel_id"),
            )
            return self._para_modelo(novo)

        return self._transacao(operacao)

    def _receber(self, encaminhamento_id, usuario_id, instante) -> Encaminhamento:
        oid = self._id_required(encaminhamento_id, 404, "Encaminhamento não encontrado")
        operador_oid = self._id_required(usuario_id, 400, "Usuário inválido")

        def operacao(session):
            doc = self._colecao.find_one({"_id": oid}, session=session)
            if doc is None:
                raise EncaminhamentoError(404, "Encaminhamento não encontrado")
            ponto = self._colecao_pontos.find_one({"_id": doc["ponto_id"]}, session=session)
            if ponto is None or ponto.get("responsavel_id") != operador_oid:
                raise EncaminhamentoError(403, "Somente o operador do ponto confirma")
            item = self._colecao_itens.find_one({"_id": doc["item_id"]}, session=session)
            if doc.get("status") == "recebido" and item and item.get("status") == "recebido":
                return self._para_modelo(doc)
            if doc.get("status") != ATIVO:
                raise EncaminhamentoError(409, "Entrega já encerrada")
            self._atualizar_tentativa(session, doc, "recebido", operador_oid, instante, None)
            self._mover_item(session, item, "recebido", operador_oid, instante, ponto_oid=doc["ponto_id"])
            self._avisar(
                session,
                item,
                ponto,
                tipo="item_recebido",
                titulo="Item recebido",
                mensagem="O ponto confirmou o recebimento do seu item.",
                evento=f"encaminhamento:{doc['_id']}:recebido",
                instante=instante,
                destinatario=doc.get("autor_id"),
            )
            return self._para_modelo(doc)

        return self._transacao(operacao)

    def _nao_recebido(self, encaminhamento_id, usuario_id, instante, motivo) -> Encaminhamento:
        if not (motivo or "").strip():
            raise EncaminhamentoError(400, "Não recebido exige motivo")
        oid = self._id_required(encaminhamento_id, 404, "Encaminhamento não encontrado")
        operador_oid = self._id_required(usuario_id, 400, "Usuário inválido")

        def operacao(session):
            doc = self._colecao.find_one({"_id": oid}, session=session)
            if doc is None:
                raise EncaminhamentoError(404, "Encaminhamento não encontrado")
            ponto = self._colecao_pontos.find_one({"_id": doc["ponto_id"]}, session=session)
            if ponto is None or ponto.get("responsavel_id") != operador_oid:
                raise EncaminhamentoError(403, "Somente o operador do ponto registra a falha")
            if doc.get("status") != ATIVO:
                raise EncaminhamentoError(409, "Entrega já encerrada")
            item = self._colecao_itens.find_one({"_id": doc["item_id"]}, session=session)
            self._atualizar_tentativa(session, doc, "nao_recebido", operador_oid, instante, motivo)
            self._mover_item(session, item, "aguardando_ponto", operador_oid, instante, ponto_oid=None)
            self._avisar(
                session,
                item,
                ponto,
                tipo="item_nao_recebido",
                titulo="Entrega não recebida",
                mensagem=f"A entrega não foi recebida: {motivo.strip()}",
                evento=f"encaminhamento:{doc['_id']}:nao_recebido",
                instante=instante,
                destinatario=doc.get("autor_id"),
            )
            return self._para_modelo(doc)

        return self._transacao(operacao)

    # ------------------------------------------------------------- auxiliares

    def _atualizar_tentativa(self, session, doc, status, ator_oid, instante, motivo) -> None:
        evento = {
            "status": status,
            "data_evento": instante,
            "ator_id": ator_oid,
            "motivo": motivo,
        }
        self._colecao.update_one(
            {"_id": doc["_id"], "status": doc["status"]},
            {
                "$set": {"status": status, "motivo": motivo, "data_modificacao": instante},
                "$push": {"historico": evento},
            },
            session=session,
        )
        doc["status"] = status
        doc["motivo"] = motivo
        doc["data_modificacao"] = instante
        doc.setdefault("historico", []).append(evento)

    def _mover_item(self, session, item, status, ator_oid, instante, *, ponto_oid) -> None:
        campos: dict[str, Any] = {"status": status, "data_modificacao": instante}
        if ponto_oid is None:
            campos["ponto_coleta_id"] = None
        else:
            campos["ponto_coleta_id"] = ponto_oid
        evento = {
            "etapa": f"encaminhamento_{status}",
            "status": status,
            "data_evento": instante,
            "responsavel_id": ator_oid,
            "observacao": None,
        }
        self._colecao_itens.update_one(
            {"_id": item["_id"]},
            {"$set": campos, "$push": {"historico": evento}},
            session=session,
        )

    def _avisar(self, session, item, ponto, *, tipo, titulo, mensagem, evento, instante, destinatario):
        if self._colecao_notificacoes is None or destinatario is None:
            return
        registro = montar_documento(
            usuario_id=str(destinatario),
            item_id=str(item["_id"]),
            interesse_id=None,
            evento=EventoNotificacao(
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                evento_id=evento,
            ),
            instante=instante,
        )
        registrar(self._colecao_notificacoes, registro, session=session)

    def _transacao(self, operacao: Callable):
        try:
            with self._colecao.database.client.start_session() as session:
                return session.with_transaction(operacao)
        except EncaminhamentoError:
            raise
        except DuplicateKeyError as erro:
            raise EncaminhamentoError(409, "Item já possui entrega prevista") from erro
        except (PyMongoError, ConfigurationError, InvalidOperation, NotImplementedError) as erro:
            raise EncaminhamentoError(503, "Operação temporariamente indisponível") from erro

    @classmethod
    def _para_modelo(cls, doc: dict[str, Any]) -> Encaminhamento:
        return Encaminhamento(
            id=str(doc["_id"]),
            item_id=str(doc["item_id"]),
            autor_id=str(doc["autor_id"]),
            ponto_id=str(doc["ponto_id"]),
            status=doc["status"],
            motivo=doc.get("motivo"),
            historico=[
                EventoEncaminhamento(
                    status=evento["status"],
                    data_evento=cls._data(evento["data_evento"]),
                    ator_id=str(evento["ator_id"]),
                    motivo=evento.get("motivo"),
                )
                for evento in doc.get("historico", [])
            ],
            data_adicao=cls._data(doc["data_adicao"]),
            data_modificacao=cls._data(doc["data_modificacao"]),
        )

    @staticmethod
    def _data(valor: datetime) -> datetime:
        return valor if valor.tzinfo else valor.replace(tzinfo=UTC)

    @staticmethod
    def _id(valor: str) -> ObjectId | None:
        try:
            return ObjectId(valor)
        except (InvalidId, TypeError):
            return None

    @classmethod
    def _id_required(cls, valor: str, status_code: int, detail: str) -> ObjectId:
        oid = cls._id(valor)
        if oid is None:
            raise EncaminhamentoError(status_code, detail)
        return oid
