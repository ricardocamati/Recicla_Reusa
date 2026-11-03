from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StatusEncaminhamento = Literal["entrega_prevista", "cancelado", "nao_recebido", "recebido"]
AcaoEncaminhamento = Literal["cancelar", "trocar", "nao_recebido", "receber"]


class EncaminhamentoCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1, max_length=64)
    ponto_id: str = Field(min_length=1, max_length=64)


class EncaminhamentoAcaoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acao: AcaoEncaminhamento
    motivo: str | None = Field(default=None, max_length=300)
    novo_ponto_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def validar_campos(self):
        if self.acao == "trocar" and not self.novo_ponto_id:
            raise ValueError("trocar exige novo_ponto_id")
        if self.acao == "nao_recebido" and not (self.motivo or "").strip():
            raise ValueError("não recebido exige motivo")
        return self


class EventoEncaminhamentoResponse(BaseModel):
    status: StatusEncaminhamento
    data_evento: datetime
    ator_id: str
    motivo: str | None = None


class EncaminhamentoResponse(BaseModel):
    id: str
    item_id: str
    autor_id: str
    ponto_id: str
    status: StatusEncaminhamento
    motivo: str | None = None
    historico: list[EventoEncaminhamentoResponse] = Field(default_factory=list)
    data_adicao: datetime
    data_modificacao: datetime
