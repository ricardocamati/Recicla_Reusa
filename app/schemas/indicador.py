from pydantic import BaseModel


class IndicadorResponse(BaseModel):
    doados: int
    ofertas_ativas: int = 0
    pendencias: int = 0
    vendidos: int
    total: int
    locais_ativos: int = 0
