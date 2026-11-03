from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StatusInteresse = Literal[
    "pendente", "selecionado", "recusado", "cancelado", "encerrado"
]
AcaoInteresse = Literal[
    "selecionar", "recusar", "desistir", "liberar", "retomar", "reabrir"
]


class InteresseCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_id: str = Field(min_length=1, max_length=64)


class InteresseUpdateRequest(BaseModel):
    """Alias legado do PATCH: aceitar virou selecionar."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["selecionado", "recusado", "cancelado"]


class InteresseAcaoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acao: AcaoInteresse
    motivo: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def exigir_motivo_quando_necessario(self):
        if self.acao in {"recusar", "liberar"} and not (self.motivo or "").strip():
            raise ValueError("motivo é obrigatório para recusar ou liberar")
        return self


class EventoInteresseResponse(BaseModel):
    status: StatusInteresse
    data_evento: datetime
    ator_id: str
    motivo: str | None = None


class InteresseResponse(BaseModel):
    id: str
    item_id: str
    usuario_id: str
    status: StatusInteresse
    tentativa: int = 1
    motivo: str | None = None
    preco_selecionado: float | None = None
    historico: list[EventoInteresseResponse] = Field(default_factory=list)
    data_adicao: datetime
    data_modificacao: datetime
