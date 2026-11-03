from app.models.item import EventoHistorico, Item
from app.schemas.item import (
    EventoHistoricoResponse,
    ItemCreateRequest,
    ItemResponse,
    ItemUpdateRequest,
)


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
        "especificacoes": dict(getattr(request, "especificacoes", {}) or {}),
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
            historico=[
                EventoHistorico(
                    etapa="cadastro",
                    status="disponivel",
                    data_evento=instante,
                    responsavel_id=proprietario_id,
                    observacao="Item cadastrado",
                )
            ],
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
            ponto_coleta_id=item.ponto_coleta_id,
            beneficiario_id=item.beneficiario_id,
            comprador_id=item.comprador_id,
            historico=[
                EventoHistoricoResponse(
                    etapa=evento.etapa,
                    status=evento.status,
                    data_evento=evento.data_evento,
                    responsavel_id=evento.responsavel_id,
                    observacao=evento.observacao,
                )
                for evento in item.historico
            ],
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

    @staticmethod
    def registrar_transicao(
        item: Item,
        *,
        novo_status: str,
        responsavel_id: str,
        instante,
        observacao: str | None = None,
    ) -> None:
        origem = item.status
        item.historico.append(
            EventoHistorico(
                etapa="transicao",
                status=novo_status,
                data_evento=instante,
                responsavel_id=responsavel_id,
                observacao=observacao or f"{origem} -> {novo_status}",
            )
        )
        item.status = novo_status
        item.data_modificacao = instante
