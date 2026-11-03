from dataclasses import dataclass
from datetime import datetime

from app.models.usuario import Endereco


@dataclass(slots=True)
class PontoColeta:
    """Local físico de recebimento, associado a uma conta operacional."""

    nome: str
    endereco: Endereco
    categorias_aceitas: list[str]
    horario_atendimento: str
    responsavel_id: str
    data_adicao: datetime
    data_modificacao: datetime
    ativo: bool = True
    id: str | None = None
