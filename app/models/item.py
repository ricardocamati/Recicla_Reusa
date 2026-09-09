from dataclasses import dataclass
from datetime import datetime


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
    data_adicao: datetime
    data_modificacao: datetime
    id: str | None = None
