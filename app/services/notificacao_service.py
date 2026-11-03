from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import NotificacaoNaoEncontradaError
from app.mappers.notificacao_mapper import NotificacaoMapper
from app.models.notificacao import Notificacao
from app.schemas.notificacao import NotificacaoResponse


class RepositorioDeNotificacoes(Protocol):
    def listar(
        self,
        usuario_id: str,
        *,
        lida: bool | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[Notificacao]: ...
    def marcar_lida(
        self,
        notificacao_id: str,
        usuario_id: str,
        instante: datetime,
    ) -> Notificacao | None: ...


class NotificacaoService:
    def __init__(
        self,
        repositorio: RepositorioDeNotificacoes,
        *,
        relogio: Callable[[], datetime] | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._relogio = relogio or (lambda: datetime.now(UTC))

    def listar(
        self,
        usuario_id: str,
        *,
        lida: bool | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[NotificacaoResponse]:
        return [
            NotificacaoMapper.para_resposta(notificacao)
            for notificacao in self._repositorio.listar(
                usuario_id, lida=lida, offset=offset, limite=limite
            )
        ]

    def marcar_lida(
        self,
        notificacao_id: str,
        usuario_id: str,
    ) -> NotificacaoResponse:
        notificacao = self._repositorio.marcar_lida(
            notificacao_id, usuario_id, self._relogio()
        )
        if notificacao is None:
            raise NotificacaoNaoEncontradaError(notificacao_id)
        return NotificacaoMapper.para_resposta(notificacao)
