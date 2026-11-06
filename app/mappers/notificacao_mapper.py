from app.models.notificacao import Notificacao
from app.schemas.notificacao import NotificacaoResponse


class NotificacaoMapper:
    @staticmethod
    def para_resposta(notificacao: Notificacao) -> NotificacaoResponse:
        if notificacao.id is None:
            raise ValueError("Notificação persistida deve possuir identificador")
        return NotificacaoResponse(
            id=notificacao.id,
            usuario_id=notificacao.usuario_id,
            item_id=notificacao.item_id,
            interesse_id=notificacao.interesse_id,
            tipo=notificacao.tipo,
            titulo=notificacao.titulo,
            mensagem=notificacao.mensagem,
            evento_id=notificacao.evento_id,
            link=notificacao.link,
            lida=notificacao.lida,
            data_leitura=notificacao.data_leitura,
            data_adicao=notificacao.data_adicao,
            data_modificacao=notificacao.data_modificacao,
        )
