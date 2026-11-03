from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.interesses import criar_router_interesses
from app.schemas.interesse import InteresseResponse
from app.security.sessions import ArmazenamentoDeSessoes, SESSION_COOKIE_NAME
from app.exceptions import InteresseError
from app.services.interesse_service import InteresseService


class ServicoInteressesFake:
    def __init__(self):
        self.criados = []

    def criar(self, dados, usuario_id):
        self.criados.append((dados.item_id, usuario_id))
        agora = datetime(2026, 10, 1, tzinfo=UTC)
        return InteresseResponse(
            id="interesse-1",
            item_id=dados.item_id,
            usuario_id=usuario_id,
            status="pendente",
            data_adicao=agora,
            data_modificacao=agora,
        )


@pytest.mark.anyio
async def test_post_interesse_autenticado_retorna_201_e_nao_aceita_identidade_do_payload():
    sessoes = ArmazenamentoDeSessoes()
    token = sessoes.criar("beneficiario-1", "beneficiario")
    servico = ServicoInteressesFake()
    app = FastAPI()
    app.include_router(criar_router_interesses(servico, sessoes))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        sem_sessao = await api.post("/api/interesses", json={"item_id": "item-1"})
        api.cookies.set(SESSION_COOKIE_NAME, token)
        resposta = await api.post(
            "/api/interesses",
            json={"item_id": "item-1", "usuario_id": "terceiro"},
        )

    assert sem_sessao.status_code == 401
    assert resposta.status_code == 400
    assert servico.criados == []


@pytest.mark.anyio
async def test_post_interesse_cria_vinculo_para_identidade_da_sessao():
    sessoes = ArmazenamentoDeSessoes()
    token = sessoes.criar("beneficiario-1", "beneficiario")
    servico = ServicoInteressesFake()
    app = FastAPI()
    app.include_router(criar_router_interesses(servico, sessoes))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", cookies={SESSION_COOKIE_NAME: token}) as api:
        resposta = await api.post(
            "/api/interesses",
            json={"item_id": "item-1"},
        )

    assert resposta.status_code == 201
    assert resposta.json()["usuario_id"] == "beneficiario-1"
    assert resposta.headers["location"] == "/api/interesses/interesse-1"
    assert servico.criados == [("item-1", "beneficiario-1")]


class RepositorioServicoFake:
    def __init__(self, *, destino="doacao", proprietario_id="doador-1"):
        self.usuario = {"tipo": "beneficiario"}
        self.item = {"proprietario_id": proprietario_id, "destino": destino, "status": "disponivel"}
        self.criados = []

    def buscar_usuario(self, usuario_id):
        return self.usuario

    def buscar_item(self, item_id):
        return self.item

    def criar(self, interesse):
        interesse.id = "interesse-2"
        self.criados.append(interesse)
        return interesse


def test_service_cria_interesse_pendente_com_timestamps_utc():
    agora = datetime(2026, 10, 1, 12, 0, 0, 123456, tzinfo=UTC)
    repo = RepositorioServicoFake()
    service = InteresseService(repo, relogio=lambda: agora)

    response = service.criar({"item_id": "item-2"}, "beneficiario-2")

    assert response.status == "pendente"
    assert response.item_id == "item-2"
    assert response.usuario_id == "beneficiario-2"
    assert response.data_adicao == agora
    assert repo.criados[0].data_modificacao == agora


@pytest.mark.parametrize(
    ("proprietario_id", "destino", "status_code"),
    [("beneficiario-2", "doacao", 400), ("doador-1", "descarte", 400), ("doador-1", "doacao", 409)],
)
def test_service_rejeita_interesse_proprio_descarte_ou_indisponivel(proprietario_id, destino, status_code):
    repo = RepositorioServicoFake(destino=destino, proprietario_id=proprietario_id)
    if status_code == 409:
        repo.item["status"] = "reservado"
    service = InteresseService(repo)

    with pytest.raises(InteresseError) as erro:
        service.criar({"item_id": "item-2"}, "beneficiario-2")

    assert erro.value.status_code == status_code
    assert repo.criados == []


@pytest.mark.anyio
async def test_autenticacao_acontece_antes_da_validacao_do_json():
    sessoes = ArmazenamentoDeSessoes()
    token = sessoes.criar("beneficiario-1", "beneficiario")
    servico = ServicoInteressesFake()
    app = FastAPI()
    app.include_router(criar_router_interesses(servico, sessoes))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        anonimo = await api.post("/api/interesses", content="{", headers={"Content-Type": "application/json"})
        api.cookies.set(SESSION_COOKIE_NAME, token)
        autenticado = await api.post("/api/interesses", content="{", headers={"Content-Type": "application/json"})

    assert anonimo.status_code == 401
    assert anonimo.headers["www-authenticate"] == "Cookie"
    assert autenticado.status_code == 400
    assert servico.criados == []
