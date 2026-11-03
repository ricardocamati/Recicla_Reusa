from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Endereco:
    """Endereço do usuário, persistido como subdocumento."""

    logradouro: str
    numero: str
    cep: str
    cidade: str
    complemento: str | None = None


@dataclass(slots=True)
class Usuario:
    """Representa um usuário com endereço aninhado."""

    nome: str
    email: str
    tipo: str
    endereco: Endereco
    senha_hash: str
    data_adicao: datetime
    data_modificacao: datetime
    id: str | None = None
