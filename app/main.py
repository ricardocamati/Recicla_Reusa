from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from app.api.usuarios import criar_router
from app.config import obter_configuracoes
from app.exceptions import UsuarioNaoEncontradoError
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.services.usuario_service import RepositorioDeUsuarios, UsuarioService


def criar_app(repositorio: RepositorioDeUsuarios | None = None) -> FastAPI:
    cliente_mongo: MongoClient | None = None

    if repositorio is None:
        configuracoes = obter_configuracoes()
        cliente_mongo = MongoClient(configuracoes.mongo_uri, tz_aware=True)
        colecao = cliente_mongo[configuracoes.mongo_database]["usuarios"]
        repositorio = MongoUsuarioRepository(colecao)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if cliente_mongo is not None:
            cliente_mongo.close()

    aplicacao = FastAPI(
        title="Recicla/Reusa",
        description="PoC inicial com CRUD de usuários",
        version="0.1.0",
        lifespan=lifespan,
    )
    aplicacao.include_router(criar_router(UsuarioService(repositorio)))

    @aplicacao.exception_handler(UsuarioNaoEncontradoError)
    async def tratar_usuario_nao_encontrado(
        request: Request, exception: UsuarioNaoEncontradoError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": 404,
                "error": "Not Found",
                "message": str(exception),
                "path": request.url.path,
                "fieldErrors": {},
            },
        )

    @aplicacao.exception_handler(RequestValidationError)
    async def tratar_entrada_invalida(
        request: Request, exception: RequestValidationError
    ) -> JSONResponse:
        erros_de_campo: dict[str, str] = {}
        for erro in exception.errors():
            campo = str(erro["loc"][-1])
            erros_de_campo.setdefault(campo, erro["msg"])
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": 400,
                "error": "Bad Request",
                "message": "Dados de entrada inválidos",
                "path": request.url.path,
                "fieldErrors": erros_de_campo,
            },
        )

    return aplicacao


app = criar_app()
