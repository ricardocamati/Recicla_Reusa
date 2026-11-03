from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.indicador import IndicadorResponse
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes
from app.services.indicador_service import IndicadorService


def criar_router_indicadores(
    servico: IndicadorService,
    sessoes: ArmazenamentoDeSessoes,
) -> APIRouter:
    router = APIRouter(prefix="/api/indicadores", tags=["indicadores"])

    @router.get("", response_model=IndicadorResponse)
    def obter(request: Request) -> IndicadorResponse:
        if sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME)) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return servico.obter()

    return router
