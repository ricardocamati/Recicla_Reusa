from app.models.item import Item
from app.schemas.item import ItemCreateRequest, ItemResponse, ItemUpdateRequest


def _dados_comuns(request: Item | ItemCreateRequest | ItemUpdateRequest) -> dict:
    return {
        "titulo": request.titulo,
        "descricao": request.descricao,
        "categoria": request.categoria,
        "marca": request.marca,
        "modelo": request.modelo,
        "condicao": request.condicao,
        "destino": request.destino,
        "valor": request.valor,
    }


class ItemMapper:
    @staticmethod
    def para_modelo(
        request: ItemCreateRequest,
        *,
        proprietario_id: str,
        instante,
    ) -> Item:
        return Item(
            **_dados_comuns(request),
            status="disponivel",
            proprietario_id=proprietario_id,
            data_adicao=instante,
            data_modificacao=instante,
        )

    @staticmethod
    def para_resposta(item: Item, *, cidade_proprietario: str) -> ItemResponse:
        if item.id is None:
            raise ValueError("Item persistido deve possuir identificador")
        return ItemResponse(
            id=item.id,
            **_dados_comuns(item),
            status=item.status,
            proprietario_id=item.proprietario_id,
            cidade_proprietario=cidade_proprietario,
            data_adicao=item.data_adicao,
            data_modificacao=item.data_modificacao,
        )

    @staticmethod
    def atualizar_modelo(
        request: ItemUpdateRequest,
        item: Item,
        *,
        instante,
    ) -> None:
        for campo, valor in _dados_comuns(request).items():
            setattr(item, campo, valor)
        item.data_modificacao = instante
