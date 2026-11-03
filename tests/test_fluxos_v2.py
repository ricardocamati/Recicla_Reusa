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
async def test_doacao_conclui_com_beneficiario_do_interesse_aceito(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    interesses = RepositorioInteressesFake()
    async with cliente(app_para(repositorio_usuarios, repositorio_itens, interesses=interesses)) as api:
        await autenticar_doador(api)
        criado = (await api.post("/api/itens", json=payload_item())).json()
        reservado = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="reservado")
        )
        # A reserva é efeito do aceite; aqui ela é simulada no repositório para
        # isolar a conclusão. A sequência real está no teste de integração.
        repositorio_itens.itens[criado["id"]].status = "reservado"
        interesses.aceitos[criado["id"]] = "beneficiario-1"
        doado = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="doado")
        )

    assert reservado.status_code == 409, reservado.text
    assert doado.status_code == 200, doado.text
    resposta = doado.json()
    assert resposta["status"] == "doado"
    assert resposta["beneficiario_id"] == "beneficiario-1"
    assert [evento["status"] for evento in resposta["historico"]] == [
        "disponivel",
        "doado",
    ]


@pytest.mark.anyio
async def test_doacao_sem_interesse_aceito_nao_conclui(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(
        app_para(repositorio_usuarios, repositorio_itens, interesses=RepositorioInteressesFake())
    ) as api:
        await autenticar_doador(api)
        criado = (await api.post("/api/itens", json=payload_item())).json()
        repositorio_itens.itens[criado["id"]].status = "reservado"
        resposta = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="doado")
        )

    assert resposta.status_code == 409
    assert repositorio_itens.itens[criado["id"]].status == "reservado"


@pytest.mark.anyio
async def test_descarte_exige_ponto_compativel_e_preserva_referencia(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    pontos = RepositorioPontosFake(
        [
            ponto(["notebook"]),
            ponto(["celular"], ponto_id="ponto-2"),
        ]
    )
    async with cliente(app_para(repositorio_usuarios, repositorio_itens, pontos=pontos)) as api:
        await autenticar_doador(api)
        criado = (
            await api.post(
                "/api/itens",
                json=payload_item(destino="descarte", valor=None, categoria="notebook"),
            )
        ).json()
        sem_ponto = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="encaminhado")
        )
        inexistente = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="encaminhado", ponto_coleta_id="ponto-9"),
        )
        incompativel = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="encaminhado", ponto_coleta_id="ponto-2"),
        )
        encaminhado = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="encaminhado", ponto_coleta_id="ponto-1"),
        )
        troca = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="encaminhado", ponto_coleta_id="ponto-2"),
        )
        coletado = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="coletado")
        )

    assert sem_ponto.status_code == 400, sem_ponto.text
    assert inexistente.status_code == 404, inexistente.text
    assert incompativel.status_code == 400, incompativel.text
    assert encaminhado.status_code == 200, encaminhado.text
    assert encaminhado.json()["ponto_coleta_id"] == "ponto-1"
    assert troca.status_code == 409, troca.text
    assert coletado.status_code == 200, coletado.text
    assert coletado.json()["status"] == "coletado"
    assert coletado.json()["ponto_coleta_id"] == "ponto-1"
    assert [evento["status"] for evento in coletado.json()["historico"]] == [
        "disponivel",
        "encaminhado",
        "coletado",
    ]


@pytest.mark.anyio
async def test_revenda_conclui_com_comprador_e_valor(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        comprador = (
            await cadastrar_usuario(api, email="comprador@example.com", nome="Comprador")
        ).json()
        await autenticar_doador(api)
        criado = (
            await api.post(
                "/api/itens",
                json=payload_item(destino="revenda", valor=250.0, condicao="reparavel"),
            )
        ).json()
        avaliacao = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="em_avaliacao")
        )
        recondicionado = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="recondicionado", observacao="Laudo: placa substituída"),
        )
        sem_comprador = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="vendido")
        )
        antecipado = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="recondicionado", comprador_id="comprador-1"),
        )
        proprio_dono = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="vendido", comprador_id=criado["proprietario_id"]),
        )
        desconhecido = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="vendido", comprador_id="comprador-9"),
        )
        vendido = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="vendido", comprador_id=comprador["id"]),
        )
        segunda = await api.put(
            f"/api/itens/{criado['id']}", json=corpo(criado, status="recondicionado")
        )

    assert avaliacao.status_code == 200, avaliacao.text
    assert recondicionado.status_code == 200, recondicionado.text
    assert recondicionado.json()["historico"][-1]["observacao"] == "Laudo: placa substituída"
    assert sem_comprador.status_code == 400, sem_comprador.text
    assert "comprador" in sem_comprador.json()["detail"]
    assert antecipado.status_code == 400, antecipado.text
    assert "conclusão da revenda" in antecipado.json()["detail"]
    assert proprio_dono.status_code == 400, proprio_dono.text
    assert desconhecido.status_code == 404, desconhecido.text
    assert vendido.status_code == 200, vendido.text
    assert vendido.json()["status"] == "vendido"
    assert vendido.json()["comprador_id"] == comprador["id"]
    assert vendido.json()["valor"] == 250.0
    assert segunda.status_code == 400, segunda.text


@pytest.mark.anyio
async def test_campos_de_fluxo_incompativeis_com_o_destino(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await autenticar_doador(api)
        doacao = (await api.post("/api/itens", json=payload_item())).json()
        descarte = (
            await api.post("/api/itens", json=payload_item(destino="descarte", valor=None))
        ).json()
        ponto_em_doacao = await api.put(
            f"/api/itens/{doacao['id']}",
            json=corpo(doacao, ponto_coleta_id="ponto-1"),
        )
        comprador_em_descarte = await api.put(
            f"/api/itens/{descarte['id']}",
            json=corpo(descarte, comprador_id="comprador-1"),
        )

    assert ponto_em_doacao.status_code == 400, ponto_em_doacao.text
    assert "ponto_coleta_id" in ponto_em_doacao.json()["detail"]
    assert comprador_em_descarte.status_code == 400, comprador_em_descarte.text
    assert "comprador_id" in comprador_em_descarte.json()["detail"]


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
        await api.put(f"/api/itens/{criado['id']}", json=corpo(criado, status="em_avaliacao"))
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
        criado = (await api.post("/api/itens", json=payload_item())).json()
        corrigido = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, destino="revenda", valor=75.0),
        )

    assert corrigido.status_code == 200, corrigido.text
    assert corrigido.json()["destino"] == "revenda"
    assert corrigido.json()["status"] == "disponivel"


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
async def test_encaminhamento_valida_a_categoria_enviada_no_mesmo_put(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    pontos = RepositorioPontosFake([ponto(["celular"], ponto_id="ponto-celular")])
    async with cliente(app_para(repositorio_usuarios, repositorio_itens, pontos=pontos)) as api:
        await autenticar_doador(api)
        criado = (
            await api.post("/api/itens", json=payload_item(destino="descarte", valor=None))
        ).json()
        categoria_antiga = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="encaminhado", ponto_coleta_id="ponto-celular"),
        )
        recategorizado = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(
                criado,
                categoria="celular",
                status="encaminhado",
                ponto_coleta_id="ponto-celular",
            ),
        )

    assert categoria_antiga.status_code == 400, categoria_antiga.text
    assert recategorizado.status_code == 200, recategorizado.text
    assert recategorizado.json()["categoria"] == "celular"
    assert recategorizado.json()["ponto_coleta_id"] == "ponto-celular"


@pytest.mark.anyio
async def test_comprador_nao_pode_ser_conta_operacional(
    repositorio_usuarios: RepositorioEmMemoria,
    repositorio_itens: RepositorioItensEmMemoria,
) -> None:
    async with cliente(app_para(repositorio_usuarios, repositorio_itens)) as api:
        await cadastrar_usuario(api, email="comprador@example.com", nome="Comprador")
        await api.post("/api/auth/logout")
        await autenticar_doador(api)
        criado = (
            await api.post("/api/itens", json=payload_item(destino="revenda", valor=90.0))
        ).json()
        for status in ("em_avaliacao", "recondicionado"):
            await api.put(f"/api/itens/{criado['id']}", json=corpo(criado, status=status))
        operador_conta = replace(
            repositorio_usuarios.usuarios["1"], id="operador", tipo="ponto_coleta"
        )
        repositorio_usuarios.usuarios["operador"] = operador_conta
        operador = await api.put(
            f"/api/itens/{criado['id']}",
            json=corpo(criado, status="vendido", comprador_id="operador"),
        )

    assert operador.status_code == 400, operador.text
