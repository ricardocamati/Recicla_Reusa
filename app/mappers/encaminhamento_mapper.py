from app.models.encaminhamento import Encaminhamento
from app.schemas.encaminhamento import (
    EncaminhamentoResponse,
    EventoEncaminhamentoResponse,
)


class EncaminhamentoMapper:
    @staticmethod
    def para_resposta(encaminhamento: Encaminhamento) -> EncaminhamentoResponse:
        if encaminhamento.id is None:
            raise ValueError("Encaminhamento persistido deve possuir identificador")
        return EncaminhamentoResponse(
            id=encaminhamento.id,
            item_id=encaminhamento.item_id,
            autor_id=encaminhamento.autor_id,
            ponto_id=encaminhamento.ponto_id,
            status=encaminhamento.status,
            motivo=encaminhamento.motivo,
            historico=[
                EventoEncaminhamentoResponse(
                    status=evento.status,
                    data_evento=evento.data_evento,
                    ator_id=evento.ator_id,
                    motivo=evento.motivo,
                )
                for evento in encaminhamento.historico
            ],
            data_adicao=encaminhamento.data_adicao,
            data_modificacao=encaminhamento.data_modificacao,
        )
