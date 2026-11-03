from dataclasses import replace
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

    def _copiar(self, item: Item) -> Item:
        return replace(item, historico=list(item.historico))

    def criar(self, item: Item) -> Item:
        item.id = f"item-{self.proximo_id}"
        self.proximo_id += 1
        self.itens[item.id] = self._copiar(item)
        return item

    def listar(
        self,
        filtros,
        *,
        proprietario_ids: set[str] | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[Item]:
        itens = [
            item
            for item in self.itens.values()
            if (filtros.categoria is None or item.categoria == filtros.categoria)
            and (filtros.condicao is None or item.condicao == filtros.condicao)
            and (filtros.destino is None or item.destino == filtros.destino)
            and (filtros.status is None or item.status == filtros.status)
            and (proprietario_ids is None or item.proprietario_id in proprietario_ids)
        ]
        return itens[offset : offset + limite]

    def buscar_por_id(self, item_id: str) -> Item | None:
        encontrado = self.itens.get(item_id)
        return self._copiar(encontrado) if encontrado else None

    def atualizar(self, item: Item, *, status_esperado: str | None = None) -> Item:
        atual = self.itens.get(item.id or "")
        if status_esperado is not None and (atual is None or atual.status != status_esperado):
            from app.exceptions import ConflitoEstadoError

            raise ConflitoEstadoError()
        self.itens[item.id or ""] = self._copiar(item)
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


def corpo_atualizacao(item: dict[str, Any], **alteracoes: Any) -> dict[str, Any]:
    campos = (
        "titulo",
        "descricao",
        "categoria",
        "marca",
        "modelo",
        "condicao",
        "destino",
        "valor",
        "especificacoes",
    )
    dados = {campo: item[campo] for campo in campos}
    dados.update(alteracoes)
    return dados


@pytest.mark.anyio
async def test_cadastro_registra_primeiro_evento_e_nao_copia_endereco(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        criado = await api.post(
            "/api/itens",
            json=payload_item(especificacoes={"memoria_ram": "8 GB", "tela": "14"}),
        )
        listado = await api.get("/api/itens")

    assert criado.status_code == 201
    corpo = criado.json()
    assert corpo["status"] == "disponivel"
    assert corpo["especificacoes"] == {"memoria_ram": "8 GB", "tela": "14"}
    assert len(corpo["historico"]) == 1
    evento = corpo["historico"][0]
    assert evento["etapa"] == "cadastro"
    assert evento["status"] == "disponivel"
    assert evento["responsavel_id"] == corpo["proprietario_id"]
    assert evento["data_evento"] == corpo["data_adicao"]
    for proibido in ("logradouro", "numero", "complemento", "cep", "endereco"):
        assert proibido not in corpo
        assert proibido not in listado.json()[0]
    assert listado.json()[0]["cidade_proprietario"] == "Maringá"


@pytest.mark.anyio
async def test_transicoes_validas_acumulam_historico(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        criado = (
            await api.post("/api/itens", json=payload_item(destino="revenda", valor=100.0))
        ).json()
        avaliacao = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="em_avaliacao"),
        )
        recondicionado = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="recondicionado"),
        )

    assert avaliacao.status_code == 200
    assert [evento["status"] for evento in avaliacao.json()["historico"]] == [
        "disponivel",
        "em_avaliacao",
    ]
    assert recondicionado.status_code == 200
    historico = recondicionado.json()["historico"]
    assert [evento["status"] for evento in historico] == [
        "disponivel",
        "em_avaliacao",
        "recondicionado",
    ]
    assert historico[-1]["observacao"] == "em_avaliacao -> recondicionado"
    assert len({evento["data_evento"] for evento in historico}) == 1


@pytest.mark.anyio
async def test_salto_de_status_e_reabertura_sao_rejeitados(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        comprador = (
            await cadastrar_usuario(api, email="comprador@example.com", nome="Comprador")
        ).json()
        await cadastrar_usuario(api)
        await autenticar(api, "maria@example.com")
        criado = (
            await api.post("/api/itens", json=payload_item(destino="revenda", valor=100.0))
        ).json()
        salto = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="vendido"),
        )
        await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="em_avaliacao"),
        )
        await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="recondicionado"),
        )
        concluido = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="vendido", comprador_id=comprador["id"]),
        )
        reabrir = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, status="recondicionado"),
        )
        trocar_destino = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo_atualizacao(criado, destino="doacao", valor=None),
        )

    assert salto.status_code == 400
    assert concluido.status_code == 200
    assert reabrir.status_code == 400
    assert trocar_destino.status_code == 400
    assert len(repositorio_itens.itens[criado["id"]].historico) == 4


@pytest.mark.anyio
async def test_catalogo_filtra_por_cidade_e_pagina(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio_usuarios, repositorio_itens, instante) as api:
        await cadastrar_usuario(api, email="maria@example.com")
        await autenticar(api, "maria@example.com")
        for indice in range(3):
            await api.post("/api/itens", json=payload_item(titulo=f"Notebook {indice}"))
        await api.post("/api/auth/logout")

        await cadastrar_usuario(
            api,
            email="joao@example.com",
            nome="João da Silva",
            endereco={
                "logradouro": "Rua B",
                "numero": "20",
                "cep": "86000000",
                "cidade": "Londrina",
            },
        )
        await autenticar(api, "joao@example.com")
        await api.post("/api/itens", json=payload_item(titulo="Monitor de Londrina", categoria="monitor"))

        maringa = await api.get("/api/itens", params={"cidade": "maringá"})
        primeira_pagina = await api.get("/api/itens", params={"cidade": "Maringá", "limite": 2})
        segunda_pagina = await api.get(
            "/api/itens", params={"cidade": "Maringá", "limite": 2, "offset": 2}
        )
        Londres = await api.get("/api/itens", params={"cidade": "Curitiba"})

    assert maringa.status_code == 200
    assert {item["cidade_proprietario"] for item in maringa.json()} == {"Maringá"}
    assert len(maringa.json()) == 3
    assert len(primeira_pagina.json()) == 2
    assert len(segunda_pagina.json()) == 1
    ids = {item["id"] for item in primeira_pagina.json()} & {
        item["id"] for item in segunda_pagina.json()
    }
    assert ids == set()
    assert Londres.json() == []
