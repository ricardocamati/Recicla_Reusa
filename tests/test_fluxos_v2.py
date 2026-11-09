"""Fluxos de doação, descarte e revenda: contrato executável da Etapa 5."""
from datetime import UTC, datetime
from dataclasses import replace

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import criar_app
from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Endereco
from tests.test_api_item import (
    RepositorioItensEmMemoria,
    autenticar,
    cadastrar_usuario,
    payload_item,
)
from tests.test_api_usuario import RepositorioEmMemoria

ENDERECO = Endereco(
    logradouro="Rua das Flores",
    numero="100",
    complemento=None,
    cep="87010000",
    cidade="Maringá",
)


def ponto(categorias: list[str], ponto_id: str = "ponto-1") -> PontoColeta:
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    return PontoColeta(
        nome="Ponto Central",
        endereco=ENDERECO,
        categorias_aceitas=categorias,
        horario_atendimento="Segunda a sexta, 08:00-17:00",
        responsavel_id="operador-1",
        data_adicao=instante,
        data_modificacao=instante,
        id=ponto_id,
    )


class RepositorioPontosFake:
    def __init__(self, pontos: list[PontoColeta] | None = None) -> None:
        self.pontos = {ponto.id: ponto for ponto in (pontos or [])}

    def buscar_por_id(self, ponto_id: str) -> PontoColeta | None:
        return self.pontos.get(ponto_id)

    def criar(self, ponto: PontoColeta) -> PontoColeta:  # pragma: no cover - não usado
        self.pontos[ponto.id] = ponto
        return ponto

    def listar(self, **_: object) -> list[PontoColeta]:  # pragma: no cover
        return list(self.pontos.values())

    def atualizar(self, ponto: PontoColeta, *, responsavel_id: str) -> bool:  # pragma: no cover
        return False

    def excluir(self, ponto_id: str, *, responsavel_id: str) -> bool:  # pragma: no cover
        return False

    def contar_por_responsavel(self, responsavel_id: str) -> int:  # pragma: no cover
        return 0


class RepositorioInteressesFake:
    """Somente a leitura usada pela conclusão da doação."""

    def __init__(self, aceitos: dict[str, str] | None = None) -> None:
        self.aceitos = aceitos or {}

    def buscar_aceito_por_item(self, item_id: str) -> str | None:
        return self.aceitos.get(item_id)


def corpo(item: dict, **alteracoes: object) -> dict:
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


def app_para(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
    *,
    interesses: RepositorioInteressesFake | None = None,
    pontos: RepositorioPontosFake | None = None,
):
    relogio = lambda: datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    return criar_app(
        repositorio_usuarios,
        repositorio_itens=repositorio_itens,
        repositorio_pontos=pontos,
        repositorio_interesses=interesses,
        relogio=relogio,
    )


def cliente(app) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Origin": "http://localhost:5500"},
    )


@pytest.fixture
def repositorio_usuarios() -> RepositorioEmMemoria:
    return RepositorioEmMemoria()


@pytest.fixture
def repositorio_itens() -> RepositorioItensEmMemoria:
    return RepositorioItensEmMemoria()


async def autenticar_doador(api: AsyncClient) -> None:
    await cadastrar_usuario(api)
    await autenticar(api, "maria@example.com")


@pytest.mark.anyio
async def test_novo_descarte_e_rejeitado_sem_criar_item(repositorio_usuarios, repositorio_itens):
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        for publicar in (True, False):
            rejeitado = await api.post("/api/itens", json=payload_item(destino="descarte", valor=None, publicar=publicar))
            assert rejeitado.status_code == 400, rejeitado.text
            assert any(e["loc"][-1] == "destino" for e in rejeitado.json()["detail"])
        assert not repositorio_itens.itens
        oferta = await api.post("/api/itens", json=payload_item())
        assert oferta.status_code == 201 and oferta.json()["destino"] == "doacao"

@pytest.mark.anyio
async def test_campos_de_fluxo_incompativeis_com_doacao(repositorio_usuarios, repositorio_itens):
    from copy import deepcopy
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        doacao = (await api.post("/api/itens", json=payload_item())).json()
        antes = deepcopy(repositorio_itens.itens)
        ponto_em_doacao = await api.put(f"/api/itens/{doacao['id']}", json=corpo(doacao, ponto_coleta_id="ponto-1"))
        comprador_em_doacao = await api.put(f"/api/itens/{doacao['id']}", json=corpo(doacao, comprador_id="comprador-1"))
        assert ponto_em_doacao.status_code == 400 and any(e["type"] == "extra_forbidden" and e["loc"][-1] == "ponto_coleta_id" for e in ponto_em_doacao.json()["detail"])
        assert comprador_em_doacao.status_code == 400 and "comprador" in comprador_em_doacao.json()["detail"]
        assert repositorio_itens.itens == antes

@pytest.mark.anyio
async def test_destino_nao_muda_depois_de_iniciado_o_fluxo(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        criado = (
            await api.post("/api/itens", json=payload_item(destino="revenda", valor=100.0))
        ).json()
        troca = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, destino="doacao", valor=None)
        )

    assert troca.status_code == 400, troca.text


@pytest.mark.anyio
async def test_destino_e_status_nao_mudam_na_mesma_atualizacao(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        criado = (await api.post("/api/itens", json=payload_item())).json()
        combinado = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, destino="revenda", valor=10.0, status="em_avaliacao"),
        )

    assert combinado.status_code == 400, combinado.text
    assert repositorio_itens.itens[criado["id"]].destino == "doacao"


@pytest.mark.anyio
async def test_destino_pode_ser_corrigido_antes_do_fluxo(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        criado = (await api.post("/api/itens", json=payload_item(publicar=False))).json()
        corrigido = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, destino="revenda", valor=75.0),
        )
        publicado = await api.post(f"/api/itens/{criado['id']}/publicar")

    assert corrigido.status_code == 200, corrigido.text
    assert corrigido.json()["destino"] == "revenda"
    assert corrigido.json()["status"] == "rascunho"
    assert publicado.status_code == 200, publicado.text
    assert publicado.json()["status"] == "disponivel"


@pytest.mark.anyio
async def test_item_com_fluxo_iniciado_nao_pode_ser_excluido(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        livre = (await api.post("/api/itens", json=payload_item())).json()
        em_fluxo = (await api.post("/api/itens", json=payload_item())).json()
        await api.put(
            f"/api/itens/{em_fluxo['id']}", json=corpo(em_fluxo, status="reservado")
        )
        remover_livre = await api.delete(f"/api/itens/{livre['id']}")
        remover_em_fluxo = await api.delete(f"/api/itens/{em_fluxo['id']}")

    assert remover_livre.status_code == 204, remover_livre.text
    assert remover_em_fluxo.status_code == 409, remover_em_fluxo.text
    assert "fluxo" in remover_em_fluxo.json()["detail"]
    assert em_fluxo["id"] in repositorio_itens.itens


@pytest.mark.anyio
async def test_rascunho_oferta_permite_categoria_mas_nao_vinculo_de_descarte(repositorio_usuarios, repositorio_itens):
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        criado = (await api.post("/api/itens", json=payload_item(publicar=False))).json()
        recategorizado = await api.put(f"/api/itens/{criado['id']}", json=corpo(criado, categoria="celular"))
        assert recategorizado.status_code == 200, recategorizado.text
        assert recategorizado.json()["categoria"] == "celular" and recategorizado.json()["status"] == "rascunho"
        com_ponto = await api.put(f"/api/itens/{criado['id']}", json=corpo(recategorizado.json(), ponto_coleta_id="ponto-celular"))
        assert com_ponto.status_code == 400 and any(e["type"] == "extra_forbidden" and e["loc"][-1] == "ponto_coleta_id" for e in com_ponto.json()["detail"])
        assert not hasattr(repositorio_itens.itens[criado["id"]], "ponto_coleta_id")
