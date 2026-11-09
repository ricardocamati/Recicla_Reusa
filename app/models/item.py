from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class EventoHistorico:
    """Evento do ciclo de vida do item, guardado em lista de subdocumentos."""

    etapa: str
    status: str
    data_evento: datetime
    responsavel_id: str
    observacao: str | None = None


@dataclass(slots=True)
class Item:
    titulo: str
    descricao: str
    categoria: str
    marca: str
    modelo: str
    condicao: str
    destino: str
    valor: float | None
    status: str
    proprietario_id: str
    especificacoes: dict[str, str]
    historico: list[EventoHistorico]
    data_adicao: datetime
    data_modificacao: datetime
    beneficiario_id: str | None = None
    comprador_id: str | None = None
    id: str | None = None
