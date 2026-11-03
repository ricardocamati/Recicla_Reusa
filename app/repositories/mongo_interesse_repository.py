from datetime import UTC, datetime
from typing import Any, Callable

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError, DuplicateKeyError, InvalidOperation, PyMongoError

from app.exceptions import InteresseError
from app.models.interesse import EventoInteresse, Interesse
from app.models.notificacao import EventoNotificacao, evento_de_status_item
from app.repositories.notificacao_documento import montar_documento, registrar

ACOES_DO_INTERESSADO = {"desistir", "retomar"}
ACOES_DO_PROPRIETARIO = {"selecionar", "recusar", "liberar", "reabrir"}


class MongoInteresseRepository:
    def __init__(self, colecao: Collection[dict[str, Any]], colecao_itens: Collection[dict[str, Any]], colecao_usuarios: Collection[dict[str, Any]], *, criar_indices: bool = True, colecao_notificacoes: Collection[dict[str, Any]] | None = None) -> None:
        self._colecao = colecao
        self._colecao_itens = colecao_itens
        self._colecao_usuarios = colecao_usuarios
        self._colecao_notificacoes = colecao_notificacoes
        if criar_indices:
            self.criar_indices()

    def criar_indices(self) -> None:
        self._colecao.create_index([("item_id", 1), ("usuario_id", 1)], unique=True, name="interesse_item_usuario_unico")
        self._colecao.create_index([("usuario_id", 1), ("data_adicao", -1)], name="interesse_usuario_data")
        self._colecao.create_index([("item_id", 1), ("data_adicao", -1)], name="interesse_item_data")

    def buscar_usuario(self, usuario_id: str) -> dict[str, Any] | None:
        oid = self._id(usuario_id)
        return self._colecao_usuarios.find_one({"_id": oid}) if oid else None

    def buscar_item(self, item_id: str) -> dict[str, Any] | None:
        oid = self._id(item_id)
        return self._colecao_itens.find_one({"_id": oid}) if oid else None

    def buscar_por_id(self, interesse_id: str) -> Interesse | None:
        oid = self._id(interesse_id)
        doc = self._colecao.find_one({"_id": oid}) if oid else None
        return self._para_modelo(doc) if doc else None

    def buscar_por_par(self, item_id: str, usuario_id: str) -> Interesse | None:
        item_oid, usuario_oid = self._id(item_id), self._id(usuario_id)
        if item_oid is None or usuario_oid is None:
            return None
        doc = self._colecao.find_one({"item_id": item_oid, "usuario_id": usuario_oid})
        return self._para_modelo(doc) if doc else None

    def listar(self, usuario_id: str, *, escopo: str = "meus", item_id: str | None = None, status: str | None = None, offset: int = 0, limite: int = 20) -> list[Interesse]:
        actor = self._id(usuario_id)
        if actor is None:
            return []
        query: dict[str, Any] = {}
        if escopo == "meus":
            query["usuario_id"] = actor
        else:
            item_ids = [d["_id"] for d in self._colecao_itens.find({"proprietario_id": actor}, {"_id": 1})]
            if not item_ids:
                return []
            query["item_id"] = {"$in": item_ids}
        if item_id is not None:
            oid = self._id(item_id)
            if oid is None:
                return []
            if isinstance(query.get("item_id"), dict) and oid not in query["item_id"]["$in"]:
                return []
            query["item_id"] = oid
        if status is not None:
            query["status"] = status
        docs = self._colecao.find(query).sort([("data_adicao", -1), ("_id", -1)]).skip(offset).limit(limite)
        return [self._para_modelo(doc) for doc in docs]

    def criar(self, interesse: Interesse) -> Interesse:
        item_oid = self._required_id(interesse.item_id, "Item não encontrado", 404)
        usuario_oid = self._required_id(interesse.usuario_id, "Usuário não encontrado", 404)
        instante = self._data(interesse.data_adicao)
        doc = {
            "item_id": item_oid,
            "usuario_id": usuario_oid,
            "status": "pendente",
            "tentativa": 1,
            "motivo": None,
            "preco_selecionado": None,
            "historico": [
                {
                    "status": "pendente",
                    "data_evento": instante,
                    "ator_id": usuario_oid,
                    "motivo": None,
                }
            ],
            "data_adicao": instante,
            "data_modificacao": instante,
        }

        def operacao(session):
            usuario = self._colecao_usuarios.find_one({"_id": usuario_oid}, session=session)
            item = self._colecao_itens.find_one({"_id": item_oid}, session=session)
            self._validar_criacao(item, usuario, interesse.usuario_id)
            resultado = self._colecao.insert_one(doc, session=session)
            interesse.id = str(resultado.inserted_id)
            interesse.data_adicao = doc["data_adicao"]
            interesse.data_modificacao = doc["data_modificacao"]
            interesse.historico = [EventoInteresse("pendente", instante, interesse.usuario_id)]
            return interesse

        try:
            return self._transacao(operacao)
        except DuplicateKeyError as erro:
            raise InteresseError(
                409, "Já existe relação deste usuário com o item; retome ou aguarde a decisão"
            ) from erro

    def executar(
        self,
        interesse_id: str,
        acao: str,
        usuario_id: str,
        instante: datetime,
        *,
        motivo: str | None = None,
        notificacao: EventoNotificacao | None = None,
    ) -> Interesse:
        """Executa uma ação do ciclo do interesse em uma transação única."""
        if acao not in ACOES_DO_INTERESSADO | ACOES_DO_PROPRIETARIO:
            raise InteresseError(400, "Ação de interesse inválida")
        interesse_oid = self._required_id(interesse_id, "Interesse não encontrado", 404)
        actor_oid = self._required_id(usuario_id, "Usuário não encontrado", 404)
        instante = self._data(instante)

        def operacao(session):
            doc = self._colecao.find_one({"_id": interesse_oid}, session=session)
            if doc is None:
                raise InteresseError(404, "Interesse não encontrado")
            item = self._colecao_itens.find_one({"_id": doc["item_id"]}, session=session)
            if item is None:
                raise InteresseError(404, "Item não encontrado")
            dono = item.get("proprietario_id") == actor_oid
            interessado = doc.get("usuario_id") == actor_oid
            if acao in ACOES_DO_PROPRIETARIO and not dono:
                raise InteresseError(403, "Somente o proprietário pode executar esta ação")
            if acao in ACOES_DO_INTERESSADO and not interessado:
                raise InteresseError(403, "Somente o interessado pode executar esta ação")

            atual = doc.get("status")
            alvo = atual
            motivo_limpo = (motivo or "").strip() or None

            if acao == "selecionar":
                if atual != "pendente":
                    raise InteresseError(400, "Só interesse pendente pode ser selecionado")
                self._reservar_item(session, doc, item, interesse_oid, actor_oid, instante)
                alvo = "selecionado"
            elif acao == "recusar":
                if atual != "pendente":
                    raise InteresseError(400, "Só interesse pendente pode ser recusado")
                if motivo_limpo is None:
                    raise InteresseError(400, "Recusa exige motivo")
                alvo = "recusado"
            elif acao in {"desistir", "liberar"}:
                if acao == "desistir" and atual not in {"pendente", "selecionado"}:
                    raise InteresseError(400, "Interesse não pode ser cancelado agora")
                if acao == "liberar" and atual != "selecionado":
                    raise InteresseError(400, "Só reserva ativa pode ser liberada")
                if acao == "liberar" and motivo_limpo is None:
                    raise InteresseError(400, "Liberação exige motivo")
                if atual == "selecionado":
                    self._liberar_item(session, doc, item, interesse_oid, actor_oid, instante)
                alvo = "cancelado"
            elif acao == "retomar":
                if atual != "cancelado":
                    raise InteresseError(400, "Só interesse cancelado pode ser retomado")
                self._exigir_item_disponivel(item)
                alvo = "pendente"
            elif acao == "reabrir":
                if atual != "recusado":
                    raise InteresseError(400, "Só interesse recusado pode ser reaberto")
                self._exigir_item_disponivel(item)
                alvo = "pendente"

            campos: dict[str, Any] = {
                "status": alvo,
                "data_modificacao": instante,
                "motivo": motivo_limpo if alvo in {"recusado", "cancelado"} else None,
            }
            if alvo == "pendente" and atual in {"cancelado", "recusado"}:
                campos["tentativa"] = int(doc.get("tentativa") or 1) + 1
                campos["preco_selecionado"] = None
            if alvo == "selecionado" and item.get("destino") == "revenda":
                campos["preco_selecionado"] = item.get("valor")
            evento = {
                "status": alvo,
                "data_evento": instante,
                "ator_id": actor_oid,
                "motivo": campos["motivo"],
            }
            changed = self._colecao.update_one(
                {"_id": interesse_oid, "status": atual},
                {"$set": campos, "$push": {"historico": evento}},
                session=session,
            )
            if changed.matched_count != 1:
                raise InteresseError(409, "Interesse alterado por outra operação")

            if notificacao is not None and self._colecao_notificacoes is not None:
                self._registrar_aviso(session, doc, item, alvo, instante, notificacao)
            doc.update(campos)
            doc["historico"] = list(doc.get("historico") or []) + [evento]
            return self._para_modelo(doc)

        return self._transacao(operacao)

    def decidir(
        self,
        interesse_id: str,
        status: str,
        usuario_id: str,
        instante: datetime,
        *,
        notificacao: EventoNotificacao | None = None,
    ) -> Interesse:
        """Alias do PATCH antigo: aceitar virou selecionar."""
        acao = {
            "aceito": "selecionar",
            "selecionado": "selecionar",
            "recusado": "recusar",
            "cancelado": "desistir",
        }.get(status)
        if acao is None:
            raise InteresseError(400, "Transição de interesse inválida")
        return self.executar(
            interesse_id,
            acao,
            usuario_id,
            instante,
            motivo="Recusado pelo proprietário" if acao == "recusar" else None,
            notificacao=notificacao,
        )

    def _reservar_item(self, session, doc, item, interesse_oid, actor_oid, instante) -> None:
        if item.get("status") != "disponivel" or item.get("interesse_aceito_id") is not None:
            raise InteresseError(409, "Item não está disponível")
        if item.get("destino") == "descarte":
            raise InteresseError(400, "Este item não aceita interesses")
        update = self._colecao_itens.update_one(
            {"_id": doc["item_id"], "status": "disponivel", "interesse_aceito_id": None},
            {
                "$set": {
                    "status": "reservado",
                    "interesse_aceito_id": interesse_oid,
                    "data_modificacao": instante,
                },
                "$push": {
                    "historico": {
                        "etapa": "reserva_interesse",
                        "status": "reservado",
                        "data_evento": instante,
                        "responsavel_id": actor_oid,
                        "observacao": "Interesse selecionado",
                    }
                },
            },
            session=session,
        )
        if update.matched_count != 1:
            raise InteresseError(409, "Item não está disponível")

    def _liberar_item(self, session, doc, item, interesse_oid, actor_oid, instante) -> None:
        if item.get("interesse_aceito_id") != interesse_oid or item.get("status") != "reservado":
            raise InteresseError(409, "O item avançou e a reserva não pode ser liberada")
        update = self._colecao_itens.update_one(
            {
                "_id": doc["item_id"],
                "status": "reservado",
                "interesse_aceito_id": interesse_oid,
            },
            {
                "$set": {"status": "disponivel", "data_modificacao": instante},
                "$unset": {"interesse_aceito_id": ""},
                "$push": {
                    "historico": {
                        "etapa": "liberacao_reserva",
                        "status": "disponivel",
                        "data_evento": instante,
                        "responsavel_id": actor_oid,
                        "observacao": "Reserva liberada",
                    }
                },
            },
            session=session,
        )
        if update.matched_count != 1:
            raise InteresseError(409, "A reserva do item foi alterada")

    @staticmethod
    def _exigir_item_disponivel(item) -> None:
        if item.get("status") != "disponivel" or item.get("interesse_aceito_id") is not None:
            raise InteresseError(409, "Item não está disponível para retomada")

    def buscar_aceito_por_item(self, item_id: str) -> str | None:
        """Interessado da seleção vigente, usado na conclusão da doação."""
        item_oid = self._id(item_id)
        if item_oid is None:
            return None
        documento = self._colecao.find_one(
            {"item_id": item_oid, "status": "selecionado"},
            sort=[("data_modificacao", -1)],
        )
        return str(documento["usuario_id"]) if documento else None

    def _registrar_aviso(self, session, doc, item, status: str, instante, notificacao) -> None:
        destinatario = doc["usuario_id"] if status != "cancelado" else item["proprietario_id"]
        registro = montar_documento(
            usuario_id=str(destinatario),
            item_id=str(doc["item_id"]),
            interesse_id=str(doc["_id"]),
            evento=notificacao,
            instante=instante,
        )
        registrar(self._colecao_notificacoes, registro, session=session)
        if status in {"selecionado", "cancelado"}:
            self._avisar_mudanca_do_item(
                session, doc, item, status, instante, excluir=destinatario
            )

    def _avisar_mudanca_do_item(
        self,
        session,
        doc: dict[str, Any],
        item: dict[str, Any],
        status: str,
        instante: datetime,
        *,
        excluir: ObjectId,
    ) -> None:
        """Aceite e cancelamento podem reservar ou liberar o item; avisa os demais."""
        if item.get("destino") not in {"doacao", "revenda"}:
            return
        if status == "selecionado":
            novo_status = "reservado"
        elif status == "cancelado":
            novo_status = "disponivel"
        else:
            return
        evento = evento_de_status_item(
            str(doc["item_id"]), item.get("titulo"), novo_status, instante
        )
        outros = self._colecao.find(
            {
                "item_id": doc["item_id"],
                "status": {"$in": ["pendente", "selecionado"]},
                "usuario_id": {"$ne": excluir},
            },
            {"usuario_id": 1},
            session=session,
        )
        for outro in outros:
            registro = montar_documento(
                usuario_id=str(outro["usuario_id"]),
                item_id=str(doc["item_id"]),
                interesse_id=str(outro["_id"]),
                evento=evento,
                instante=instante,
            )
            registrar(self._colecao_notificacoes, registro, session=session)

    def _transacao(self, operacao: Callable):
        try:
            with self._colecao.database.client.start_session() as session:
                return session.with_transaction(operacao)
        except InteresseError:
            raise
        except DuplicateKeyError:
            raise
        except (PyMongoError, ConfigurationError, InvalidOperation, NotImplementedError) as erro:
            raise InteresseError(503, "Operação temporariamente indisponível") from erro

    @staticmethod
    def _validar_criacao(item, usuario, usuario_id: str) -> None:
        if usuario is None:
            raise InteresseError(404, "Usuário não encontrado")
        if usuario.get("tipo") != "pessoa":
            raise InteresseError(403, "Este perfil não pode registrar interesses")
        if item is None:
            raise InteresseError(404, "Item não encontrado")
        if str(item.get("proprietario_id")) == usuario_id:
            raise InteresseError(400, "Não é permitido demonstrar interesse no próprio item")
        if item.get("destino") == "descarte":
            raise InteresseError(400, "Itens destinados a descarte não aceitam interesses")
        if item.get("status") != "disponivel":
            raise InteresseError(409, "Item não está disponível")
        if item.get("interesse_aceito_id") is not None:
            raise InteresseError(409, "O item já possui um interesse selecionado")

    @staticmethod
    def _para_modelo(doc: dict[str, Any]) -> Interesse:
        historico = [
            EventoInteresse(
                status=evento.get("status", "pendente"),
                data_evento=MongoInteresseRepository._data(evento["data_evento"]),
                ator_id=str(evento.get("ator_id") or doc["usuario_id"]),
                motivo=evento.get("motivo"),
            )
            for evento in doc.get("historico") or []
        ]
        return Interesse(
            id=str(doc["_id"]),
            item_id=str(doc["item_id"]),
            usuario_id=str(doc["usuario_id"]),
            status=doc["status"],
            tentativa=int(doc.get("tentativa") or 1),
            motivo=doc.get("motivo"),
            preco_selecionado=doc.get("preco_selecionado"),
            historico=historico,
            data_adicao=MongoInteresseRepository._data(doc["data_adicao"]),
            data_modificacao=MongoInteresseRepository._data(doc["data_modificacao"]),
        )

    @staticmethod
    def _id(valor: str) -> ObjectId | None:
        try:
            return ObjectId(valor)
        except (InvalidId, TypeError):
            return None

    @classmethod
    def _required_id(cls, valor: str, detail: str, status_code: int) -> ObjectId:
        oid = cls._id(valor)
        if oid is None:
            raise InteresseError(status_code, detail)
        return oid

    @staticmethod
    def _data(valor: datetime) -> datetime:
        utc = valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor.astimezone(UTC)
        return utc.replace(microsecond=utc.microsecond // 1000 * 1000)
