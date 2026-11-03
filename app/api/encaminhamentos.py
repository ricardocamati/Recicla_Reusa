from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.exceptions import EncaminhamentoError
from app.schemas.encaminhamento import (
    EncaminhamentoAcaoRequest,
    EncaminhamentoCreateRequest,
    EncaminhamentoResponse,
)
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes
from app.services.encaminhamento_service import EncaminhamentoService


def criar_router_encaminhamentos(
    servico: EncaminhamentoService, sessoes: ArmazenamentoDeSessoes
) -> APIRouter:
    class RotaProtegida(APIRoute):
        def get_route_handler(self):
            handler = super().get_route_handler()

            async def protegido(request: Request):
                sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
                if sessao is None:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Autenticação necessária"},
                        headers={"WWW-Authenticate": "Cookie"},
                    )
                detalhe_id = request.path_params.get("encaminhamento_id")
                if detalhe_id is not None and request.method == "GET":
                    if not ObjectId.is_valid(detalhe_id):
                        return JSONResponse(
                            status_code=404, content={"detail": "Encaminhamento não encontrado"}
                        )
                    try:
                        await run_in_threadpool(
                            servico.buscar_por_id, detalhe_id, sessao.usuario_id
                        )
                    except EncaminhamentoError as erro:
                        return JSONResponse(
                            status_code=erro.status_code, content={"detail": erro.detail}
                        )
                permitidos = (
                    {"escopo", "ponto_id", "item_id", "status", "offset", "limite"}
                    if request.method == "GET" and detalhe_id is None
                    else set()
                )
                extras = set(request.query_params) - permitidos
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
                try:
                    return await handler(request)
                except RequestValidationError as erro:
                    return JSONResponse(
                        status_code=400, content={"detail": jsonable_encoder(erro.errors())}
                    )

            return protegido

    router = APIRouter(
        prefix="/api/encaminhamentos", tags=["encaminhamentos"], route_class=RotaProtegida
    )

    def usuario(request: Request) -> str:
        sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
        if sessao is None:
            raise HTTPException(status_code=401, detail="Autenticação necessária")
        return sessao.usuario_id

    @router.get("", response_model=list[EncaminhamentoResponse])
    def listar(
        request: Request,
        escopo: str = Query(default="autor", pattern="^(autor|operador)$"),
        ponto_id: str | None = None,
        item_id: str | None = None,
        status: str | None = None,
        offset: int = Query(default=0, ge=0),
        limite: int = Query(default=20, ge=1, le=100),
    ) -> list[EncaminhamentoResponse]:
        return servico.listar(
            usuario(request),
            escopo=escopo,
            ponto_id=ponto_id,
            item_id=item_id,
            status=status,
            offset=offset,
            limite=limite,
        )

    @router.get("/{encaminhamento_id}", response_model=EncaminhamentoResponse)
    def buscar(encaminhamento_id: str, request: Request) -> EncaminhamentoResponse:
        return servico.buscar_por_id(encaminhamento_id, usuario(request))

    @router.post("", response_model=EncaminhamentoResponse, status_code=status.HTTP_201_CREATED)
    def criar(dados: EncaminhamentoCreateRequest, request: Request) -> EncaminhamentoResponse:
        return servico.criar(dados, usuario(request))

    @router.post("/{encaminhamento_id}/acoes", response_model=EncaminhamentoResponse)
    def executar_acao(
        encaminhamento_id: str, dados: EncaminhamentoAcaoRequest, request: Request
    ) -> EncaminhamentoResponse:
        return servico.executar(encaminhamento_id, dados, usuario(request))

    return router


def tratar_erro_encaminhamento(erro: EncaminhamentoError) -> JSONResponse:
    return JSONResponse(status_code=erro.status_code, content={"detail": erro.detail})
