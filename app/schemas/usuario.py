from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TipoUsuario = Literal["doador", "beneficiario", "ponto_coleta"]
TipoCadastro = Literal["doador", "beneficiario"]


class EnderecoSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    logradouro: str = Field(min_length=1, max_length=160)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=160)
    cep: str = Field(min_length=8, max_length=8)
    cidade: str = Field(min_length=1, max_length=160)

    @field_validator("cep", mode="before")
    @classmethod
    def normalizar_cep(cls, valor: str) -> str:
        if not isinstance(valor, str):
            raise ValueError("CEP inválido")
        valor = valor.strip().replace("-", "")
        if len(valor) != 8 or not valor.isdigit():
            raise ValueError("CEP deve possuir oito dígitos")
        return valor

    @field_validator("complemento")
    @classmethod
    def normalizar_complemento(cls, valor: str | None) -> str | None:
        return valor or None


class UsuarioCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    senha: str = Field(min_length=8, max_length=128)
    tipo: TipoCadastro
    endereco: EnderecoSchema

    @field_validator("nome", "email")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        if not valor:
            raise ValueError("campo obrigatório")
        return valor

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        if not isinstance(valor, str):
            raise ValueError("email inválido")
        valor = valor.strip().lower()
        if "@" not in valor or "." not in valor.rsplit("@", 1)[-1]:
            raise ValueError("email inválido")
        return valor

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor: str) -> str:
        if not any(caractere.isalpha() for caractere in valor) or not any(
            caractere.isdigit() for caractere in valor
        ):
            raise ValueError("senha deve conter letra e número")
        return valor


class UsuarioUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nome: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    endereco: EnderecoSchema

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        if not valor:
            raise ValueError("campo obrigatório")
        return valor

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        if not isinstance(valor, str):
            raise ValueError("email inválido")
        valor = valor.strip().lower()
        if "@" not in valor or "." not in valor.rsplit("@", 1)[-1]:
            raise ValueError("email inválido")
        return valor


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str = Field(min_length=5, max_length=160)
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        if not isinstance(valor, str):
            raise ValueError("email inválido")
        return valor.strip().lower()


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    tipo: TipoUsuario
    endereco: EnderecoSchema
    data_adicao: datetime
    data_modificacao: datetime


class UsuarioSummaryResponse(BaseModel):
    id: str
    nome: str
    tipo: TipoUsuario
    cidade: str
