from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import (
    ConflitoEstadoError,
    FluxoItemError,
    ItemNaoAutorizadoError,
    ItemNaoEncontradoError,
    TransicaoInvalidaError,
    UsuarioNaoEncontradoError,
)
from app.mappers.item_mapper import ItemMapper
from app.models.item import Item
from app.models.notificacao import EventoNotificacao, evento_de_status_item
from app.models.usuario import Usuario
from app.schemas.item import FiltrosItem, ItemCreateRequest, ItemResponse, ItemUpdateRequest

TRANSICOES: dict[str, dict[str, set[str]]] = {
    "doacao": {
        "disponivel": {"reservado"},
        "reservado": {"doado"},
    },
    "descarte": {
        "disponivel": {"encaminhado"},
        "encaminhado": {"coletado"},
    },
    "revenda": {
        "disponivel": {"em_avaliacao"},
        "em_avaliacao": {"recondicionado"},
        "recondicionado": {"vendido"},
    },
}

STATUS_CONCLUIDOS = {"doado", "coletado", "vendido"}


class RepositorioDeItens(Protocol):
    def criar(self, item: Item) -> Item: ...
    def listar(
        self,
        filtros: FiltrosItem,
        *,
        proprietario_ids: set[str] | None = None,
        offset: int = 0,
        limite: int = 20,
        somente_catalogo: bool = False,
    ) -> list[Item]: ...
    def listar_por_proprietario(
        self,
        proprietario_id: str,
        statuses: tuple[str, ...],
        *,
        offset: int = 0,
        limite: int = 20,
    ) -> list[Item]: ...
    def buscar_por_id(self, item_id: str) -> Item | None: ...
    def atualizar(
        self,
        item: Item,
        *,
        status_esperado: str | None = None,
        notificacao: EventoNotificacao | None = None,
    ) -> Item: ...
    def excluir(self, item_id: str) -> None: ...


class RepositorioDeInteressesParaItens(Protocol):
    def buscar_aceito_por_item(self, item_id: str) -> str | None: ...


class CompatibilidadeDePontos(Protocol):
    def garantir_compatibilidade(self, ponto_id: str, categoria: str): ...


class RepositorioDeUsuariosParaItens(Protocol):
    def buscar_por_id(self, usuario_id: str) -> Usuario | None: ...
    def buscar_por_ids(self, usuario_ids: Iterable[str]) -> dict[str, Usuario]: ...
    def buscar_por_cidade(self, cidade: str) -> list[str]: ...


class ItemService:
    def __init__(
        self,
        repositorio: RepositorioDeItens,
        repositorio_usuarios: RepositorioDeUsuariosParaItens,
        *,
        relogio: Callable[[], datetime] | None = None,
        reservas_por_interesse: bool | None = None,
        interesses: RepositorioDeInteressesParaItens | None = None,
        pontos: CompatibilidadeDePontos | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._repositorio_usuarios = repositorio_usuarios
        self._relogio = relogio or (lambda: datetime.now(UTC))
        # Com a coleção de interesses disponível, reservar deixa de ser efeito de PUT.
        self._reservas_por_interesse = (
            interesses is not None
            if reservas_por_interesse is None
            else reservas_por_interesse
        )
        self._interesses = interesses
        self._pontos = pontos

    def criar(self, request: ItemCreateRequest, *, proprietario_id: str) -> ItemResponse:
        proprietario = self._obter_pessoa(proprietario_id)
        status = "disponivel" if request.publicar else "rascunho"
        item = ItemMapper.para_modelo(
            request,
            proprietario_id=proprietario_id,
            instante=self._relogio(),
            status=status,
        )
        criado = self._repositorio.criar(item)
        return self._resposta(criado, proprietario)

    def publicar(self, item_id: str, *, proprietario_id: str) -> ItemResponse:
        """Publica um rascunho; descarte também sai do rascunho, mas fora do catálogo."""
        item = self._buscar_item(item_id)
        proprietario = self._obter_pessoa(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()
        if item.status != "rascunho":
            raise TransicaoInvalidaError(item.status, "disponivel")
        instante = self._relogio()
        item.status = "disponivel"
        item.data_modificacao = instante
        ItemMapper.registrar_transicao(
            item,
            novo_status="disponivel",
            responsavel_id=proprietario_id,
            instante=instante,
            observacao="Item publicado",
        )
        return self._resposta(self._repositorio.atualizar(item), proprietario)

    def arquivar(self, item_id: str, *, proprietario_id: str) -> ItemResponse:
        """Encerra a gestão sem apagar o item nem as referências dele."""
        item = self._buscar_item(item_id)
        proprietario = self._obter_pessoa(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()
        if item.status == "arquivado":
            return self._resposta(item, proprietario)
        instante = self._relogio()
        anterior = item.status
        item.status = "arquivado"
        item.data_modificacao = instante
        ItemMapper.registrar_transicao(
            item,
            novo_status="arquivado",
            responsavel_id=proprietario_id,
            instante=instante,
            observacao=f"Item arquivado a partir de {anterior}",
        )
        return self._resposta(self._repositorio.atualizar(item), proprietario)

    def listar(
        self,
        filtros: FiltrosItem,
        *,
        offset: int = 0,
        limite: int = 20,
    ) -> list[ItemResponse]:
        if filtros.destino == "descarte":
            raise FluxoItemError(400, "Descarte não aparece no catálogo")
        tem_faixa = filtros.preco_min is not None or filtros.preco_max is not None
        if tem_faixa and filtros.destino not in (None, "revenda"):
            raise FluxoItemError(400, "Faixa de preço só se aplica a revenda")
        if (
            filtros.preco_min is not None
            and filtros.preco_max is not None
            and filtros.preco_min > filtros.preco_max
        ):
            raise FluxoItemError(400, "Faixa de preço inválida")
        proprietario_ids = None
        if filtros.cidade:
            proprietario_ids = set(
                self._repositorio_usuarios.buscar_por_cidade(filtros.cidade)
            )
        itens = self._repositorio.listar(
            filtros,
            proprietario_ids=proprietario_ids,
            offset=offset,
            limite=limite,
            somente_catalogo=True,
        )
        proprietarios = self._buscar_proprietarios(itens)
        return [
            self._resposta(item, proprietario=proprietarios.get(item.proprietario_id))
            for item in itens
        ]

    def listar_meus(
        self,
        proprietario_id: str,
        *,
        grupo: str = "ativos",
        offset: int = 0,
        limite: int = 20,
    ) -> list[ItemResponse]:
        grupos = {
            "ativos": ("rascunho", "disponivel"),
            "em_andamento": ("reservado", "encaminhado", "em_avaliacao", "recondicionado"),
            "encerrados": ("doado", "coletado", "vendido", "arquivado"),
        }
        if grupo not in grupos:
            raise FluxoItemError(400, "Grupo inválido")
        self._obter_pessoa(proprietario_id)
        itens = self._repositorio.listar_por_proprietario(
            proprietario_id, grupos[grupo], offset=offset, limite=limite
        )
        proprietarios = self._buscar_proprietarios(itens)
        return [
            self._resposta(item, proprietario=proprietarios.get(item.proprietario_id))
            for item in itens
        ]

    def buscar_por_id(self, item_id: str) -> ItemResponse:
        item = self._buscar_item(item_id)
        return self._resposta(item)

    def atualizar(
        self,
        item_id: str,
        request: ItemUpdateRequest,
        *,
        proprietario_id: str,
    ) -> ItemResponse:
        item = self._buscar_item(item_id)
        proprietario = self._obter_pessoa(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()

        instante = self._relogio()
        status_anterior = item.status
        novo_status = request.status
        if (self._reservas_por_interesse and item.destino == "doacao"
                and novo_status == "reservado" and status_anterior != "reservado"):
            # A reserva é efeito do aceite, nunca de um PUT isolado.
            raise ConflitoEstadoError()
        if item.status in STATUS_CONCLUIDOS:
            if (novo_status is not None and novo_status != item.status) or (
                request.destino != item.destino
            ):
                raise TransicaoInvalidaError(item.status, novo_status or request.destino)
        if novo_status in ("rascunho", "arquivado"):
            raise FluxoItemError(
                400, "Publicação e arquivamento usam os comandos próprios do item"
            )
        if request.destino != item.destino:
            if status_anterior != "rascunho":
                raise FluxoItemError(
                    400, "Modalidade só pode mudar enquanto o item é rascunho"
                )
            if novo_status not in (None, status_anterior):
                raise FluxoItemError(
                    400, "Altere a modalidade antes de publicar o item"
                )

        transicao = novo_status is not None and novo_status != status_anterior
        if transicao:
            self._validar_transicao(item.destino, status_anterior, novo_status)
        referencias = self._preparar_fluxo(
            item,
            request,
            alvo=novo_status if transicao else None,
        )

        ItemMapper.atualizar_modelo(request, item, instante=instante)
        item.ponto_coleta_id = referencias["ponto_coleta_id"]
        item.comprador_id = referencias["comprador_id"]
        if referencias["beneficiario_id"] is not None:
            item.beneficiario_id = referencias["beneficiario_id"]

        if transicao:
            ItemMapper.registrar_transicao(
                item,
                novo_status=novo_status,
                responsavel_id=proprietario_id,
                instante=instante,
                observacao=request.observacao,
            )

        evento = (
            self._evento_notificacao(item, novo_status, instante) if transicao else None
        )
        atualizado = self._repositorio.atualizar(
            item,
            status_esperado=status_anterior,
            notificacao=evento,
        )
        return self._resposta(atualizado, proprietario)

    @staticmethod
    def _evento_notificacao(
        item: Item,
        novo_status: str,
        instante: datetime,
    ) -> EventoNotificacao:
        return evento_de_status_item(
            item.id or "",
            item.titulo,
            novo_status,
            instante,
            concluido=novo_status in STATUS_CONCLUIDOS,
        )

    def excluir(self, item_id: str, *, proprietario_id: str) -> None:
        item = self._buscar_item(item_id)
        self._obter_pessoa(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()
        if item.status != "disponivel":
            # Excluir apagaria o histórico do fluxo e a referência que protege
            # beneficiário, comprador e ponto de coleta.
            raise FluxoItemError(
                409, "Item com fluxo iniciado não pode ser excluído"
            )
        self._repositorio.excluir(item_id)

    @staticmethod
    def _validar_transicao(destino: str, origem: str, alvo: str) -> None:
        permitidos = TRANSICOES.get(destino, {}).get(origem, set())
        if alvo not in permitidos:
            raise TransicaoInvalidaError(origem, alvo)

    def _preparar_fluxo(
        self,
        item: Item,
        request: ItemUpdateRequest,
        *,
        alvo: str | None,
    ) -> dict[str, str | None]:
        """Valida as referências do fluxo e devolve o que deve ser gravado."""
        if request.ponto_coleta_id is not None and item.destino != "descarte":
            raise FluxoItemError(
                400, "ponto_coleta_id só se aplica a itens de descarte"
            )
        if request.comprador_id is not None and item.destino != "revenda":
            raise FluxoItemError(400, "comprador_id só se aplica a itens de revenda")

        ponto = item.ponto_coleta_id
        if item.destino == "descarte":
            if item.ponto_coleta_id is not None:
                if request.ponto_coleta_id not in (None, item.ponto_coleta_id):
                    raise FluxoItemError(
                        409, "Ponto de coleta já definido para este item"
                    )
            elif alvo == "encaminhado":
                if request.ponto_coleta_id is None:
                    raise FluxoItemError(
                        400, "Encaminhamento exige ponto de coleta"
                    )
                # A categoria do próprio PUT é a que valerá após a gravação.
                self._garantir_ponto(request.ponto_coleta_id, request.categoria)
                ponto = request.ponto_coleta_id
            elif alvo == "coletado":
                raise FluxoItemError(
                    409, "Item sem ponto de coleta não pode ser coletado"
                )
            elif request.ponto_coleta_id is not None:
                raise FluxoItemError(
                    400, "Ponto de coleta só pode ser definido no encaminhamento"
                )

        comprador = item.comprador_id
        if item.destino == "revenda":
            if item.comprador_id is not None:
                if request.comprador_id not in (None, item.comprador_id):
                    raise FluxoItemError(
                        409, "Comprador já definido para este item"
                    )
            elif alvo == "vendido":
                if request.comprador_id is None:
                    raise FluxoItemError(400, "Conclusão da revenda exige comprador")
                self._validar_comprador(request.comprador_id, item.proprietario_id)
                comprador = request.comprador_id
            elif request.comprador_id is not None:
                raise FluxoItemError(
                    400, "Comprador só pode ser informado na conclusão da revenda"
                )

        beneficiario = None
        if alvo == "doado":
            beneficiario = (
                self._interesses.buscar_aceito_por_item(item.id or "")
                if self._interesses is not None
                else None
            )
            if beneficiario is None:
                raise FluxoItemError(409, "Doação exige interesse aceito")

        return {
            "ponto_coleta_id": ponto,
            "comprador_id": comprador,
            "beneficiario_id": beneficiario,
        }

    def _garantir_ponto(self, ponto_id: str, categoria: str) -> None:
        if self._pontos is None:
            raise FluxoItemError(400, "Ponto de coleta não pode ser validado")
        self._pontos.garantir_compatibilidade(ponto_id, categoria)

    def _validar_comprador(self, comprador_id: str, proprietario_id: str) -> None:
        if comprador_id == proprietario_id:
            raise FluxoItemError(400, "Comprador deve ser diferente do proprietário")
        comprador = self._repositorio_usuarios.buscar_por_id(comprador_id)
        if comprador is None:
            raise UsuarioNaoEncontradoError(comprador_id)
        if comprador.tipo != "pessoa":
            raise FluxoItemError(400, "Comprador deve ser uma pessoa cadastrada")

    def _buscar_item(self, item_id: str) -> Item:
        item = self._repositorio.buscar_por_id(item_id)
        if item is None:
            raise ItemNaoEncontradoError(item_id)
        return item

    def _obter_pessoa(self, usuario_id: str) -> Usuario:
        usuario = self._repositorio_usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoError(usuario_id)
        if usuario.tipo != "pessoa":
            raise ItemNaoAutorizadoError()
        return usuario

    def _resposta(self, item: Item, proprietario: Usuario | None = None) -> ItemResponse:
        proprietario = proprietario or self._repositorio_usuarios.buscar_por_id(item.proprietario_id)
        if proprietario is None:
            raise UsuarioNaoEncontradoError(item.proprietario_id)
        return ItemMapper.para_resposta(
            item,
            cidade_proprietario=proprietario.endereco.cidade,
        )

    def _buscar_proprietarios(self, itens: list[Item]) -> dict[str, Usuario]:
        ids = {item.proprietario_id for item in itens}
        buscar_por_ids = getattr(self._repositorio_usuarios, "buscar_por_ids", None)
        if callable(buscar_por_ids):
            return buscar_por_ids(ids)
        return {
            usuario_id: usuario
            for usuario_id in ids
            if (usuario := self._repositorio_usuarios.buscar_por_id(usuario_id)) is not None
        }
