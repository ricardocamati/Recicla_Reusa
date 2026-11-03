from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class EventoEncaminhamento:
    """Evento da tentativa de encaminhamento ao ponto."""

    status: str
    data_evento: datetime
    ator_id: str
    motivo: str | None = None


@dataclass(slots=True)
class Encaminhamento:
    item_id: str
    autor_id: str
    ponto_id: str
    status: str
    data_adicao: datetime
    data_modificacao: datetime
    motivo: str | None = None
    historico: list[EventoEncaminhamento] = field(default_factory=list)
    id: str | None = None
