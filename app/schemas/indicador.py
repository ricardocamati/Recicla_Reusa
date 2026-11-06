from pydantic import BaseModel


class IndicadorResponse(BaseModel):
    doados: int
    coletados: int
    indicados: int = 0
    ofertas_ativas: int = 0
    pendencias: int = 0
    vendidos: int
    total: int
