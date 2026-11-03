from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class EventoInteresse:
    """Evento do ciclo do interesse, sempre acrescentado."""

    status: str
    data_evento: datetime
    ator_id: str
    motivo: str | None = None


@dataclass(slots=True)
class Combinacao:
    """Combinação de entrega proposta por um dos participantes selecionados."""

    local_texto: str
    revisao: int
    proposto_por: str
    proposto_em: datetime
    previsao: datetime | None = None
    observacao: str | None = None
    aceito_por: str | None = None
    aceito_em: datetime | None = None


@dataclass(slots=True)
class Interesse:
    item_id: str
    usuario_id: str
    status: str
    data_adicao: datetime
    data_modificacao: datetime
    tentativa: int = 1
    motivo: str | None = None
    preco_selecionado: float | None = None
    resultado: str | None = None
    combinacao: Combinacao | None = None
    historico: list[EventoInteresse] = field(default_factory=list)
    id: str | None = None
