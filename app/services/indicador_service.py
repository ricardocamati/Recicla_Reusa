from typing import Protocol

from app.schemas.indicador import IndicadorResponse


class RepositorioDeIndicadores(Protocol):
    def contar_por_status(self) -> dict[str, int]: ...


class IndicadorService:
    def __init__(self, repositorio: RepositorioDeIndicadores) -> None:
        self._repositorio = repositorio

    def obter(self) -> IndicadorResponse:
        contagem = self._repositorio.contar_por_status()
        doados = int(contagem.get("doado", 0))
        coletados = int(contagem.get("coletado", 0))
        vendidos = int(contagem.get("vendido", 0))
        return IndicadorResponse(
            doados=doados,
            coletados=coletados,
            vendidos=vendidos,
            total=doados + coletados + vendidos,
        )
