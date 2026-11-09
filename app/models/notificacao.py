from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class EventoNotificacao:
    """Descrição de um evento de domínio, sem destinatário definido."""

    tipo: str
    titulo: str
    mensagem: str
    evento_id: str
    link: str | None = None


def evento_de_status_item(
    item_id: str,
    titulo: str | None,
    status: str,
    instante: datetime,
    *,
    concluido: bool = False,
) -> EventoNotificacao:
    """Evento de mudança de status do item, usado por itens e interesses."""
    alvo = f'"{titulo}"' if titulo else "que você acompanha"
    return EventoNotificacao(
        tipo="item_concluido" if concluido else "status_item_alterado",
        titulo="Item concluído" if concluido else "Status do item atualizado",
        mensagem=f"O item {alvo} passou para {status}.",
        evento_id=f"item:{item_id}:{status}:{instante.isoformat()}",
    )


LINK_POR_TIPO: dict[str, str] = {
    "interesse_recebido": "/interesses.html",
    "interesse_aceito": "/interesses.html",
    "interesse_recusado": "/interesses.html",
    "interesse_cancelado": "/interesses.html",
    "entrega_declarada": "/interesses.html",
    "item_concluido": "/interesses.html",
    "status_item_alterado": "/interesses.html",
}


def link_do_tipo(tipo: str) -> str | None:
    """Destino interno do aviso, para o destinatário agir sem procurar a tela."""
    return LINK_POR_TIPO.get(tipo)


@dataclass(slots=True)
class Notificacao:
    usuario_id: str
    item_id: str
    tipo: str
    titulo: str
    mensagem: str
    evento_id: str
    lida: bool
    data_adicao: datetime
    data_modificacao: datetime
    interesse_id: str | None = None
    link: str | None = None
    data_leitura: datetime | None = None
    id: str | None = None
