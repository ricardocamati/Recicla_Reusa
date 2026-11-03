"""Documento e gravação idempotente de notificações dentro de uma transação."""
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.client_session import ClientSession

from app.models.notificacao import EventoNotificacao, link_do_tipo


def _object_id(valor: str) -> ObjectId:
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError) as erro:
        raise ValueError("Identificador de notificação inválido") from erro


def montar_documento(
    *,
    usuario_id: str,
    item_id: str,
    evento: EventoNotificacao,
    instante: datetime,
    interesse_id: str | None = None,
) -> dict[str, Any]:
    momento = instante.astimezone(UTC).replace(microsecond=instante.microsecond // 1000 * 1000)
    return {
        "usuario_id": _object_id(usuario_id),
        "item_id": _object_id(item_id),
        "interesse_id": _object_id(interesse_id) if interesse_id else None,
        "tipo": evento.tipo,
        "titulo": evento.titulo,
        "mensagem": evento.mensagem,
        "evento_id": evento.evento_id,
        "link": evento.link or link_do_tipo(evento.tipo),
        "lida": False,
        "data_leitura": None,
        "data_adicao": momento,
        "data_modificacao": momento,
    }


def registrar(
    colecao: Collection[dict[str, Any]],
    documento: dict[str, Any],
    *,
    session: ClientSession | None = None,
) -> None:
    """Insere uma vez por (evento, destinatário, item); repetir é inofensivo."""
    filtro = {
        "evento_id": documento["evento_id"],
        "usuario_id": documento["usuario_id"],
        "item_id": documento["item_id"],
    }
    # O upsert com igualdade no índice único é idempotente; uma corrida real
    # entre transações é resolvida pelo retry do with_transaction.
    colecao.update_one(
        filtro,
        {"$setOnInsert": documento},
        upsert=True,
        session=session,
    )
