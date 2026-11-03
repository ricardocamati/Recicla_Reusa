from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import (
    PontoIncompativelError,
    PontoNaoEncontradoError,
    UsuarioNaoEncontradoError,
)
from app.mappers.ponto_coleta_mapper import PontoColetaMapper
from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Usuario
from app.schemas.ponto_coleta import (
    PontoColetaCreateRequest,
    PontoColetaResponse,
    PontoColetaUpdateRequest,
)


class RepositorioDePontos(Protocol):
    def criar(self, ponto: PontoColeta) -> PontoColeta: ...
    def listar(self, **filtros) -> list[PontoColeta]: ...
    def buscar_por_id(self, ponto_id: str) -> PontoColeta | None: ...
    def definir_ativo(self, ponto_id: str, ativo: bool, *, responsavel_id: str) -> PontoColetaResponse:
        ponto = self._repositorio.buscar_por_id(ponto_id)
        if ponto is None:
            raise PontoNaoEncontradoError(ponto_id)
        if ponto.responsavel_id != responsavel_id:
            raise PontoNaoAutorizadoError()
        if not self._repositorio.definir_ativo(
            ponto_id, responsavel_id=responsavel_id, ativo=ativo, instante=self._relogio()
        ):
            raise PontoNaoEncontradoError(ponto_id)
        atualizado = self._repositorio.buscar_por_id(ponto_id)
        if atualizado is None:
            raise PontoNaoEncontradoError(ponto_id)
        return PontoColetaMapper.para_resposta(atualizado)

    def atualizar(self, ponto: PontoColeta, *, responsavel_id: str) -> bool: ...
    def excluir(self, ponto_id: str, *, responsavel_id: str) -> bool: ...
    def contar_por_responsavel(self, responsavel_id: str) -> int: ...


class RepositorioDeUsuariosParaPontos(Protocol):
    def buscar_por_id(self, usuario_id: str) -> Usuario | None: ...


class PontoColetaService:
    def __init__(
        self,
        repositorio: RepositorioDePontos,
        repositorio_usuarios: RepositorioDeUsuariosParaPontos,
        *,
        relogio: Callable[[], datetime] | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._repositorio_usuarios = repositorio_usuarios
        self._relogio = relogio or (lambda: datetime.now(UTC))

    def criar(
        self,
        request: PontoColetaCreateRequest,
        *,
        responsavel_id: str,
    ) -> PontoColetaResponse:
        self._obter_operador(responsavel_id)
        ponto = PontoColetaMapper.para_modelo(
            request,
            responsavel_id=responsavel_id,
            instante=self._relogio(),
        )
        return PontoColetaMapper.para_resposta(self._repositorio.criar(ponto))

    def listar(
        self,
        *,
        cidade: str | None = None,
        categoria: str | None = None,
        escopo: str | None = None,
        usuario_id: str,
        offset: int = 0,
        limite: int = 20,
    ) -> list[PontoColetaResponse]:
        responsavel_id = usuario_id if escopo == "meus" else None
        pontos = self._repositorio.listar(
            cidade=cidade,
            categoria=categoria,
            responsavel_id=responsavel_id,
            offset=offset,
            limite=limite,
        )
        return [PontoColetaMapper.para_resposta(ponto) for ponto in pontos]

    def buscar_por_id(self, ponto_id: str) -> PontoColetaResponse:
        return PontoColetaMapper.para_resposta(self._buscar(ponto_id))

    def definir_ativo(self, ponto_id: str, ativo: bool, *, responsavel_id: str) -> PontoColetaResponse:
        ponto = self._repositorio.buscar_por_id(ponto_id)
        if ponto is None:
            raise PontoNaoEncontradoError(ponto_id)
        if ponto.responsavel_id != responsavel_id:
            raise PontoNaoAutorizadoError()
        if not self._repositorio.definir_ativo(
            ponto_id, responsavel_id=responsavel_id, ativo=ativo, instante=self._relogio()
        ):
            raise PontoNaoEncontradoError(ponto_id)
        atualizado = self._repositorio.buscar_por_id(ponto_id)
        if atualizado is None:
            raise PontoNaoEncontradoError(ponto_id)
        return PontoColetaMapper.para_resposta(atualizado)

    def atualizar(
        self,
        ponto_id: str,
        request: PontoColetaUpdateRequest,
        *,
        responsavel_id: str,
    ) -> PontoColetaResponse:
        ponto = self._buscar(ponto_id)
        if ponto.responsavel_id != responsavel_id:
            raise PontoNaoEncontradoError(ponto_id)
        PontoColetaMapper.atualizar_modelo(request, ponto, instante=self._relogio())
        if not self._repositorio.atualizar(ponto, responsavel_id=responsavel_id):
            raise PontoNaoEncontradoError(ponto_id)
        return PontoColetaMapper.para_resposta(ponto)

    def excluir(self, ponto_id: str, *, responsavel_id: str) -> None:
        if not self._repositorio.excluir(ponto_id, responsavel_id=responsavel_id):
            raise PontoNaoEncontradoError(ponto_id)

    def garantir_compatibilidade(self, ponto_id: str, categoria: str) -> PontoColeta:
        ponto = self._buscar(ponto_id)
        if categoria not in ponto.categorias_aceitas:
            raise PontoIncompativelError(ponto_id, categoria)
        return ponto

    def _buscar(self, ponto_id: str) -> PontoColeta:
        ponto = self._repositorio.buscar_por_id(ponto_id)
        if ponto is None:
            raise PontoNaoEncontradoError(ponto_id)
        return ponto

    def _obter_operador(self, usuario_id: str) -> Usuario:
        usuario = self._repositorio_usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoError(usuario_id)
        if usuario.tipo != "ponto_coleta":
            raise PontoNaoEncontradoError(usuario_id)
        return usuario
