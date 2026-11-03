from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.item import CategoriaItem
from app.schemas.usuario import EnderecoRequest, EnderecoResponse


class PontoColetaCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nome: str = Field(min_length=3, max_length=120)
    endereco: EnderecoRequest
    categorias_aceitas: list[CategoriaItem] = Field(min_length=1, max_length=13)
    horario_atendimento: str = Field(min_length=3, max_length=160)

    @field_validator("categorias_aceitas")
    @classmethod
    def sem_duplicatas(cls, valores: list[str]) -> list[str]:
        if len(set(valores)) != len(valores):
            raise ValueError("categorias aceitas não podem se repetir")
        return valores


class PontoColetaUpdateRequest(PontoColetaCreateRequest):
    pass


class PontoColetaResponse(BaseModel):
    id: str
    nome: str
    endereco: EnderecoResponse
    categorias_aceitas: list[str]
    horario_atendimento: str
    responsavel_id: str
    data_adicao: datetime
    data_modificacao: datetime
