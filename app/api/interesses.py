from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.exceptions import InteresseError
from app.schemas.interesse import (
    CombinacaoAceiteRequest,
    CombinacaoRequest,
    InteresseAcaoRequest,
    InteresseCreateRequest,
    InteresseResponse,
    InteresseUpdateRequest,
    StatusInteresse,
)
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes, Sessao
from app.services.interesse_service import InteresseService


def criar_router_interesses(servico: InteresseService, sessoes: ArmazenamentoDeSessoes) -> APIRouter:
    class RotaProtegida(APIRoute):
        def get_route_handler(self):
            handler = super().get_route_handler()

            async def protegido(request: Request):
                sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
                if sessao is None:
                    return JSONResponse(status_code=401, content={"detail": "Autenticação necessária"}, headers={"WWW-Authenticate": "Cookie"})
                tipo = sessao.tipo
                if tipo != "pessoa":
                    return JSONResponse(status_code=403, content={"detail": "Ação não permitida para este perfil"})
                detalhe_id = request.path_params.get("interesse_id")
                if detalhe_id is not None:
                    if not ObjectId.is_valid(detalhe_id):
                        return JSONResponse(status_code=404, content={"detail": "Interesse não encontrado"})
                    try:
                        await run_in_threadpool(servico.buscar_por_id, detalhe_id, sessao.usuario_id)
                    except InteresseError as erro:
                        return JSONResponse(status_code=erro.status_code, content={"detail": erro.detail})
                permitidos = {"escopo", "item_id", "status", "offset", "limite"} if detalhe_id is None and request.method == "GET" else set()
                extras = set(request.query_params) - permitidos
                if extras:
                    return JSONResponse(status_code=400, content={"detail": [
                        {"loc": ["query", campo], "msg": "Parâmetro desconhecido", "type": "extra_forbidden"}
                        for campo in sorted(extras)
                    ]})
                item_id = request.query_params.get("item_id")
                if item_id is not None and not ObjectId.is_valid(item_id):
                    return JSONResponse(status_code=400, content={"detail": "item_id inválido"})
                try:
                    return await handler(request)
                except RequestValidationError as erro:
                    return JSONResponse(status_code=400, content={"detail": jsonable_encoder(erro.errors())})

            return protegido

    router = APIRouter(prefix="/api/interesses", tags=["interesses"], route_class=RotaProtegida)

    def sessao_obrigatoria(request: Request) -> Sessao:
        sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
        if sessao is None:
            raise HTTPException(status_code=401, detail="Autenticação necessária", headers={"WWW-Authenticate": "Cookie"})
        return sessao

    def chamar(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InteresseError as erro:
            raise HTTPException(status_code=erro.status_code, detail=erro.detail) from erro

    @router.post("", response_model=InteresseResponse, status_code=status.HTTP_201_CREATED)
    def criar(dados: InteresseCreateRequest, request: Request, response: Response):
        sessao = sessao_obrigatoria(request)
        interesse = chamar(servico.criar, dados, sessao.usuario_id)
        response.headers["Location"] = f"/api/interesses/{interesse.id}"
        return interesse

    @router.get("", response_model=list[InteresseResponse])
    def listar(request: Request, escopo: str = Query(default="meus", pattern="^(meus|recebidos)$"), item_id: str | None = Query(default=None, min_length=1, max_length=64), status_interesse: StatusInteresse | None = Query(default=None, alias="status"), offset: int = Query(default=0, ge=0), limite: int = Query(default=20, ge=1, le=100)):
        sessao = sessao_obrigatoria(request)
        return chamar(servico.listar, sessao.usuario_id, escopo=escopo, item_id=item_id, status=status_interesse, offset=offset, limite=limite)

    @router.get("/{interesse_id}", response_model=InteresseResponse)
    def buscar_por_id(interesse_id: str, request: Request):
        sessao = sessao_obrigatoria(request)
        return chamar(servico.buscar_por_id, interesse_id, sessao.usuario_id)

    @router.put("/{interesse_id}/combinacao", response_model=InteresseResponse)
    def propor_combinacao(
        interesse_id: str, dados: CombinacaoRequest, request: Request
    ):
        sessao = sessao_obrigatoria(request)
        return chamar(servico.propor_combinacao, interesse_id, dados, sessao.usuario_id)

    @router.post("/{interesse_id}/combinacao/aceite", response_model=InteresseResponse)
    def aceitar_combinacao(
        interesse_id: str, dados: CombinacaoAceiteRequest, request: Request
    ):
        sessao = sessao_obrigatoria(request)
        return chamar(servico.aceitar_combinacao, interesse_id, dados, sessao.usuario_id)

    @router.post("/{interesse_id}/acoes", response_model=InteresseResponse)
    def executar_acao(
        interesse_id: str, dados: InteresseAcaoRequest, request: Request
    ):
        sessao = sessao_obrigatoria(request)
        return chamar(servico.executar_acao, interesse_id, dados, sessao.usuario_id)

    @router.patch("/{interesse_id}", response_model=InteresseResponse)
    def atualizar(interesse_id: str, dados: InteresseUpdateRequest, request: Request):
        sessao = sessao_obrigatoria(request)
        return chamar(servico.atualizar, interesse_id, dados, sessao.usuario_id)

    return router
