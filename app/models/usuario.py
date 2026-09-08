from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Usuario:
    """Representa um usuário persistido na coleção ``usuarios``."""

    nome: str
    email: str
    tipo: str
    cidade: str
    data_cadastro: datetime
    id: str | None = None
