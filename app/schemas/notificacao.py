from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TipoNotificacao = Literal[
    "interesse_aceito",
    "interesse_recusado",
    "interesse_cancelado",
    "status_item_alterado",
    "item_concluido",
    "entrega_declarada",
]


class NotificacaoUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lida: Literal[True]


class NotificacaoResponse(BaseModel):
    id: str
    usuario_id: str
    item_id: str
    interesse_id: str | None = None
    tipo: TipoNotificacao
    titulo: str
    mensagem: str
    evento_id: str
    link: str | None = None
    lida: bool
    data_leitura: datetime | None = None
    data_adicao: datetime
    data_modificacao: datetime
