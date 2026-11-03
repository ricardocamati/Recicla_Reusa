from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import (
    ItemNaoAutorizadoError,
    ItemNaoEncontradoError,
    TransicaoInvalidaError,
    UsuarioNaoEncontradoError,
)
from app.mappers.item_mapper import ItemMapper
from app.models.item import Item
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
    ) -> list[Item]: ...
    def buscar_por_id(self, item_id: str) -> Item | None: ...
    def atualizar(self, item: Item, *, status_esperado: str | None = None) -> Item: ...
    def excluir(self, item_id: str) -> None: ...


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
    ) -> None:
        self._repositorio = repositorio
        self._repositorio_usuarios = repositorio_usuarios
        self._relogio = relogio or (lambda: datetime.now(UTC))

    def criar(self, request: ItemCreateRequest, *, proprietario_id: str) -> ItemResponse:
        proprietario = self._obter_doador(proprietario_id)
        item = ItemMapper.para_modelo(
            request,
            proprietario_id=proprietario_id,
            instante=self._relogio(),
        )
        criado = self._repositorio.criar(item)
        return self._resposta(criado, proprietario)

    def listar(
        self,
        filtros: FiltrosItem,
        *,
        offset: int = 0,
        limite: int = 20,
    ) -> list[ItemResponse]:
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
        proprietario = self._obter_doador(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()

        instante = self._relogio()
        status_anterior = item.status
        novo_status = request.status
        if item.status in STATUS_CONCLUIDOS:
            if (novo_status is not None and novo_status != item.status) or (
                request.destino != item.destino
            ):
                raise TransicaoInvalidaError(item.status, novo_status or request.destino)

        ItemMapper.atualizar_modelo(request, item, instante=instante)

        transicao = novo_status is not None and novo_status != status_anterior
        if transicao:
            self._validar_transicao(item.destino, status_anterior, novo_status)
            ItemMapper.registrar_transicao(
                item,
                novo_status=novo_status,
                responsavel_id=proprietario_id,
                instante=instante,
            )

        atualizado = self._repositorio.atualizar(
            item,
            status_esperado=status_anterior if transicao else None,
        )
        return self._resposta(atualizado, proprietario)

    def excluir(self, item_id: str, *, proprietario_id: str) -> None:
        item = self._buscar_item(item_id)
        self._obter_doador(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()
        self._repositorio.excluir(item_id)

    @staticmethod
    def _validar_transicao(destino: str, origem: str, alvo: str) -> None:
        permitidos = TRANSICOES.get(destino, {}).get(origem, set())
        if alvo not in permitidos:
            raise TransicaoInvalidaError(origem, alvo)

    def _buscar_item(self, item_id: str) -> Item:
        item = self._repositorio.buscar_por_id(item_id)
        if item is None:
            raise ItemNaoEncontradoError(item_id)
        return item

    def _obter_doador(self, usuario_id: str) -> Usuario:
        usuario = self._repositorio_usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoError(usuario_id)
        if usuario.tipo != "doador":
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
