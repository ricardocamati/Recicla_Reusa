from app.models.interesse import Interesse
from app.schemas.interesse import InteresseResponse


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
            data_adicao=interesse.data_adicao,
            data_modificacao=interesse.data_modificacao,
        )
