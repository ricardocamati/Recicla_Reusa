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
from app.api.usuarios import criar_routers
from app.config import Settings
from app.exceptions import (
    EmailDuplicadoError,
    ItemNaoAutorizadoError,
    ItemNaoEncontradoError,
    UsuarioNaoEncontradoError,
)
from app.repositories.mongo_item_repository import MongoItemRepository
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.security.sessions import ArmazenamentoDeSessoes
from app.services.item_service import ItemService, RepositorioDeItens
from app.services.usuario_service import UsuarioService, RepositorioDeUsuarios


def criar_app(
    repositorio: RepositorioDeUsuarios | None = None,
    *,
    repositorio_itens: RepositorioDeItens | None = None,
    relogio: Callable[[], datetime] | None = None,
    sessoes: ArmazenamentoDeSessoes | None = None,
) -> FastAPI:
    settings = Settings()
    cliente_mongo = None
    repositorio_mongo = None
    repositorio_itens_mongo = None
    if repositorio is None:
        cliente_mongo = MongoClient(settings.mongo_uri)
        banco = cliente_mongo[settings.mongo_database]
        colecao_usuarios = banco[settings.mongo_collection_usuarios]
        repositorio_mongo = MongoUsuarioRepository(colecao_usuarios, criar_indice=False)
        repositorio = repositorio_mongo
        colecao_itens = banco[settings.mongo_collection_itens]
        repositorio_itens_mongo = MongoItemRepository(colecao_itens, criar_indices=False)
        repositorio_itens = repositorio_itens_mongo

    relogio = relogio or (lambda: datetime.now(UTC))
    sessoes = sessoes or ArmazenamentoDeSessoes(relogio=relogio)
    servico = UsuarioService(repositorio, relogio=relogio)
    servico_itens = (
        ItemService(repositorio_itens, repositorio, relogio=relogio)
        if repositorio_itens is not None
        else None
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if repositorio_mongo is not None:
            repositorio_mongo.criar_indice_email()
        if repositorio_itens_mongo is not None:
            repositorio_itens_mongo.criar_indices()
        yield

    app = FastAPI(title="Recicla/Reusa", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origens_cors(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    if cliente_mongo is not None:
        app.state.mongo_client = cliente_mongo
        app.state.mongo_repository = repositorio_mongo
        app.state.mongo_item_repository = repositorio_itens_mongo

    router_usuarios, router_auth = criar_routers(
        servico,
        sessoes,
        cookies_seguros=settings.secure_cookies,
    )
    app.include_router(router_usuarios)
    app.include_router(router_auth)
    if servico_itens is not None:
        app.include_router(criar_router_itens(servico_itens, sessoes))

    @app.get("/health", tags=["infraestrutura"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

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
