from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Interesse:
    item_id: str
    usuario_id: str
    status: str
    data_adicao: datetime
    data_modificacao: datetime
    id: str | None = None
