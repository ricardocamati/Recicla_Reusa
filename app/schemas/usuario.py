from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TipoUsuario = Literal["doador", "beneficiario", "ponto_coleta"]


class UsuarioBaseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    tipo: TipoUsuario
    cidade: str = Field(min_length=2, max_length=80)

    @field_validator("nome", "email", "cidade")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        if not valor:
            raise ValueError("campo obrigatório")
        return valor

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        if "@" not in valor or "." not in valor.rsplit("@", 1)[-1]:
            raise ValueError("email inválido")
        return valor


class UsuarioCreateRequest(UsuarioBaseRequest):
    pass


class UsuarioUpdateRequest(UsuarioBaseRequest):
    pass


class UsuarioResponse(UsuarioBaseRequest):
    id: str
    data_cadastro: datetime


class UsuarioSummaryResponse(BaseModel):
    id: str
    nome: str
    email: str
    tipo: TipoUsuario
