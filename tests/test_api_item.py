from datetime import UTC, datetime
from collections.abc import Callable
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import criar_app
from app.models.item import Item
from tests.test_api_usuario import RepositorioEmMemoria, payload as payload_usuario


class RepositorioItensEmMemoria:
    def __init__(self) -> None:
        self.itens: dict[str, Item] = {}
        self.proximo_id = 1

    def criar(self, item: Item) -> Item:
        item.id = f"item-{self.proximo_id}"
        self.proximo_id += 1
        self.itens[item.id] = item
        return item

    def listar(self, filtros) -> list[Item]:
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


@pytest.fixture
def repositorio_usuarios() -> RepositorioEmMemoria:
    return RepositorioEmMemoria()


@pytest.fixture
def repositorio_itens() -> RepositorioItensEmMemoria:
    return RepositorioItensEmMemoria()


@pytest.fixture
def instante() -> datetime:
    return datetime(2026, 9, 8, 12, 0, tzinfo=UTC)


def cliente(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime | Callable[[], datetime],
) -> AsyncClient:
    relogio = instante if callable(instante) else lambda: instante
    return AsyncClient(
        transport=ASGITransport(
            app=criar_app(
                repositorio_usuarios,
                repositorio_itens=repositorio_itens,
                relogio=relogio,
            ),
        ),
        base_url="http://testserver",
        headers={"Origin": "http://localhost:5500"},
    )


def payload_item(**alteracoes: Any) -> dict[str, Any]:
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
    return dados


async def cadastrar_usuario(api: AsyncClient, **alteracoes: Any):
    dados = payload_usuario(**alteracoes)
    return await api.post("/api/usuarios", json=dados)


async def autenticar(api: AsyncClient, email: str, senha: str = "Senha123"):
    return await api.post("/api/auth/login", json={"email": email, "senha": senha})


@pytest.mark.anyio
async def test_doador_cadastra_item_com_proprietario_da_sessao(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        usuario = await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        resposta = await api.post(
            "/api/itens",
            json=payload_item(proprietario_id="adulterado", data_adicao="2030-01-01T00:00:00Z"),
        )

    assert usuario.status_code == 201
    assert resposta.status_code == 400


@pytest.mark.anyio
async def test_doador_cadastra_item_valido_e_nao_duplica_endereco(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        usuario = await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        resposta = await api.post("/api/itens", json=payload_item(categoria="Informática"))

    assert usuario.status_code == 201
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["proprietario_id"] == usuario.json()["id"]
    assert corpo["status"] == "disponivel"
    assert corpo["cidade_proprietario"] == "Maringá"
    assert "endereco" not in corpo
    assert "Location" in resposta.headers


@pytest.mark.anyio
async def test_beneficiario_nao_pode_cadastrar_item(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        await cadastrar_usuario(api, email="beneficiario@example.com", tipo="beneficiario")
        await autenticar(api, "beneficiario@example.com")
        resposta = await api.post("/api/itens", json=payload_item())

    assert resposta.status_code == 403
    assert repositorio_itens.itens == {}


@pytest.mark.anyio
async def test_ponto_coleta_consulta_mas_nao_cadastra_item(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        cadastro = await cadastrar_usuario(
            api,
            email="ponto@example.com",
            tipo="beneficiario",
        )
        usuario = repositorio_usuarios.usuarios[cadastro.json()["id"]]
        usuario.tipo = "ponto_coleta"
        await autenticar(api, "ponto@example.com")
        catalogo = await api.get("/api/itens")
        criacao = await api.post("/api/itens", json=payload_item())

    assert catalogo.status_code == 200
    assert criacao.status_code == 403


@pytest.mark.anyio
async def test_listar_filtra_itens_por_categoria_destino_e_status(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        await api.post("/api/itens", json=payload_item())
        segundo = await api.post(
            "/api/itens",
            json=payload_item(categoria="telefonia", condicao="reparavel", destino="revenda", valor=100),
        )
        repositorio_itens.itens[segundo.json()["id"]].status = "doado"
        resposta = await api.get(
            "/api/itens",
            params={
                "categoria": "telefonia",
                "condicao": "reparavel",
                "destino": "revenda",
                "status": "doado",
            },
        )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["categoria"] == "telefonia"


@pytest.mark.anyio
async def test_catalogo_exige_sessao_e_item_invalido_retorna_404(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        sem_sessao = await api.get("/api/itens")
        criacao_sem_sessao = await api.post("/api/itens", json=payload_item())
        await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        invalido = await api.get("/api/itens/abc")

    assert sem_sessao.status_code == 401
    assert criacao_sem_sessao.status_code == 401
    assert invalido.status_code == 404


@pytest.mark.anyio
async def test_atualizar_e_excluir_item_exigem_o_proprietario(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        primeiro = await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        criado = await api.post("/api/itens", json=payload_item())
        await api.post("/api/auth/logout")
        await cadastrar_usuario(api, email="joao@example.com", nome="João da Silva")
        await autenticar(api, "joao@example.com")
        item_id = criado.json()["id"]
        atualizacao = await api.put(
            f"/api/itens/{item_id}",
            json=payload_item(titulo="Alteração indevida"),
        )
        exclusao = await api.delete(f"/api/itens/{item_id}")
        await api.post("/api/auth/logout")
        await autenticar(api, "maria@example.com")
        proprio = await api.put(
            f"/api/itens/{item_id}",
            json=payload_item(titulo="Notebook atualizado"),
        )
        removido = await api.delete(f"/api/itens/{item_id}")

    assert primeiro.status_code == 201
    assert atualizacao.status_code == 403
    assert exclusao.status_code == 403
    assert proprio.status_code == 200
    assert removido.status_code == 204


@pytest.mark.anyio
async def test_validacao_de_enums_e_valor_de_revenda(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        condicao_invalida = await api.post("/api/itens", json=payload_item(condicao="novo"))
        destino_invalido = await api.post("/api/itens", json=payload_item(destino="troca"))
        sem_valor = await api.post("/api/itens", json=payload_item(destino="revenda", valor=None))
        valor_negativo = await api.post("/api/itens", json=payload_item(destino="revenda", valor=-0.01))
        revenda_zero = await api.post("/api/itens", json=payload_item(destino="revenda", valor=0))
        doacao_com_valor = await api.post("/api/itens", json=payload_item(destino="doacao", valor=100))

    assert condicao_invalida.status_code == 400
    assert destino_invalido.status_code == 400
    assert sem_valor.status_code == 400
    assert valor_negativo.status_code == 400
    assert revenda_zero.status_code == 201
    assert doacao_com_valor.status_code == 400
