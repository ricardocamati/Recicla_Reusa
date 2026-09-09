from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from app.api.usuarios import criar_routers
from app.config import Settings
from app.exceptions import EmailDuplicadoError, UsuarioNaoEncontradoError
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.security.sessions import ArmazenamentoDeSessoes
from app.services.usuario_service import UsuarioService, RepositorioDeUsuarios


def criar_app(
    repositorio: RepositorioDeUsuarios | None = None,
    *,
    relogio: Callable[[], datetime] | None = None,
    sessoes: ArmazenamentoDeSessoes | None = None,
) -> FastAPI:
    settings = Settings()
    cliente_mongo = None
    repositorio_mongo = None
    if repositorio is None:
        cliente_mongo = MongoClient(settings.mongo_uri)
        colecao = cliente_mongo[settings.mongo_database][settings.mongo_collection_usuarios]
        repositorio_mongo = MongoUsuarioRepository(colecao, criar_indice=False)
        repositorio = repositorio_mongo

    relogio = relogio or (lambda: datetime.now(UTC))
    sessoes = sessoes or ArmazenamentoDeSessoes(relogio=relogio)
    servico = UsuarioService(repositorio, relogio=relogio)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if repositorio_mongo is not None:
            repositorio_mongo.criar_indice_email()
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

    router_usuarios, router_auth = criar_routers(
        servico,
        sessoes,
        cookies_seguros=settings.secure_cookies,
    )
    app.include_router(router_usuarios)
    app.include_router(router_auth)

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
