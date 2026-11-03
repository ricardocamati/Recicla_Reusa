from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatusInteresse = Literal["pendente", "aceito", "recusado", "cancelado"]


class InteresseCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_id: str = Field(min_length=1, max_length=64)


class InteresseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["aceito", "recusado", "cancelado"]


class InteresseResponse(BaseModel):
    id: str
    item_id: str
    usuario_id: str
    status: StatusInteresse
    data_adicao: datetime
    data_modificacao: datetime
