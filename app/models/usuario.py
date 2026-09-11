from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Usuario:
    """Representa um usuário com campos de endereço no nível raiz."""

    nome: str
    email: str
    tipo: str
    logradouro: str
    numero: str
    cep: str
    cidade: str
    complemento: str | None
    senha_hash: str
    data_adicao: datetime
    data_modificacao: datetime
    id: str | None = None
