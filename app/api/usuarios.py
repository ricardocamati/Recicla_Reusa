from fastapi import APIRouter, Response, status

from app.schemas.usuario import (
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)
from app.services.usuario_service import UsuarioService


def criar_router(servico: UsuarioService) -> APIRouter:
    router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

    @router.get("", response_model=list[UsuarioSummaryResponse])
    def listar() -> list[UsuarioSummaryResponse]:
        return servico.listar()

    @router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
    def criar(request: UsuarioCreateRequest, response: Response) -> UsuarioResponse:
        usuario = servico.criar(request)
        response.headers["Location"] = f"/api/usuarios/{usuario.id}"
        return usuario

    @router.get("/{usuario_id}", response_model=UsuarioResponse)
    def buscar_por_id(usuario_id: str) -> UsuarioResponse:
        return servico.buscar_por_id(usuario_id)

    @router.put("/{usuario_id}", response_model=UsuarioResponse)
    def atualizar(usuario_id: str, request: UsuarioUpdateRequest) -> UsuarioResponse:
        return servico.atualizar(usuario_id, request)

    @router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
    def excluir(usuario_id: str) -> Response:
        servico.excluir(usuario_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
