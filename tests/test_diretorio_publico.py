"""Contrato público do diretório, separado da gestão autenticada."""
from types import SimpleNamespace

import mongomock
import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.main import criar_app
from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Endereco
from app.repositories.mongo_ponto_coleta_repository import MongoPontoColetaRepository
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from tests.test_pontos_coleta_v2 import INSTANTE

PUBLICOS = {"id", "nome", "endereco", "categorias_aceitas", "horario_atendimento"}


@pytest.fixture
def diretorio():
    banco = mongomock.MongoClient(tz_aware=True).teste_diretorio
    usuarios = MongoUsuarioRepository(banco.usuarios, criar_indice=False)
    pontos = MongoPontoColetaRepository(banco.pontos_coleta, criar_indices=False)
    app = criar_app(usuarios, repositorio_pontos=pontos)
    return SimpleNamespace(banco=banco, pontos=pontos, app=app)


def adicionar_local(ambiente, nome="Ponto público", *, ativo=True, cidade="Maringá", categoria="notebook", responsavel=None):
    return ambiente.pontos.criar(PontoColeta(
        nome=nome,
        endereco=Endereco(logradouro="Rua do Local Público", numero="20", cep="87000000", cidade=cidade),
        categorias_aceitas=[categoria], horario_atendimento="Segunda a sexta",
        responsavel_id=responsavel or str(ObjectId()), ativo=ativo,
        data_adicao=INSTANTE, data_modificacao=INSTANTE,
    ))


@pytest.mark.anyio
async def test_visitante_lista_e_abre_detalhe_sem_cookie_com_projecao_publica(diretorio):
    ponto = adicionar_local(diretorio)
    async with AsyncClient(transport=ASGITransport(app=diretorio.app), base_url="http://teste") as api:
        lista = await api.get("/api/pontos-coleta")
        assert lista.status_code == 200, lista.text
        detalhe = await api.get(f"/api/pontos-coleta/{ponto.id}")
        assert detalhe.status_code == 200, detalhe.text
        assert len(lista.json()) == 1
        assert lista.json()[0] == detalhe.json()
        assert set(detalhe.json()) == PUBLICOS
        assert detalhe.json()["endereco"]["logradouro"] == "Rua do Local Público"
        assert "set-cookie" not in lista.headers and "set-cookie" not in detalhe.headers
        assert not api.cookies


@pytest.mark.anyio
async def test_publico_filtra_ativos_cidade_categoria_antes_de_paginar_com_desempate_por_id(diretorio):
    for i in range(105):
        adicionar_local(diretorio, f"Anterior {i:03}", cidade="Outra cidade")
    adicionar_local(diretorio, "Anterior inativo", ativo=False)
    adicionar_local(diretorio, "Anterior incompatível", categoria="monitor")
    maiores = [ObjectId("000000000000000000000003"), ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]
    for oid in maiores:
        local = adicionar_local(diretorio, "Mesmo nome")
        doc = diretorio.banco.pontos_coleta.find_one_and_delete({"_id": ObjectId(local.id)})
        doc["_id"] = oid
        diretorio.banco.pontos_coleta.insert_one(doc)
    async with AsyncClient(transport=ASGITransport(app=diretorio.app), base_url="http://teste") as api:
        pagina = await api.get("/api/pontos-coleta", params={"cidade": "  mArInGá  ", "categoria": "notebook", "offset": 1, "limite": 1})
        assert pagina.status_code == 200, pagina.text
        assert [p["id"] for p in pagina.json()] == ["000000000000000000000002"]
        completa = await api.get("/api/pontos-coleta", params={"cidade": "Maringá", "categoria": "notebook"})
        assert [p["id"] for p in completa.json()] == [str(x) for x in sorted(maiores)]


@pytest.mark.anyio
async def test_detalhe_publico_oculta_inativo_e_preserva_ausencia_de_ativo_no_legado(diretorio):
    inativo = adicionar_local(diretorio, ativo=False)
    legado = adicionar_local(diretorio, "Local sem campo ativo")
    diretorio.banco.pontos_coleta.update_one({"_id": ObjectId(legado.id)}, {"$unset": {"ativo": ""}})
    async with AsyncClient(transport=ASGITransport(app=diretorio.app), base_url="http://teste") as api:
        for identificador in [inativo.id, str(ObjectId()), "identificador-invalido"]:
            resposta = await api.get(f"/api/pontos-coleta/{identificador}")
            assert resposta.status_code == 404, resposta.text
            assert resposta.json() == {"detail": "Ponto de coleta não encontrado"}
        assert (await api.get(f"/api/pontos-coleta/{legado.id}")).status_code == 200
        lista = (await api.get("/api/pontos-coleta")).json()
        assert [p["id"] for p in lista] == [legado.id]
    assert "ativo" not in diretorio.banco.pontos_coleta.find_one({"_id": ObjectId(legado.id)})


@pytest.mark.anyio
@pytest.mark.parametrize("query", ["ativo=false", "responsavel_id=outro", "item_id=abc", "id_operacao=abc", "escopo=qualquer", "cidade=A&cidade=B"])
async def test_consulta_publica_rejeita_parametros_extras_e_repetidos(diretorio, query):
    ponto = adicionar_local(diretorio)
    async with AsyncClient(transport=ASGITransport(app=diretorio.app), base_url="http://teste") as api:
        for rota in ["/api/pontos-coleta", f"/api/pontos-coleta/{ponto.id}"]:
            resposta = await api.get(rota + "?" + query)
            assert resposta.status_code == 400, resposta.text
            assert "detail" in resposta.json()
        assert (await api.get("/api/pontos-coleta?categoria=notebook")).status_code == 200


@pytest.mark.anyio
async def test_escopo_de_gestao_exige_operador_e_expoe_apenas_seus_locais(diretorio):
    from tests.test_pontos_coleta_v2 import usuario
    usuarios = MongoUsuarioRepository(diretorio.banco.usuarios, criar_indice=False)
    dono = usuarios.criar(usuario("dono-local@example.test", "ponto_coleta"))
    outro = usuarios.criar(usuario("outro-local@example.test", "ponto_coleta"))
    usuarios.criar(usuario("pessoa-local@example.test", "pessoa"))
    proprio = adicionar_local(diretorio, ativo=False, responsavel=dono.id)
    adicionar_local(diretorio, "Local de outro operador", responsavel=outro.id)
    async with AsyncClient(transport=ASGITransport(app=diretorio.app), base_url="http://teste", headers={"Origin": "http://localhost:5500"}) as api:
        for rota in ["/api/pontos-coleta?escopo=meus", f"/api/pontos-coleta/{proprio.id}?escopo=meus"]:
            negado = await api.get(rota)
            assert negado.status_code == 401, negado.text
            assert negado.headers["www-authenticate"] == "Cookie"
        # A seleção do escopo protegido precede a validação dos filtros de gestão.
        assert (await api.get("/api/pontos-coleta?escopo=meus&categoria=invalida")).status_code == 401
        login = await api.post("/api/auth/login", json={"email": dono.email, "senha": "Senha123"})
        assert login.status_code == 200
        meus = await api.get("/api/pontos-coleta?escopo=meus")
        assert meus.status_code == 200, meus.text
        assert [p["id"] for p in meus.json()] == [proprio.id]
        assert meus.json()[0]["responsavel_id"] == dono.id
        assert meus.json()[0]["ativo"] is False
        detalhe = await api.get(f"/api/pontos-coleta/{proprio.id}?escopo=meus")
        assert detalhe.status_code == 200 and detalhe.json()["ativo"] is False
        assert (await api.get(f"/api/pontos-coleta/{proprio.id}")).status_code == 404
        api.cookies.clear()
        assert (await api.post("/api/auth/login", json={"email": outro.email, "senha": "Senha123"})).status_code == 200
        assert (await api.get(f"/api/pontos-coleta/{proprio.id}?escopo=meus")).status_code == 404
        api.cookies.clear()
        assert (await api.post("/api/auth/login", json={"email": "pessoa-local@example.test", "senha": "Senha123"})).status_code == 200
        assert (await api.get("/api/pontos-coleta?escopo=meus")).status_code == 403
        assert (await api.get(f"/api/pontos-coleta/{proprio.id}?escopo=meus")).status_code == 403
        assert set((await api.get("/api/pontos-coleta")).json()[0]) == PUBLICOS
        assert (await api.get("/api/pontos-coleta?escopo=meus&ativo=false")).status_code == 403


@pytest.mark.anyio
@pytest.mark.parametrize("query", ["offset=-1", "limite=0", "limite=101", "categoria=inexistente", "cidade=%20%20"])
async def test_filtros_publicos_invalidos_nao_sao_aceitos(diretorio, query):
    adicionar_local(diretorio)
    async with AsyncClient(transport=ASGITransport(app=diretorio.app), base_url="http://teste") as api:
        resposta = await api.get("/api/pontos-coleta?" + query)
        assert resposta.status_code == 400, resposta.text
        controle = await api.get("/api/pontos-coleta?offset=0&limite=1&categoria=notebook")
        assert controle.status_code == 200 and len(controle.json()) == 1
