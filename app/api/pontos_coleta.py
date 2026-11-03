from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.schemas.item import CategoriaItem
from app.schemas.ponto_coleta import (
    PontoColetaCreateRequest,
    PontoColetaResponse,
    PontoColetaUpdateRequest,
)
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes, Sessao
from app.services.ponto_coleta_service import PontoColetaService


def criar_router_pontos_coleta(
    servico: PontoColetaService,
    sessoes: ArmazenamentoDeSessoes,
) -> APIRouter:
    router = APIRouter(prefix="/api/pontos-coleta", tags=["pontos-coleta"])

    def sessao_obrigatoria(request: Request) -> Sessao:
        sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
        if sessao is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return sessao

    def exigir_operador(sessao: Sessao) -> None:
        if sessao.tipo != "ponto_coleta":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ação permitida somente para pontos de coleta",
            )

    @router.get("", response_model=list[PontoColetaResponse])
    def listar(
        request: Request,
        cidade: str | None = Query(default=None, min_length=1, max_length=160),
        categoria: CategoriaItem | None = Query(default=None),
        escopo: Literal["meus"] | None = Query(default=None),
        offset: int = Query(default=0, ge=0),
        limite: int = Query(default=20, ge=1, le=100),
    ) -> list[PontoColetaResponse]:
        sessao = sessao_obrigatoria(request)
        if escopo == "meus" and sessao.tipo != "ponto_coleta":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ação não permitida")
        return servico.listar(
            cidade=cidade,
            categoria=categoria,
            escopo=escopo,
            usuario_id=sessao.usuario_id,
            offset=offset,
            limite=limite,
        )

    @router.post("", response_model=PontoColetaResponse, status_code=status.HTTP_201_CREATED)
    def criar(
        dados: PontoColetaCreateRequest,
        response: Response,
        request: Request,
    ) -> PontoColetaResponse:
        sessao = sessao_obrigatoria(request)
        exigir_operador(sessao)
        ponto = servico.criar(dados, responsavel_id=sessao.usuario_id)
        response.headers["Location"] = f"/api/pontos-coleta/{ponto.id}"
        return ponto

    @router.get("/{ponto_id}", response_model=PontoColetaResponse)
    def buscar(ponto_id: str, request: Request) -> PontoColetaResponse:
        sessao_obrigatoria(request)
        return servico.buscar_por_id(ponto_id)

    @router.put("/{ponto_id}", response_model=PontoColetaResponse)
    def atualizar(
        ponto_id: str,
        dados: PontoColetaUpdateRequest,
        request: Request,
    ) -> PontoColetaResponse:
        sessao = sessao_obrigatoria(request)
        exigir_operador(sessao)
        return servico.atualizar(ponto_id, dados, responsavel_id=sessao.usuario_id)

    @router.delete("/{ponto_id}", status_code=status.HTTP_204_NO_CONTENT)
    def excluir(ponto_id: str, request: Request) -> Response:
        sessao = sessao_obrigatoria(request)
        exigir_operador(sessao)
        servico.excluir(ponto_id, responsavel_id=sessao.usuario_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
