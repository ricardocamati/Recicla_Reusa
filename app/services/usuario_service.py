from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import UsuarioNaoEncontradoError
from app.mappers.usuario_mapper import UsuarioMapper
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)


class RepositorioDeUsuarios(Protocol):
    def criar(self, usuario: Usuario) -> Usuario: ...
    def listar(self) -> list[Usuario]: ...
    def buscar_por_id(self, usuario_id: str) -> Usuario | None: ...
    def atualizar(self, usuario: Usuario) -> Usuario: ...
    def excluir(self, usuario_id: str) -> None: ...


class UsuarioService:
    def __init__(self, repositorio: RepositorioDeUsuarios, *, relogio: Callable[[], datetime] | None = None) -> None:
        self._repositorio = repositorio
        self._relogio = relogio or (lambda: datetime.now(UTC))
        self._mapper = UsuarioMapper()

    def criar(self, request: UsuarioCreateRequest) -> UsuarioResponse:
        usuario = self._mapper.para_modelo(request, data_cadastro=self._relogio())
        return self._mapper.para_resposta(self._repositorio.criar(usuario))

    def listar(self) -> list[UsuarioSummaryResponse]:
        return [self._mapper.para_resumo(usuario) for usuario in self._repositorio.listar()]

    def buscar_por_id(self, usuario_id: str) -> UsuarioResponse:
        return self._mapper.para_resposta(self._buscar_modelo(usuario_id))

    def atualizar(self, usuario_id: str, request: UsuarioUpdateRequest) -> UsuarioResponse:
        usuario = self._buscar_modelo(usuario_id)
        self._mapper.atualizar_modelo(request, usuario)
        return self._mapper.para_resposta(self._repositorio.atualizar(usuario))

    def excluir(self, usuario_id: str) -> None:
        self._buscar_modelo(usuario_id)
        self._repositorio.excluir(usuario_id)

    def _buscar_modelo(self, usuario_id: str) -> Usuario:
        usuario = self._repositorio.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoError(usuario_id)
        return usuario
