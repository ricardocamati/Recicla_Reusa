from app.models.interesse import Combinacao, Interesse
from app.schemas.interesse import (
    CombinacaoResponse,
    EventoInteresseResponse,
    InteresseResponse,
)


def _combinacao(combinacao: Combinacao | None) -> CombinacaoResponse | None:
    if combinacao is None:
        return None
    return CombinacaoResponse(
        local_texto=combinacao.local_texto,
        previsao=combinacao.previsao,
        observacao=combinacao.observacao,
        revisao=combinacao.revisao,
        proposto_por=combinacao.proposto_por,
        proposto_em=combinacao.proposto_em,
        aceito_por=combinacao.aceito_por,
        aceito_em=combinacao.aceito_em,
    )


class InteresseMapper:
    @staticmethod
    def para_resposta(interesse: Interesse) -> InteresseResponse:
        if interesse.id is None:
            raise ValueError("Interesse persistido deve possuir identificador")
        return InteresseResponse(
            id=interesse.id,
            item_id=interesse.item_id,
            usuario_id=interesse.usuario_id,
            status=interesse.status,
            tentativa=interesse.tentativa,
            motivo=interesse.motivo,
            preco_selecionado=interesse.preco_selecionado,
            resultado=interesse.resultado,
            combinacao=_combinacao(interesse.combinacao),
            historico=[
                EventoInteresseResponse(
                    status=evento.status,
                    data_evento=evento.data_evento,
                    ator_id=evento.ator_id,
                    motivo=evento.motivo,
                )
                for evento in interesse.historico
            ],
            data_adicao=interesse.data_adicao,
            data_modificacao=interesse.data_modificacao,
        )
