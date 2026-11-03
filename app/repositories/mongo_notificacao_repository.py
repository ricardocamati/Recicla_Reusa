from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.client_session import ClientSession

from app.models.notificacao import Notificacao


class MongoNotificacaoRepository:
    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        *,
        criar_indices: bool = True,
    ) -> None:
        self._colecao = colecao
        if criar_indices:
            self.criar_indices()

    def criar_indices(self) -> None:
        self._colecao.create_index(
            [("evento_id", 1), ("usuario_id", 1), ("item_id", 1)],
            unique=True,
            name="notificacao_evento_destinatario",
        )
        self._colecao.create_index(
            [("usuario_id", 1), ("data_adicao", -1)],
            name="notificacao_usuario_data",
        )

    def listar(
        self,
        usuario_id: str,
        *,
        lida: bool | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[Notificacao]:
        usuario_oid = self._id(usuario_id)
        if usuario_oid is None:
            return []
        consulta: dict[str, Any] = {"usuario_id": usuario_oid}
        if lida is not None:
            consulta["lida"] = lida
        documentos = (
            self._colecao.find(consulta)
            .sort([("data_adicao", -1), ("_id", -1)])
            .skip(offset)
            .limit(limite)
        )
        return [self._para_modelo(documento) for documento in documentos]

    def buscar_por_id(self, notificacao_id: str, usuario_id: str) -> Notificacao | None:
        notificacao_oid = self._id(notificacao_id)
        usuario_oid = self._id(usuario_id)
        if notificacao_oid is None or usuario_oid is None:
            return None
        documento = self._colecao.find_one(
            {"_id": notificacao_oid, "usuario_id": usuario_oid}
        )
        return self._para_modelo(documento) if documento else None

    def marcar_lida(
        self,
        notificacao_id: str,
        usuario_id: str,
        instante: datetime,
    ) -> Notificacao | None:
        from pymongo import ReturnDocument

        notificacao_oid = self._id(notificacao_id)
        usuario_oid = self._id(usuario_id)
        if notificacao_oid is None or usuario_oid is None:
            return None
        momento = self._data(instante)
        documento = self._colecao.find_one_and_update(
            {"_id": notificacao_oid, "usuario_id": usuario_oid},
            {"$set": {"lida": True, "data_leitura": momento, "data_modificacao": momento}},
            return_document=ReturnDocument.AFTER,
        )
        return self._para_modelo(documento) if documento else None

    @staticmethod
    def _id(valor: str) -> ObjectId | None:
        try:
            return ObjectId(valor)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    def _data(instante: datetime) -> datetime:
        utc = instante.replace(tzinfo=UTC) if instante.tzinfo is None else instante.astimezone(UTC)
        return utc.replace(microsecond=utc.microsecond // 1000 * 1000)

    @classmethod
    def _para_modelo(cls, documento: dict[str, Any]) -> Notificacao:
        return Notificacao(
            id=str(documento["_id"]),
            usuario_id=str(documento["usuario_id"]),
            item_id=str(documento["item_id"]),
            interesse_id=(
                str(documento["interesse_id"])
                if documento.get("interesse_id") is not None
                else None
            ),
            tipo=documento["tipo"],
            titulo=documento["titulo"],
            mensagem=documento["mensagem"],
            evento_id=documento["evento_id"],
            lida=bool(documento.get("lida", False)),
            data_leitura=(
                cls._data(documento["data_leitura"])
                if documento.get("data_leitura") is not None
                else None
            ),
            data_adicao=cls._data(documento["data_adicao"]),
            data_modificacao=cls._data(documento["data_modificacao"]),
        )
