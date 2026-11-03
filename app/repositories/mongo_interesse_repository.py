from datetime import UTC, datetime
from typing import Any, Callable

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError, DuplicateKeyError, InvalidOperation, PyMongoError

from app.exceptions import InteresseError
from app.models.interesse import Interesse


class MongoInteresseRepository:
    def __init__(self, colecao: Collection[dict[str, Any]], colecao_itens: Collection[dict[str, Any]], colecao_usuarios: Collection[dict[str, Any]], *, criar_indices: bool = True) -> None:
        self._colecao = colecao
        self._colecao_itens = colecao_itens
        self._colecao_usuarios = colecao_usuarios
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
        doc = {"item_id": item_oid, "usuario_id": usuario_oid, "status": "pendente", "data_adicao": self._data(interesse.data_adicao), "data_modificacao": self._data(interesse.data_modificacao)}

        def operacao(session):
            usuario = self._colecao_usuarios.find_one({"_id": usuario_oid}, session=session)
            item = self._colecao_itens.find_one({"_id": item_oid}, session=session)
            self._validar_criacao(item, usuario, interesse.usuario_id)
            resultado = self._colecao.insert_one(doc, session=session)
            interesse.id = str(resultado.inserted_id)
            interesse.data_adicao = doc["data_adicao"]
            interesse.data_modificacao = doc["data_modificacao"]
            return interesse

        try:
            return self._transacao(operacao)
        except DuplicateKeyError as erro:
            raise InteresseError(409, "Já existe interesse deste usuário para o item") from erro

    def decidir(self, interesse_id: str, status: str, usuario_id: str, instante: datetime) -> Interesse:
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
            if status == "cancelado":
                if not interessado:
                    raise InteresseError(403, "Somente o interessado pode cancelar")
                if doc["status"] not in {"pendente", "aceito"}:
                    raise InteresseError(400, "Transição de interesse inválida")
            else:
                if not dono:
                    raise InteresseError(403, "Somente o proprietário pode decidir")
                if doc["status"] != "pendente" or status not in {"aceito", "recusado"}:
                    raise InteresseError(400, "Transição de interesse inválida")

            if status == "aceito":
                if item.get("status") != "disponivel" or item.get("interesse_aceito_id") is not None:
                    raise InteresseError(409, "Item não está disponível")
                if item.get("destino") == "doacao":
                    update = self._colecao_itens.update_one(
                        {"_id": doc["item_id"], "status": "disponivel", "interesse_aceito_id": None},
                        {"$set": {"status": "reservado", "interesse_aceito_id": interesse_oid, "data_modificacao": instante}, "$push": {"historico": {"etapa": "reserva_interesse", "status": "reservado", "data_evento": instante, "responsavel_id": actor_oid, "observacao": "Interesse aceito"}}}, session=session)
                elif item.get("destino") == "revenda":
                    update = self._colecao_itens.update_one(
                        {"_id": doc["item_id"], "status": "disponivel", "interesse_aceito_id": None},
                        {"$set": {"interesse_aceito_id": interesse_oid, "data_modificacao": instante}}, session=session)
                else:
                    raise InteresseError(400, "Este item não aceita interesses")
                if update.matched_count != 1:
                    raise InteresseError(409, "Item não está disponível")

            if status == "cancelado" and doc["status"] == "aceito":
                esperado = "reservado" if item.get("destino") == "doacao" else "disponivel"
                if item.get("interesse_aceito_id") != interesse_oid or item.get("status") != esperado:
                    raise InteresseError(409, "O item avançou e a seleção não pode ser liberada")
                if item.get("destino") == "doacao" and item.get("status") == "reservado":
                    update = self._colecao_itens.update_one(
                        {"_id": doc["item_id"], "status": "reservado", "interesse_aceito_id": interesse_oid},
                        {"$set": {"status": "disponivel", "data_modificacao": instante}, "$unset": {"interesse_aceito_id": ""}, "$push": {"historico": {"etapa": "cancelamento_interesse", "status": "disponivel", "data_evento": instante, "responsavel_id": actor_oid, "observacao": "Interesse aceito cancelado"}}}, session=session)
                    if update.matched_count != 1:
                        raise InteresseError(409, "A reserva do item foi alterada")
                elif item.get("destino") == "revenda" and item.get("status") == "disponivel":
                    update = self._colecao_itens.update_one(
                        {"_id": doc["item_id"], "status": "disponivel", "interesse_aceito_id": interesse_oid},
                        {"$unset": {"interesse_aceito_id": ""}, "$set": {"data_modificacao": instante}}, session=session)
                    if update.matched_count != 1:
                        raise InteresseError(409, "A seleção do item foi alterada")

            changed = self._colecao.update_one({"_id": interesse_oid, "status": doc["status"]}, {"$set": {"status": status, "data_modificacao": instante}}, session=session)
            if changed.matched_count != 1:
                raise InteresseError(409, "Interesse alterado por outra operação")
            doc.update(status=status, data_modificacao=instante)
            return self._para_modelo(doc)

        return self._transacao(operacao)

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
        if usuario.get("tipo") not in {"doador", "beneficiario"}:
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
            raise InteresseError(409, "O item já possui um interesse aceito")

    @staticmethod
    def _para_modelo(doc: dict[str, Any]) -> Interesse:
        return Interesse(id=str(doc["_id"]), item_id=str(doc["item_id"]), usuario_id=str(doc["usuario_id"]), status=doc["status"], data_adicao=MongoInteresseRepository._data(doc["data_adicao"]), data_modificacao=MongoInteresseRepository._data(doc["data_modificacao"]))

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
