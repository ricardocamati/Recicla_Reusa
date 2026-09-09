from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import secrets

SESSION_COOKIE_NAME = "recicla_sessao"
SESSION_DURATION = timedelta(minutes=30)


@dataclass(frozen=True, slots=True)
class Sessao:
    usuario_id: str
    tipo: str
    expira_em: datetime


class ArmazenamentoDeSessoes:
    def __init__(self, *, relogio: Callable[[], datetime] | None = None) -> None:
        self._relogio = relogio or (lambda: datetime.now(UTC))
        self._sessoes: dict[str, Sessao] = {}

    def criar(self, usuario_id: str, tipo: str) -> str:
        identificador = secrets.token_urlsafe(32)
        self._sessoes[identificador] = Sessao(
            usuario_id=usuario_id,
            tipo=tipo,
            expira_em=self._relogio() + SESSION_DURATION,
        )
        return identificador

    def buscar(self, identificador: str | None) -> Sessao | None:
        if not identificador:
            return None
        sessao = self._sessoes.get(identificador)
        if sessao is None:
            return None
        if sessao.expira_em <= self._relogio():
            self._sessoes.pop(identificador, None)
            return None
        return sessao

    def remover(self, identificador: str | None) -> None:
        if identificador:
            self._sessoes.pop(identificador, None)
