from collections.abc import Callable
from datetime import UTC, datetime

from app.exceptions import EncaminhamentoError
from app.mappers.encaminhamento_mapper import EncaminhamentoMapper
from app.models.encaminhamento import Encaminhamento
from app.schemas.encaminhamento import (
    EncaminhamentoAcaoRequest,
    EncaminhamentoCreateRequest,
    EncaminhamentoResponse,
)


class EncaminhamentoService:
    """Regras de encaminhamento de descarte ao ponto de coleta."""

    def __init__(self, repositorio, *, repositorio_pontos=None, relogio: Callable[[], datetime] | None = None) -> None:
        self._repositorio = repositorio
        self._pontos = repositorio_pontos
        self._relogio = relogio or (lambda: datetime.now(UTC))

    def criar(self, dados: EncaminhamentoCreateRequest, usuario_id: str) -> EncaminhamentoResponse:
        encaminhamento = self._repositorio.criar(
            dados.item_id, usuario_id, dados.ponto_id, self._relogio()
        )
        return EncaminhamentoMapper.para_resposta(encaminhamento)

    def listar(
        self,
        usuario_id: str,
        *,
        escopo: str = "autor",
        ponto_id: str | None = None,
        item_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[EncaminhamentoResponse]:
        return [
            EncaminhamentoMapper.para_resposta(item)
            for item in self._repositorio.listar(
                usuario_id,
                escopo=escopo,
                ponto_id=ponto_id,
                item_id=item_id,
                status=status,
                offset=offset,
                limite=limite,
            )
        ]

    def buscar_por_id(self, encaminhamento_id: str, usuario_id: str) -> EncaminhamentoResponse:
        encaminhamento = self._repositorio.buscar_por_id(encaminhamento_id)
        if encaminhamento is None:
            raise EncaminhamentoError(404, "Encaminhamento não encontrado")
        self._garantir_participante(encaminhamento, usuario_id)
        return EncaminhamentoMapper.para_resposta(encaminhamento)

    def executar(
        self, encaminhamento_id: str, dados: EncaminhamentoAcaoRequest, usuario_id: str
    ) -> EncaminhamentoResponse:
        encaminhamento = self._repositorio.executar(
            encaminhamento_id,
            dados.acao,
            usuario_id,
            self._relogio(),
            motivo=dados.motivo,
            novo_ponto_id=dados.novo_ponto_id,
        )
        return EncaminhamentoMapper.para_resposta(encaminhamento)

    def avisar_ponto_inativado(self, ponto_id: str) -> int:
        return self._repositorio.avisar_ponto_inativado(ponto_id, self._relogio())

    def _garantir_participante(self, encaminhamento: Encaminhamento, usuario_id: str) -> None:
        if encaminhamento.autor_id == usuario_id:
            return
        if self._pontos is not None:
            ponto = self._pontos.buscar_por_id(encaminhamento.ponto_id)
            if ponto is not None and ponto.responsavel_id == usuario_id:
                return
        raise EncaminhamentoError(404, "Encaminhamento não encontrado")
