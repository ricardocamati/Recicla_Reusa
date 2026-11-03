"""Destinação informada pelo autor, sobre replica set real."""
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.main import criar_app


@pytest.fixture
def ambiente(monkeypatch):
    uri = os.environ.get("INTERESSES_TEST_MONGO_URI")
    if not uri:
        pytest.skip("defina INTERESSES_TEST_MONGO_URI para executar contra replica set real")
    cliente_mongo = MongoClient(uri, serverSelectionTimeoutMS=5000)
    assert cliente_mongo.admin.command("hello").get("setName"), "teste exige replica set"
    nome = "teste_destinacao_" + uuid4().hex
    monkeypatch.setenv("MONGO_URI", uri)
    monkeypatch.setenv("MONGO_DATABASE", nome)
    monkeypatch.setenv("MONGO_COLLECTION_USUARIOS", "contas_dest")
    monkeypatch.setenv("MONGO_COLLECTION_ITENS", "itens_dest")
    monkeypatch.setenv("MONGO_COLLECTION_PONTOS_COLETA", "pontos_dest")
    monkeypatch.setenv("MONGO_COLLECTION_INTERESSES", "interesses_dest")
    monkeypatch.setenv("MONGO_COLLECTION_NOTIFICACOES", "avisos_dest")
    monkeypatch.setenv("MONGO_COLLECTION_ENCAMINHAMENTOS", "entregas_dest")
    app = criar_app()
    banco = cliente_mongo[nome]
    contexto = SimpleNamespace(
        app=app,
        banco=banco,
        clientes=[],
        itens=banco.itens_dest,
        pontos=banco.pontos_dest,
    )
    try:
        with TestClient(app):
            yield contexto
    finally:
        for cliente in contexto.clientes:
            cliente.close()
        assert nome.startswith("teste_destinacao_")
        cliente_mongo.drop_database(nome)
        cliente_mongo.close()


def nova_conta(ambiente, nome, tipo="pessoa"):
    cliente = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.append(cliente)
    email = f"{nome}-{uuid4().hex[:8]}@example.test"
    resposta = cliente.post(
        "/api/usuarios",
        json={
            "nome": "Pessoa " + nome,
            "email": email,
            "senha": "Teste12345",
            "tipo": tipo,
            "endereco": {
                "logradouro": "Rua Teste",
                "numero": "1",
                "cep": "87000000",
                "cidade": "Maringá",
            },
        },
    )
    assert resposta.status_code == 201, resposta.text
    assert cliente.post(
        "/api/auth/login", json={"email": email, "senha": "Teste12345"}
    ).status_code == 200
    return cliente, resposta.json()["id"]


def novo_operador(ambiente, nome="operador"):
    from app.schemas.usuario import PontoColetaProvisionRequest
    from app.services.usuario_service import UsuarioService

    email = f"{nome}-{uuid4().hex[:8]}@example.test"
    UsuarioService(ambiente.app.state.mongo_repository).provisionar_ponto_coleta(
        PontoColetaProvisionRequest(
            nome="Operação Destino",
            email=email,
            senha="Teste12345",
            endereco={
                "logradouro": "Rua do Ponto",
                "numero": "10",
                "cep": "87000000",
                "cidade": "Maringá",
            },
        )
    )
    cliente = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.append(cliente)
    assert cliente.post(
        "/api/auth/login", json={"email": email, "senha": "Teste12345"}
    ).status_code == 200
    return cliente


def criar_descarte(cliente, titulo="Geladeira velha", categoria="eletrodomestico"):
    resposta = cliente.post(
        "/api/itens",
        json={
            "titulo": titulo,
            "descricao": "Descarte do autor",
            "categoria": categoria,
            "marca": "Marca teste",
            "modelo": "Modelo teste",
            "condicao": "sem_conserto",
            "destino": "descarte",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def informar(cliente, item, **campos):
    dados = {"tipo_local": "ecoponto"}
    dados.update(campos)
    return cliente.post(f"/api/itens/{item['id']}/destinacao", json=dados)


def test_informar_destinacao_encerra_item_com_rotulo(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    item = criar_descarte(dono)

    resposta = informar(dono, item, nome="Ecoponto Zona Norte", cidade="Maringá")
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["status"] == "destinacao_informada"
    assert corpo["destinacao_informada"]["tipo_local"] == "ecoponto"
    assert corpo["destinacao_informada"]["nome"] == "Ecoponto Zona Norte"
    assert corpo["ponto_coleta_id"] is None
    assert ambiente.pontos.count_documents({}) == 0
    assert corpo["historico"][-1]["status"] == "destinacao_informada"

    assert dono.get("/api/itens").json() == []


def test_destinacao_nao_vaza_para_terceiros_nem_operador(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    vizinho, _ = nova_conta(ambiente, "vizinho")
    operador = novo_operador(ambiente)
    item = criar_descarte(dono)
    assert informar(dono, item, tipo_local="cooperativa").status_code == 200

    propria = dono.get(f"/api/itens/{item['id']}").json()
    assert propria["destinacao_informada"] is not None
    alheia = vizinho.get(f"/api/itens/{item['id']}").json()
    assert alheia["destinacao_informada"] is None
    operador_vista = operador.get(f"/api/itens/{item['id']}").json()
    assert operador_vista["destinacao_informada"] is None

    fila = operador.get("/api/encaminhamentos?escopo=operador").json()
    assert fila == []


def test_validacao_da_indicacao(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    item = criar_descarte(dono)

    assert dono.post(f"/api/itens/{item['id']}/destinacao", json={}).status_code == 400
    assert informar(dono, item, tipo_local="lixao").status_code == 400
    assert informar(dono, item, nome="x" * 121).status_code == 400
    assert informar(dono, item, observacao="y" * 301).status_code == 400
    assert (
        dono.post(
            f"/api/itens/{item['id']}/destinacao",
            json={"tipo_local": "ecoponto", "latitude": -23.4},
        ).status_code
        == 400
    )
    assert (
        dono.post(
            f"/api/itens/{item['id']}/destinacao",
            json={"tipo_local": "ecoponto", "arquivo": "comprovante.pdf"},
        ).status_code
        == 400
    )

    documento = ambiente.itens.find_one({"titulo": item["titulo"]})
    assert documento["status"] == "aguardando_ponto"
    assert documento.get("destinacao_informada") is None


def test_indicacao_e_tentativa_ativa_nao_coexistem(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    ponto = operador.post(
        "/api/pontos-coleta",
        json={
            "nome": "Ponto Central",
            "endereco": {
                "logradouro": "Rua do Ponto",
                "numero": "10",
                "cep": "87000000",
                "cidade": "Maringá",
            },
            "categorias_aceitas": ["eletrodomestico"],
            "horario_atendimento": "Segunda a sexta",
        },
    ).json()
    item = criar_descarte(dono)

    assert informar(dono, item, tipo_local="comercio").status_code == 200
    conflito = dono.post(
        "/api/encaminhamentos", json={"item_id": item["id"], "ponto_id": ponto["id"]}
    )
    assert conflito.status_code == 409
    assert "aguardando" in conflito.json()["detail"]

    assert dono.delete(f"/api/itens/{item['id']}/destinacao").status_code == 200
    assert (
        dono.post(
            "/api/encaminhamentos", json={"item_id": item["id"], "ponto_id": ponto["id"]}
        ).status_code
        == 201
    )
    previsto = dono.post(
        f"/api/itens/{item['id']}/destinacao", json={"tipo_local": "ecoponto"}
    )
    assert previsto.status_code == 409


def test_desfazer_preserva_historico_e_bloqueia_arquivado(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    item = criar_descarte(dono)
    assert informar(dono, item, tipo_local="outro", nome="Ferro-velho do bairro").status_code == 200

    desfeito = dono.delete(f"/api/itens/{item['id']}/destinacao")
    assert desfeito.status_code == 200, desfeito.text
    corpo = desfeito.json()
    assert corpo["status"] == "aguardando_ponto"
    assert corpo["destinacao_informada"] is None
    assert [evento["status"] for evento in corpo["historico"]] == [
        "aguardando_ponto",
        "destinacao_informada",
        "aguardando_ponto",
    ]

    repetido = dono.delete(f"/api/itens/{item['id']}/destinacao")
    assert repetido.status_code == 409

    assert dono.post(f"/api/itens/{item['id']}/arquivar").status_code == 200
    bloqueado = dono.delete(f"/api/itens/{item['id']}/destinacao")
    assert bloqueado.status_code == 409


def test_indicadores_separam_recebido_de_indicado(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    ponto = operador.post(
        "/api/pontos-coleta",
        json={
            "nome": "Ponto Recebedor",
            "endereco": {
                "logradouro": "Rua do Ponto",
                "numero": "10",
                "cep": "87000000",
                "cidade": "Maringá",
            },
            "categorias_aceitas": ["eletrodomestico"],
            "horario_atendimento": "Segunda a sexta",
        },
    ).json()

    recebido = criar_descarte(dono, "Fogão entregue")
    entrega = dono.post(
        "/api/encaminhamentos",
        json={"item_id": recebido["id"], "ponto_id": ponto["id"]},
    ).json()
    assert operador.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes", json={"acao": "receber"}
    ).status_code == 200

    indicado = criar_descarte(dono, "Micro-ondas indicado")
    assert informar(dono, indicado, tipo_local="ecoponto").status_code == 200

    indicadores = dono.get("/api/indicadores").json()
    assert indicadores["coletados"] == 1
    assert indicadores["indicados"] == 1
    assert indicadores["total"] == 1

    assert dono.delete(f"/api/itens/{indicado['id']}/destinacao").status_code == 200
    depois = dono.get("/api/indicadores").json()
    assert depois["indicados"] == 0
    assert depois["coletados"] == 1
