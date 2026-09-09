from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.exceptions import ItemNaoAutorizadoError, ItemNaoEncontradoError, UsuarioNaoEncontradoError
from app.models.item import Item
from app.models.usuario import Endereco, Usuario
from app.schemas.item import FiltrosItem, ItemCreateRequest, ItemUpdateRequest
from app.services.item_service import ItemService


class RepositorioItensFake:
    def __init__(self) -> None:
        self.itens: dict[str, Item] = {}
        self.proximo_id = 1

    def criar(self, item: Item) -> Item:
        item.id = f"item-{self.proximo_id}"
        self.proximo_id += 1
        self.itens[item.id] = item
        return item

    def listar(self, filtros: FiltrosItem) -> list[Item]:
        return [
            item
            for item in self.itens.values()
            if (filtros.categoria is None or item.categoria == filtros.categoria)
            and (filtros.condicao is None or item.condicao == filtros.condicao)
            and (filtros.destino is None or item.destino == filtros.destino)
            and (filtros.status is None or item.status == filtros.status)
        ]

    def buscar_por_id(self, item_id: str) -> Item | None:
        return self.itens.get(item_id)

    def atualizar(self, item: Item) -> Item:
        self.itens[item.id or ""] = item
        return item

    def excluir(self, item_id: str) -> None:
        self.itens.pop(item_id, None)


class RepositorioUsuariosFake:
    def __init__(self, usuarios: list[Usuario] | None = None) -> None:
        self.usuarios = {usuario.id: usuario for usuario in usuarios or [] if usuario.id}
        self.chamadas_em_lote = 0

    def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        return self.usuarios.get(usuario_id)

    def buscar_por_ids(self, usuario_ids: set[str]) -> dict[str, Usuario]:
        self.chamadas_em_lote += 1
        return {
            usuario_id: self.usuarios[usuario_id]
            for usuario_id in usuario_ids
            if usuario_id in self.usuarios
        }


def usuario_doador(usuario_id: str = "u1") -> Usuario:
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    return Usuario(
        id=usuario_id,
        nome="Maria",
        email=f"{usuario_id}@example.com",
        tipo="doador",
        endereco=Endereco(
            logradouro="Rua A",
            numero="10",
            cep="87000000",
            cidade="Maringá",
            complemento=None,
        ),
        senha_hash="hash",
        data_adicao=instante,
        data_modificacao=instante,
    )


def request(**alteracoes) -> ItemCreateRequest:
    dados = {
        "titulo": "Notebook usado",
        "descricao": "Funcionando com bateria fraca",
        "categoria": "informatica",
        "marca": "Dell",
        "modelo": "Inspiron 15",
        "condicao": "funcional",
        "destino": "doacao",
        "valor": None,
    }
    dados.update(alteracoes)
    return ItemCreateRequest(**dados)


def update_request(**alteracoes) -> ItemUpdateRequest:
    dados = request().model_dump()
    dados.pop("valor")
    dados.update(alteracoes)
    return ItemUpdateRequest(**dados)


def service(
    itens: RepositorioItensFake,
    usuarios: RepositorioUsuariosFake,
    relogio,
) -> ItemService:
    return ItemService(itens, usuarios, relogio=relogio)


def test_criar_item_define_proprietario_status_e_auditoria() -> None:
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    itens = RepositorioItensFake()
    servico = service(itens, RepositorioUsuariosFake([usuario_doador()]), lambda: instante)

    resposta = servico.criar(request(valor=None), proprietario_id="u1")

    assert resposta.id == "item-1"
    assert resposta.proprietario_id == "u1"
    assert resposta.status == "disponivel"
    assert resposta.data_adicao == instante
    assert resposta.data_modificacao == instante
    assert resposta.cidade_proprietario == "Maringá"
    assert not hasattr(itens.itens["item-1"], "endereco")


def test_criar_item_rejeita_proprietario_inexistente() -> None:
    servico = service(RepositorioItensFake(), RepositorioUsuariosFake(), datetime.now)

    with pytest.raises(UsuarioNaoEncontradoError):
        servico.criar(request(), proprietario_id="ausente")


def test_listar_aplica_filtros_combinados() -> None:
    itens = RepositorioItensFake()
    usuarios = RepositorioUsuariosFake([usuario_doador()])
    servico = service(itens, usuarios, datetime.now)
    servico.criar(request(), proprietario_id="u1")
    servico.criar(
        request(categoria="telefonia", condicao="reparavel", destino="revenda", valor=Decimal("100")),
        proprietario_id="u1",
    )

    respostas = servico.listar(FiltrosItem(categoria="telefonia", destino="revenda"))

    assert len(respostas) == 1
    assert respostas[0].categoria == "telefonia"
    assert usuarios.chamadas_em_lote == 1


def test_atualizar_preserva_identidade_proprietario_e_data_adicao() -> None:
    instantes = iter(
        [
            datetime(2026, 9, 8, 12, 0, tzinfo=UTC),
            datetime(2026, 9, 8, 12, 5, tzinfo=UTC),
        ]
    )
    itens = RepositorioItensFake()
    servico = service(itens, RepositorioUsuariosFake([usuario_doador()]), lambda: next(instantes))
    criado = servico.criar(request(), proprietario_id="u1")

    resposta = servico.atualizar(
        criado.id,
        update_request(titulo="Notebook atualizado", condicao="funcional_com_defeito"),
        proprietario_id="u1",
    )

    assert resposta.id == criado.id
    assert resposta.proprietario_id == "u1"
    assert resposta.data_adicao == datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    assert resposta.data_modificacao == datetime(2026, 9, 8, 12, 5, tzinfo=UTC)
    assert resposta.titulo == "Notebook atualizado"


def test_atualizar_item_inexistente_gera_erro() -> None:
    servico = service(RepositorioItensFake(), RepositorioUsuariosFake([usuario_doador()]), datetime.now)

    with pytest.raises(ItemNaoEncontradoError):
        servico.atualizar("ausente", update_request(), proprietario_id="u1")


def test_proprietario_diferente_nao_altera_ou_exclui_item() -> None:
    itens = RepositorioItensFake()
    usuarios = RepositorioUsuariosFake([usuario_doador("u1"), usuario_doador("u2")])
    servico = service(itens, usuarios, datetime.now)
    criado = servico.criar(request(), proprietario_id="u1")

    with pytest.raises(ItemNaoAutorizadoError):
        servico.atualizar(criado.id, update_request(), proprietario_id="u2")
    with pytest.raises(ItemNaoAutorizadoError):
        servico.excluir(criado.id, proprietario_id="u2")
