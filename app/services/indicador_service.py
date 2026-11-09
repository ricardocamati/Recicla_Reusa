from typing import Protocol

from app.schemas.indicador import IndicadorResponse


class RepositorioDeIndicadores(Protocol):
    def contar_por_modalidade_e_status(self) -> dict[str, int]: ...
    def contar_locais_ativos(self) -> int: ...


class IndicadorService:
    def __init__(self, repositorio: RepositorioDeIndicadores) -> None:
        self._repositorio = repositorio

    def obter(self) -> IndicadorResponse:
        # Cada item conta uma única vez, e só depois da confirmação de recebimento.
        contagem = self._repositorio.contar_por_modalidade_e_status()
        doados = int(contagem.get("doacao:concluido", 0))
        vendidos = int(contagem.get("revenda:concluido", 0))
        situacoes = self._repositorio.contar_por_situacao()
        ofertas_ativas = int(situacoes.get("disponivel", 0))
        pendencias = sum(
            int(situacoes.get(situacao, 0))
            for situacao in (
                "reservado",
                "aguardando_confirmacao",
            )
        )
        return IndicadorResponse(
            doados=doados,
            ofertas_ativas=ofertas_ativas,
            pendencias=pendencias,
            vendidos=vendidos,
            total=doados + vendidos,
            locais_ativos=self._repositorio.contar_locais_ativos(),
        )
