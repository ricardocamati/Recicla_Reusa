from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Protocol

from app.exceptions import ItemNaoEncontradoError, ItemNaoAutorizadoError, UsuarioNaoEncontradoError
from app.mappers.item_mapper import ItemMapper
from app.models.item import Item
from app.models.usuario import Usuario
from app.schemas.item import FiltrosItem, ItemCreateRequest, ItemResponse, ItemUpdateRequest


class RepositorioDeItens(Protocol):
    def criar(self, item: Item) -> Item: ...
    def listar(self, filtros: FiltrosItem) -> list[Item]: ...
    def buscar_por_id(self, item_id: str) -> Item | None: ...
    def atualizar(self, item: Item) -> Item: ...
    def excluir(self, item_id: str) -> None: ...


class RepositorioDeUsuariosParaItens(Protocol):
    def buscar_por_id(self, usuario_id: str) -> Usuario | None: ...
    def buscar_por_ids(self, usuario_ids: Iterable[str]) -> dict[str, Usuario]: ...


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

    def listar(self, filtros: FiltrosItem) -> list[ItemResponse]:
        itens = self._repositorio.listar(filtros)
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
        ItemMapper.atualizar_modelo(request, item, instante=self._relogio())
        atualizado = self._repositorio.atualizar(item)
        return self._resposta(atualizado, proprietario)

    def excluir(self, item_id: str, *, proprietario_id: str) -> None:
        item = self._buscar_item(item_id)
        self._obter_doador(proprietario_id)
        if item.proprietario_id != proprietario_id:
            raise ItemNaoAutorizadoError()
        self._repositorio.excluir(item_id)

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
