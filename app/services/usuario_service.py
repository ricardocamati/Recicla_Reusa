from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import EmailDuplicadoError, UsuarioNaoEncontradoError
from app.mappers.usuario_mapper import UsuarioMapper
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)
from app.security.passwords import verify_password


class RepositorioDeUsuarios(Protocol):
    def criar(self, usuario: Usuario) -> Usuario: ...
    def listar(self) -> list[Usuario]: ...
    def buscar_por_id(self, usuario_id: str) -> Usuario | None: ...
    def buscar_por_email(self, email: str) -> Usuario | None: ...
    def atualizar(self, usuario: Usuario) -> Usuario: ...
    def excluir(self, usuario_id: str) -> None: ...


class UsuarioService:
    def __init__(
        self,
        repositorio: RepositorioDeUsuarios,
        *,
        relogio: Callable[[], datetime] | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._relogio = relogio or (lambda: datetime.now(UTC))

    def criar(self, request: UsuarioCreateRequest) -> UsuarioResponse:
        if self._repositorio.buscar_por_email(request.email) is not None:
            raise EmailDuplicadoError(request.email)
        instante = self._relogio()
        usuario = UsuarioMapper.para_modelo(request, instante=instante)
        return UsuarioMapper.para_resposta(self._repositorio.criar(usuario))

    def listar(self) -> list[UsuarioSummaryResponse]:
        return [UsuarioMapper.para_resumo(usuario) for usuario in self._repositorio.listar()]

    def buscar_por_id(self, usuario_id: str) -> UsuarioResponse:
        return UsuarioMapper.para_resposta(self._buscar_modelo(usuario_id))

    def resumir_por_id(self, usuario_id: str) -> UsuarioSummaryResponse:
        return UsuarioMapper.para_resumo(self._buscar_modelo(usuario_id))

    def atualizar(self, usuario_id: str, request: UsuarioUpdateRequest) -> UsuarioResponse:
        usuario = self._buscar_modelo(usuario_id)
        outro = self._repositorio.buscar_por_email(request.email)
        if outro is not None and outro.id != usuario.id:
            raise EmailDuplicadoError(request.email)
        UsuarioMapper.atualizar_modelo(request, usuario, instante=self._relogio())
        return UsuarioMapper.para_resposta(self._repositorio.atualizar(usuario))

    def excluir(self, usuario_id: str) -> None:
        self._buscar_modelo(usuario_id)
        self._repositorio.excluir(usuario_id)

    def autenticar(self, email: str, senha: str) -> Usuario | None:
        usuario = self._repositorio.buscar_por_email(email.lower())
        if usuario is None or not verify_password(senha, usuario.senha_hash):
            return None
        return usuario

    def _buscar_modelo(self, usuario_id: str) -> Usuario:
        usuario = self._repositorio.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoError(usuario_id)
        return usuario
