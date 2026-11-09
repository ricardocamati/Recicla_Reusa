from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from app.api.itens import criar_router_itens
from app.api.indicadores import criar_router_indicadores
from app.api.interesses import criar_router_interesses
from app.api.notificacoes import criar_router_notificacoes
from app.api.pontos_coleta import criar_router_pontos_coleta
from app.api.usuarios import criar_routers
from app.config import Settings
from app.exceptions import (
    ConflitoEstadoError,
    EmailDuplicadoError,
    FluxoItemError,
    InteresseError,
    ItemNaoAutorizadoError,
    ItemNaoEncontradoError,
    NotificacaoNaoEncontradaError,
    PontoIncompativelError,
    PontoNaoEncontradoError,
    ReferenciaAtivaError,
    TransicaoInvalidaError,
    UsuarioNaoEncontradoError,
)
from app.repositories.mongo_item_repository import MongoItemRepository
from app.repositories.mongo_indicador_repository import MongoIndicadorRepository
from app.repositories.mongo_interesse_repository import MongoInteresseRepository
from app.repositories.mongo_notificacao_repository import MongoNotificacaoRepository
from app.repositories.mongo_ponto_coleta_repository import MongoPontoColetaRepository
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.security.origins import origem_permitida, requisicao_com_sessao_mutavel
from app.security.sessions import ArmazenamentoDeSessoes
from app.services.item_service import ItemService, RepositorioDeItens
from app.services.indicador_service import IndicadorService, RepositorioDeIndicadores
from app.services.interesse_service import InteresseService, RepositorioDeInteresses
from app.services.notificacao_service import NotificacaoService, RepositorioDeNotificacoes
from app.services.ponto_coleta_service import PontoColetaService, RepositorioDePontos
from app.services.usuario_service import UsuarioService, RepositorioDeUsuarios


def criar_app(
    repositorio: RepositorioDeUsuarios | None = None,
    *,
    repositorio_itens: RepositorioDeItens | None = None,
    repositorio_pontos: RepositorioDePontos | None = None,
    repositorio_interesses: RepositorioDeInteresses | None = None,
    repositorio_notificacoes: RepositorioDeNotificacoes | None = None,
    repositorio_indicadores: RepositorioDeIndicadores | None = None,
    relogio: Callable[[], datetime] | None = None,
    sessoes: ArmazenamentoDeSessoes | None = None,
) -> FastAPI:
    settings = Settings()
    cliente_mongo = None
    repositorio_mongo = None
    repositorio_itens_mongo = None
    repositorio_pontos_mongo = None
    repositorio_interesses_mongo = None
    repositorio_notificacoes_mongo = None
    repositorio_indicadores_mongo = None
    if repositorio is None:
        cliente_mongo = MongoClient(settings.mongo_uri)
        banco = cliente_mongo[settings.mongo_database]
        colecao_usuarios = banco[settings.mongo_collection_usuarios]
        colecao_pontos = banco[settings.mongo_collection_pontos_coleta]
        colecao_interesses = banco[settings.mongo_collection_interesses]
        colecao_notificacoes = banco[settings.mongo_collection_notificacoes]
        colecao_itens = banco[settings.mongo_collection_itens]
        repositorio_mongo = MongoUsuarioRepository(
            colecao_usuarios,
            criar_indice=False,
            colecao_pontos_coleta=colecao_pontos,
            colecao_interesses=colecao_interesses,
            colecao_itens=colecao_itens,
        )
        repositorio = repositorio_mongo
        repositorio_itens_mongo = MongoItemRepository(
            colecao_itens,
            criar_indices=False,
            colecao_interesses=colecao_interesses,
            colecao_notificacoes=colecao_notificacoes,
        )
        repositorio_itens = repositorio_itens_mongo
        repositorio_pontos_mongo = MongoPontoColetaRepository(
            colecao_pontos, criar_indices=False,
        )
        repositorio_pontos = repositorio_pontos_mongo
        repositorio_interesses_mongo = MongoInteresseRepository(
            colecao_interesses,
            colecao_itens,
            colecao_usuarios,
            criar_indices=False,
            colecao_notificacoes=colecao_notificacoes,
        )
        repositorio_interesses = repositorio_interesses_mongo
        repositorio_notificacoes_mongo = MongoNotificacaoRepository(
            colecao_notificacoes, criar_indices=False
        )
        repositorio_notificacoes = repositorio_notificacoes_mongo
        repositorio_indicadores_mongo = MongoIndicadorRepository(colecao_itens)
        repositorio_indicadores = repositorio_indicadores_mongo

    relogio = relogio or (lambda: datetime.now(UTC))
    sessoes = sessoes or ArmazenamentoDeSessoes(relogio=relogio)
    servico = UsuarioService(repositorio, relogio=relogio)
    servico_pontos = (
        PontoColetaService(repositorio_pontos, repositorio, relogio=relogio)
        if repositorio_pontos is not None
        else None
    )
    servico_itens = (
        ItemService(repositorio_itens, repositorio, relogio=relogio,
                    interesses=repositorio_interesses)
        if repositorio_itens is not None
        else None
    )
    servico_interesses = (
        InteresseService(repositorio_interesses, relogio=relogio)
        if repositorio_interesses is not None
        else None
    )
    servico_notificacoes = (
        NotificacaoService(repositorio_notificacoes, relogio=relogio)
        if repositorio_notificacoes is not None
        else None
    )
    servico_indicadores = (
        IndicadorService(repositorio_indicadores)
        if repositorio_indicadores is not None
        else None
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if repositorio_mongo is not None:
            repositorio_mongo.criar_indice_email()
        if repositorio_itens_mongo is not None:
            repositorio_itens_mongo.criar_indices()
        if repositorio_pontos_mongo is not None:
            repositorio_pontos_mongo.criar_indices()
        if repositorio_interesses_mongo is not None:
            repositorio_interesses_mongo.criar_indices()
        if repositorio_notificacoes_mongo is not None:
            repositorio_notificacoes_mongo.criar_indices()
        yield

    app = FastAPI(title="Recicla/Reusa", version="1.0.0", lifespan=lifespan)
    origens_configuradas = settings.origens_cors()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origens_configuradas,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def proteger_mutacao_por_origem(request: Request, call_next):
        if requisicao_com_sessao_mutavel(request) and not origem_permitida(
            request,
            origens_configuradas,
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Origem não permitida"},
            )
        return await call_next(request)

    if cliente_mongo is not None:
        app.state.mongo_client = cliente_mongo
        app.state.mongo_repository = repositorio_mongo
        app.state.mongo_item_repository = repositorio_itens_mongo
        app.state.mongo_ponto_repository = repositorio_pontos_mongo
        app.state.mongo_interesse_repository = repositorio_interesses_mongo
        app.state.mongo_notificacao_repository = repositorio_notificacoes_mongo
        app.state.mongo_indicador_repository = repositorio_indicadores_mongo

    router_usuarios, router_auth = criar_routers(
        servico,
        sessoes,
        cookies_seguros=settings.secure_cookies,
    )
    app.include_router(router_usuarios)
    app.include_router(router_auth)
    if servico_itens is not None:
        app.include_router(criar_router_itens(servico_itens, sessoes))
    if servico_pontos is not None:
        app.include_router(
            criar_router_pontos_coleta(
                servico_pontos, sessoes
            )
        )
    if servico_interesses is not None:
        app.include_router(criar_router_interesses(servico_interesses, sessoes))
    if servico_notificacoes is not None:
        app.include_router(criar_router_notificacoes(servico_notificacoes, sessoes))
    if servico_indicadores is not None:
        app.include_router(criar_router_indicadores(servico_indicadores, sessoes))

    @app.get("/health", tags=["infraestrutura"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(InteresseError)
    async def interesse_handler(request: Request, exc: InteresseError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(FluxoItemError)
    async def fluxo_item_handler(request: Request, exc: FluxoItemError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(NotificacaoNaoEncontradaError)
    async def notificacao_nao_encontrada_handler(
        request: Request,
        exc: NotificacaoNaoEncontradaError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404, content={"detail": "Notificação não encontrada"}
        )

    @app.exception_handler(EmailDuplicadoError)
    async def email_duplicado_handler(
        request: Request,
        exc: EmailDuplicadoError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "E-mail já cadastrado"})

    @app.exception_handler(UsuarioNaoEncontradoError)
    async def usuario_nao_encontrado_handler(
        request: Request,
        exc: UsuarioNaoEncontradoError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Usuário não encontrado"})

    @app.exception_handler(ItemNaoEncontradoError)
    async def item_nao_encontrado_handler(
        request: Request,
        exc: ItemNaoEncontradoError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Item não encontrado"})

    @app.exception_handler(ItemNaoAutorizadoError)
    async def item_nao_autorizado_handler(
        request: Request,
        exc: ItemNaoAutorizadoError,
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": "Ação não permitida"})

    @app.exception_handler(TransicaoInvalidaError)
    async def transicao_invalida_handler(
        request: Request,
        exc: TransicaoInvalidaError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Transição de status inválida: {exc.origem} -> {exc.destino}"},
        )

    @app.exception_handler(ConflitoEstadoError)
    async def conflito_estado_handler(
        request: Request,
        exc: ConflitoEstadoError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Item alterado por outra operação"})

    @app.exception_handler(PontoNaoEncontradoError)
    async def ponto_nao_encontrado_handler(
        request: Request,
        exc: PontoNaoEncontradoError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Ponto de coleta não encontrado"})

    @app.exception_handler(PontoIncompativelError)
    async def ponto_incompativel_handler(
        request: Request,
        exc: PontoIncompativelError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": "Ponto de coleta não aceita a categoria do item"},
        )

    @app.exception_handler(ReferenciaAtivaError)
    async def referencia_ativa_handler(
        request: Request,
        exc: ReferenciaAtivaError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Registro possui referências ativas e não pode ser excluído"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    return app


app = criar_app()
