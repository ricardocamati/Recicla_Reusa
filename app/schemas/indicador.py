from pydantic import BaseModel


class IndicadorResponse(BaseModel):
    doados: int
    coletados: int
    indicados: int = 0
    vendidos: int
    total: int
