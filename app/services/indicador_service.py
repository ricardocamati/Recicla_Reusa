from typing import Protocol

from app.schemas.indicador import IndicadorResponse


class RepositorioDeIndicadores(Protocol):
    def contar_por_modalidade_e_status(self) -> dict[str, int]: ...


class IndicadorService:
    def __init__(self, repositorio: RepositorioDeIndicadores) -> None:
        self._repositorio = repositorio

    def obter(self) -> IndicadorResponse:
        # Cada item conta uma única vez, e só depois da confirmação de recebimento.
        contagem = self._repositorio.contar_por_modalidade_e_status()
        doados = int(contagem.get("doacao:concluido", 0))
        vendidos = int(contagem.get("revenda:concluido", 0))
        coletados = int(contagem.get("descarte:recebido", 0))
        indicados = int(contagem.get("descarte:destinacao_informada", 0))
        situacoes = self._repositorio.contar_por_situacao()
        ofertas_ativas = int(situacoes.get("disponivel", 0))
        pendencias = sum(
            int(situacoes.get(situacao, 0))
            for situacao in (
                "reservado",
                "aguardando_confirmacao",
                "aguardando_ponto",
                "entrega_prevista",
            )
        )
        return IndicadorResponse(
            doados=doados,
            coletados=coletados,
            indicados=indicados,
            ofertas_ativas=ofertas_ativas,
            pendencias=pendencias,
            vendidos=vendidos,
            # Recebimento no ponto continua separado de destinação apenas informada.
            total=doados + coletados + vendidos,
        )
