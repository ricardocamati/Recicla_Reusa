from app.models.interesse import Interesse
from app.schemas.interesse import EventoInteresseResponse, InteresseResponse


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
