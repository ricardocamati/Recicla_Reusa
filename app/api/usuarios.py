from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status

from app.schemas.usuario import (
    LoginRequest,
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)
from app.security.sessions import (
    SESSION_COOKIE_NAME,
    ArmazenamentoDeSessoes,
    Sessao,
)
from app.services.usuario_service import UsuarioService


def criar_routers(
    servico: UsuarioService,
    sessoes: ArmazenamentoDeSessoes,
    *,
    cookies_seguros: bool = False,
) -> APIRouter:
    router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])
    auth_router = APIRouter(prefix="/api/auth", tags=["autenticacao"])

    def sessao_opcional(request: Request) -> Sessao | None:
        return sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))

    def sessao_obrigatoria(request: Request) -> Sessao:
        sessao = sessao_opcional(request)
        if sessao is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return sessao

    @router.get("", response_model=list[UsuarioSummaryResponse])
    def listar() -> list[UsuarioSummaryResponse]:
        return servico.listar()

    @router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
    def criar(request: UsuarioCreateRequest, response: Response) -> UsuarioResponse:
        usuario = servico.criar(request)
        response.headers["Location"] = f"/api/usuarios/{usuario.id}"
        return usuario

    @router.get(
        "/me",
        response_model=UsuarioResponse,
    )
    def meu_perfil(request: Request) -> UsuarioResponse:
        sessao = sessao_obrigatoria(request)
        return servico.buscar_por_id(sessao.usuario_id)

    @router.get(
        "/{usuario_id}",
        response_model=UsuarioResponse | UsuarioSummaryResponse,
    )
    def buscar_por_id(usuario_id: str, request: Request) -> UsuarioResponse | UsuarioSummaryResponse:
        sessao = sessao_opcional(request)
        if sessao is not None and sessao.usuario_id == usuario_id:
            return servico.buscar_por_id(usuario_id)
        return servico.resumir_por_id(usuario_id)

    @router.put("/{usuario_id}", response_model=UsuarioResponse)
    def atualizar(
        usuario_id: str,
        request: UsuarioUpdateRequest,
        contexto: Request,
    ) -> UsuarioResponse:
        sessao = sessao_obrigatoria(contexto)
        if sessao.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ação não permitida")
        return servico.atualizar(usuario_id, request)

    @router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
    def excluir(usuario_id: str, request: Request) -> Response:
        sessao = sessao_obrigatoria(request)
        if sessao.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ação não permitida")
        servico.excluir(usuario_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @auth_router.post("/login", response_model=UsuarioResponse)
    def login(request: LoginRequest, response: Response) -> UsuarioResponse:
        usuario = servico.autenticar(request.email, request.senha)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Cookie"},
            )
        identificador = sessoes.criar(usuario.id or "", usuario.tipo)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=identificador,
            max_age=1800,
            httponly=True,
            samesite="lax",
            secure=cookies_seguros,
            path="/",
        )
        return servico.buscar_por_id(usuario.id or "")

    @auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(
        response: Response,
        identificador: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    ) -> Response:
        sessoes.remover(identificador)
        response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    return router, auth_router


def criar_router(
    servico: UsuarioService,
    sessoes: ArmazenamentoDeSessoes,
    *,
    cookies_seguros: bool = False,
) -> APIRouter:
    """Mantém compatibilidade para consumidores que registram só usuários."""
    return criar_routers(
        servico,
        sessoes,
        cookies_seguros=cookies_seguros,
    )[0]
