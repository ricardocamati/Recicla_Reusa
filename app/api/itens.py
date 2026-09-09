from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.schemas.item import (
    CategoriaItem,
    CondicaoItem,
    DestinoItem,
    FiltrosItem,
    ItemCreateRequest,
    ItemResponse,
    ItemUpdateRequest,
    StatusItem,
)
from app.security.sessions import SESSION_COOKIE_NAME, ArmazenamentoDeSessoes, Sessao
from app.services.item_service import ItemService


def criar_router_itens(
    servico: ItemService,
    sessoes: ArmazenamentoDeSessoes,
) -> APIRouter:
    router = APIRouter(prefix="/api/itens", tags=["itens"])

    def sessao_obrigatoria(request: Request) -> Sessao:
        sessao = sessoes.buscar(request.cookies.get(SESSION_COOKIE_NAME))
        if sessao is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária",
                headers={"WWW-Authenticate": "Cookie"},
            )
        return sessao

    def exigir_doador(sessao: Sessao) -> None:
        if sessao.tipo != "doador":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ação permitida somente para doadores",
            )

    @router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
    def criar(request: ItemCreateRequest, response: Response, contexto: Request) -> ItemResponse:
        sessao = sessao_obrigatoria(contexto)
        exigir_doador(sessao)
        item = servico.criar(request, proprietario_id=sessao.usuario_id)
        response.headers["Location"] = f"/api/itens/{item.id}"
        return item

    @router.get("", response_model=list[ItemResponse])
    def listar(
        request: Request,
        categoria: CategoriaItem | None = Query(default=None),
        condicao: CondicaoItem | None = Query(default=None),
        destino: DestinoItem | None = Query(default=None),
        status_item: StatusItem | None = Query(default=None, alias="status"),
    ) -> list[ItemResponse]:
        sessao_obrigatoria(request)
        filtros = FiltrosItem(
            categoria=categoria,
            condicao=condicao,
            destino=destino,
            status=status_item,
        )
        return servico.listar(filtros)

    @router.get("/{item_id}", response_model=ItemResponse)
    def buscar_por_id(item_id: str, request: Request) -> ItemResponse:
        sessao_obrigatoria(request)
        return servico.buscar_por_id(item_id)

    @router.put("/{item_id}", response_model=ItemResponse)
    def atualizar(
        item_id: str,
        request: ItemUpdateRequest,
        contexto: Request,
    ) -> ItemResponse:
        sessao = sessao_obrigatoria(contexto)
        exigir_doador(sessao)
        return servico.atualizar(
            item_id,
            request,
            proprietario_id=sessao.usuario_id,
        )

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def excluir(item_id: str, request: Request) -> Response:
        sessao = sessao_obrigatoria(request)
        exigir_doador(sessao)
        servico.excluir(item_id, proprietario_id=sessao.usuario_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
