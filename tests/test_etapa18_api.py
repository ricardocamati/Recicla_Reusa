"""Contrato enxuto da Etapa 18: descarte só como diretório."""
from dataclasses import fields

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import criar_app
from app.models.item import Item
from tests.test_fluxos_runtime import ambiente  # fixture com banco próprio e limpeza por UUID
from app.schemas.item import ItemCreateRequest, ItemUpdateRequest, ItemResponse


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.parametrize("modelo", [ItemCreateRequest, ItemUpdateRequest, ItemResponse])
def test_item_so_contem_modalidades_de_oferta_e_sem_campos_de_descarte(modelo):
    propriedades = modelo.model_json_schema()["properties"]
    assert set(propriedades["destino"]["enum"]) == {"doacao", "revenda"}
    assert not {"ponto_coleta_id", "destinacao_informada"} & propriedades.keys()


def test_modelo_persistido_nao_contem_vinculo_de_descarte():
    assert not {"ponto_coleta_id", "destinacao_informada"} & {campo.name for campo in fields(Item)}


def test_openapi_nao_mantem_rotas_schemas_ou_grupo_do_fluxo_removido():
    contrato = criar_app().openapi()
    assert not any("encaminhamentos" in p or "/destinacao" in p for p in contrato["paths"])
    assert not any("Encaminhamento" in n or "Destinacao" in n or "Compatibilidade" in n for n in contrato["components"]["schemas"])
    grupos = next(p for p in contrato["paths"]["/api/itens/meus"]["get"]["parameters"] if p["name"] == "grupo")
    assert "historico_descarte" not in str(grupos)
    assert set(ItemResponse.model_json_schema()["properties"]["status"]["enum"]) == {
        "rascunho", "disponivel", "reservado", "aguardando_confirmacao", "concluido", "arquivado",
    }


@pytest.mark.anyio
@pytest.mark.parametrize("metodo,caminho", [
    ("GET", "/api/encaminhamentos"),
    ("POST", "/api/encaminhamentos"),
    ("GET", "/api/encaminhamentos/000000000000000000000001"),
    ("POST", "/api/encaminhamentos/000000000000000000000001/acoes"),
    ("POST", "/api/itens/000000000000000000000001/destinacao"),
    ("DELETE", "/api/itens/000000000000000000000001/destinacao"),
])
async def test_rotas_retiradas_nao_possuem_handler_de_compatibilidade(metodo, caminho):
    async with AsyncClient(transport=ASGITransport(app=criar_app()), base_url="http://teste") as cliente:
        resposta = await cliente.request(metodo, caminho, headers={"Origin": "http://localhost:5500"})
    assert resposta.status_code == 404


def test_gestao_real_exige_papel_e_responsavel_antes_de_json_invalido(ambiente):
    from fastapi.testclient import TestClient
    from tests.test_fluxos_runtime import nova_conta, novo_operador, criar_ponto
    operador, _ = novo_operador(ambiente)
    outro, _ = novo_operador(ambiente, nome="outro-operador")
    pessoa, _, _ = nova_conta(ambiente, "pessoa")
    ponto = criar_ponto(operador, "Local próprio", ["notebook"])
    caminho = f"/api/pontos-coleta/{ponto['id']}"
    colecoes = ambiente.banco.list_collection_names()
    antes = {n: list(ambiente.banco[n].find().sort("_id")) for n in colecoes}
    with TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"}) as anonimo:
        resposta = anonimo.post("/api/pontos-coleta", content="{", headers={"Content-Type": "application/json"})
        assert resposta.status_code == 401
        assert resposta.headers["WWW-Authenticate"] == "Cookie"
    assert pessoa.post("/api/pontos-coleta", content="{", headers={"Content-Type": "application/json"}).status_code == 403
    assert operador.post("/api/itens", content="{", headers={"Content-Type": "application/json"}).status_code == 403
    assert outro.put(caminho, content="{", headers={"Content-Type": "application/json"}).status_code == 404
    assert pessoa.get(caminho + "?escopo=meus").status_code == 403
    assert outro.get(caminho + "?escopo=meus").status_code == 404
    assert antes == {n: list(ambiente.banco[n].find().sort("_id")) for n in colecoes}
    assert operador.post(caminho + "/situacao", json={"ativo": False}).status_code == 200
    assert pessoa.get(caminho).status_code == 404
    assert operador.get(caminho + "?escopo=meus").status_code == 200
    assert operador.delete(caminho).status_code == 204
    assert operador.get(caminho + "?escopo=meus").status_code == 404
