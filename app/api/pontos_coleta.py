from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.schemas.item import CategoriaItem
from app.schemas.ponto_coleta import (
    PontoColetaCreateRequest,
    PontoColetaPublicResponse,
    PontoColetaResponse,
    PontoColetaUpdateRequest,
    PontoSituacaoRequest,
)
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes, Sessao
from app.services.ponto_coleta_service import PontoColetaService


def criar_router_pontos_coleta(
    servico: PontoColetaService,
    sessoes: ArmazenamentoDeSessoes,
    servico_encaminhamentos=None,
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

    def selecionar_escopo(request: Request) -> Sessao | None:
        """Autoriza gestão antes de validar filtros; leitura pública não usa sessão."""
        escopo = request.query_params.get("escopo")
        sessao = None
        if escopo == "meus":
            sessao = sessao_obrigatoria(request)
            exigir_operador(sessao)
        elif escopo is not None:
            raise HTTPException(status_code=400, detail="Escopo de consulta inválido")
        permitidos = {"escopo"}
        if "ponto_id" not in request.path_params:
            permitidos.update({"cidade", "categoria", "offset", "limite"})
            if escopo == "meus":
                permitidos.add("ativo")
        for campo in request.query_params:
            if campo not in permitidos:
                raise HTTPException(status_code=400, detail=f"Parâmetro de consulta não permitido: {campo}")
            if len(request.query_params.getlist(campo)) != 1:
                raise HTTPException(status_code=400, detail=f"Parâmetro de consulta repetido: {campo}")
        if "cidade" in request.query_params and not request.query_params["cidade"].strip():
            raise HTTPException(status_code=400, detail="Cidade não pode estar vazia")
        return sessao

    @router.get("", response_model=list[PontoColetaResponse | PontoColetaPublicResponse])
    def listar(
        request: Request,
        cidade: str | None = Query(default=None, min_length=1, max_length=160),
        categoria: CategoriaItem | None = Query(default=None),
        escopo: Literal["meus"] | None = Query(default=None),
        offset: int = Query(default=0, ge=0),
        limite: int = Query(default=20, ge=1, le=100),
        ativo: bool | None = Query(default=None),
        sessao: Sessao | None = Depends(selecionar_escopo),
    ) -> list[PontoColetaResponse | PontoColetaPublicResponse]:
        if escopo is None:
            return servico.listar_publicos(
                cidade=cidade, categoria=categoria, offset=offset, limite=limite,
            )
        assert sessao is not None
        return servico.listar(
            cidade=cidade,
            categoria=categoria,
            escopo=escopo,
            usuario_id=sessao.usuario_id,
            ativo=ativo,
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

    @router.get("/{ponto_id}", response_model=PontoColetaResponse | PontoColetaPublicResponse)
    def buscar(
        ponto_id: str,
        request: Request,
        escopo: Literal["meus"] | None = Query(default=None),
        sessao: Sessao | None = Depends(selecionar_escopo),
    ) -> PontoColetaResponse | PontoColetaPublicResponse:
        if escopo == "meus":
            assert sessao is not None
            return servico.buscar_proprio(ponto_id, responsavel_id=sessao.usuario_id)
        return servico.buscar_publico(ponto_id)

    @router.put("/{ponto_id}", response_model=PontoColetaResponse)
    def atualizar(
        ponto_id: str,
        dados: PontoColetaUpdateRequest,
        request: Request,
    ) -> PontoColetaResponse:
        sessao = sessao_obrigatoria(request)
        exigir_operador(sessao)
        return servico.atualizar(ponto_id, dados, responsavel_id=sessao.usuario_id)

    @router.post("/{ponto_id}/situacao", response_model=PontoColetaResponse)
    def definir_situacao(
        ponto_id: str,
        dados: PontoSituacaoRequest,
        request: Request,
    ) -> PontoColetaResponse:
        sessao = sessao_obrigatoria(request)
        exigir_operador(sessao)
        resposta = servico.definir_ativo(
            ponto_id, dados.ativo, responsavel_id=sessao.usuario_id
        )
        if not dados.ativo and servico_encaminhamentos is not None:
            servico_encaminhamentos.avisar_ponto_inativado(ponto_id)
        return resposta

    @router.delete("/{ponto_id}", status_code=status.HTTP_204_NO_CONTENT)
    def excluir(ponto_id: str, request: Request) -> Response:
        sessao = sessao_obrigatoria(request)
        exigir_operador(sessao)
        servico.excluir(ponto_id, responsavel_id=sessao.usuario_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
