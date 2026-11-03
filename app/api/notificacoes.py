from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from app.schemas.notificacao import NotificacaoResponse, NotificacaoUpdateRequest
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes, Sessao
from app.services.notificacao_service import NotificacaoService


def criar_router_notificacoes(
    servico: NotificacaoService,
    sessoes: ArmazenamentoDeSessoes,
) -> APIRouter:
    router = APIRouter(prefix="/api/notificacoes", tags=["notificacoes"])

    def sessao_obrigatoria(request: Request) -> Sessao:
        sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
        if sessao is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return sessao

    @router.get("", response_model=list[NotificacaoResponse])
    def listar(
        request: Request,
        lida: bool | None = Query(default=None),
        offset: int = Query(default=0, ge=0),
        limite: int = Query(default=20, ge=1, le=100),
    ) -> list[NotificacaoResponse]:
        sessao = sessao_obrigatoria(request)
        extras = set(request.query_params) - {"lida", "offset", "limite"}
        if extras:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": [
                        {
                            "loc": ["query", campo],
                            "msg": "Parâmetro desconhecido",
                            "type": "extra_forbidden",
                        }
                        for campo in sorted(extras)
                    ]
                },
            )
        return servico.listar(
            sessao.usuario_id, lida=lida, offset=offset, limite=limite
        )

    @router.patch("/{notificacao_id}", response_model=NotificacaoResponse)
    def marcar_lida(
        notificacao_id: str,
        request: NotificacaoUpdateRequest,
        contexto: Request,
    ) -> NotificacaoResponse:
        sessao = sessao_obrigatoria(contexto)
        return servico.marcar_lida(notificacao_id, sessao.usuario_id)

    return router
