from pydantic import BaseModel


class IndicadorResponse(BaseModel):
    doados: int
    coletados: int
    vendidos: int
    total: int
