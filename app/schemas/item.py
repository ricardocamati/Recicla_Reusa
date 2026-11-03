from datetime import datetime
from typing import Annotated, Literal
import unicodedata

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _normalizar_enum(valor: object) -> object:
    if not isinstance(valor, str):
        return valor
    sem_acentos = unicodedata.normalize("NFKD", valor)
    sem_acentos = "".join(
        caractere for caractere in sem_acentos if not unicodedata.combining(caractere)
    )
    return sem_acentos.strip().lower().replace(" ", "_").replace("-", "_")


CategoriaItem = Annotated[
    Literal[
        "informatica",
        "notebook",
        "desktop",
        "telefonia",
        "celular",
        "tablet",
        "televisao",
        "audio",
        "eletrodomestico",
        "perifericos",
        "monitor",
        "impressora",
        "outro",
    ],
    BeforeValidator(_normalizar_enum),
]
CondicaoItem = Annotated[
    Literal[
        "funcional",
        "funcional_com_defeito",
        "reparavel",
        "sem_conserto",
        "recondicionado",
    ],
    BeforeValidator(_normalizar_enum),
]
DestinoItem = Annotated[
    Literal["doacao", "descarte", "revenda"],
    BeforeValidator(_normalizar_enum),
]
StatusItem = Annotated[
    Literal[
        "disponivel",
        "reservado",
        "doado",
        "encaminhado",
        "coletado",
        "em_avaliacao",
        "recondicionado",
        "vendido",
    ],
    BeforeValidator(_normalizar_enum),
]


class ItemCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    especificacoes: dict[str, str] = Field(default_factory=dict)

    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=1, max_length=2000)
    categoria: CategoriaItem
    marca: str = Field(min_length=1, max_length=80)
    modelo: str = Field(min_length=1, max_length=120)
    condicao: CondicaoItem
    destino: DestinoItem
    valor: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_valor_por_destino(self):
        if self.destino == "revenda" and self.valor is None:
            raise ValueError("item de revenda exige valor")
        if self.destino != "revenda" and self.valor is not None:
            raise ValueError("valor só pode ser informado para revenda")
        return self


class ItemUpdateRequest(ItemCreateRequest):
    status: StatusItem | None = None
    ponto_coleta_id: str | None = None
    comprador_id: str | None = None
    observacao: str | None = Field(default=None, max_length=300)


class FiltrosItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categoria: CategoriaItem | None = None
    condicao: CondicaoItem | None = None
    destino: DestinoItem | None = None
    status: StatusItem | None = None
    cidade: str | None = Field(default=None, min_length=1, max_length=160)


class EventoHistoricoResponse(BaseModel):
    etapa: str
    status: str
    data_evento: datetime
    responsavel_id: str
    observacao: str | None = None


class ItemResponse(BaseModel):
    id: str
    titulo: str
    descricao: str
    categoria: CategoriaItem
    marca: str
    modelo: str
    condicao: CondicaoItem
    destino: DestinoItem
    valor: float | None
    status: StatusItem
    proprietario_id: str
    cidade_proprietario: str
    ponto_coleta_id: str | None = None
    beneficiario_id: str | None = None
    comprador_id: str | None = None
    especificacoes: dict[str, str]
    historico: list[EventoHistoricoResponse]
    data_adicao: datetime
    data_modificacao: datetime
