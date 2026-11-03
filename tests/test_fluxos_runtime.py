"""Fluxos completos sobre replica set real; cada caso usa banco próprio por UUID."""
import os
from types import SimpleNamespace
from uuid import uuid4

from bson import ObjectId

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
    nome = "teste_fluxos_runtime_" + uuid4().hex
    assert nome not in cliente_mongo.list_database_names()
    monkeypatch.setenv("MONGO_URI", uri)
    monkeypatch.setenv("MONGO_DATABASE", nome)
    monkeypatch.setenv("MONGO_COLLECTION_USUARIOS", "participantes_fluxo")
    monkeypatch.setenv("MONGO_COLLECTION_ITENS", "equipamentos_fluxo")
    monkeypatch.setenv("MONGO_COLLECTION_PONTOS_COLETA", "locais_fluxo")
    monkeypatch.setenv("MONGO_COLLECTION_INTERESSES", "solicitacoes_fluxo")
    app = criar_app()
    banco = cliente_mongo[nome]
    contexto = SimpleNamespace(
        app=app,
        banco=banco,
        clientes=[],
        usuarios=banco.participantes_fluxo,
        itens=banco.equipamentos_fluxo,
        pontos=banco.locais_fluxo,
        interesses=banco.solicitacoes_fluxo,
    )
    try:
        with TestClient(app):
            yield contexto
    finally:
        for cliente in contexto.clientes:
            cliente.close()
        assert nome.startswith("teste_fluxos_runtime_")
        cliente_mongo.drop_database(nome)
        assert nome not in cliente_mongo.list_database_names()
        cliente_mongo.close()


def nova_conta(ambiente, nome, tipo="beneficiario"):
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
    assert (
        cliente.post(
            "/api/auth/login", json={"email": email, "senha": "Teste12345"}
        ).status_code
        == 200
    )
    return cliente, resposta.json()["id"], email


def novo_operador(ambiente, nome="operador"):
    """Provisiona a conta operacional pelo caminho de serviço e autentica."""
    from app.schemas.usuario import PontoColetaProvisionRequest
    from app.services.usuario_service import UsuarioService

    email = f"{nome}-{uuid4().hex[:8]}@example.test"
    servico = UsuarioService(ambiente.app.state.mongo_repository)
    operador = servico.provisionar_ponto_coleta(
        PontoColetaProvisionRequest(
            nome="Ponto de Coleta Teste",
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
    assert (
        cliente.post(
            "/api/auth/login", json={"email": email, "senha": "Teste12345"}
        ).status_code
        == 200
    )
    return cliente, operador.id


def criar_ponto(operador, nome, categorias):
    resposta = operador.post(
        "/api/pontos-coleta",
        json={
            "nome": nome,
            "endereco": {
                "logradouro": "Rua do Ponto",
                "numero": "10",
                "cep": "87000000",
                "cidade": "Maringá",
            },
            "categorias_aceitas": categorias,
            "horario_atendimento": "Segunda a sexta",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_item(cliente, **alteracoes):
    dados = {
        "titulo": "Notebook de teste",
        "descricao": "Fixture isolada",
        "categoria": "notebook",
        "marca": "Marca teste",
        "modelo": "Modelo teste",
        "condicao": "funcional",
        "destino": "doacao",
        "especificacoes": {"memoria_ram": "8 GB"},
    }
    dados.update(alteracoes)
    resposta = cliente.post("/api/itens", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def corpo(item, **alteracoes):
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


def test_indicadores_contam_apenas_itens_concluidos(ambiente):
    visitante = TestClient(ambiente.app)
    ambiente.clientes.append(visitante)
    sem_sessao = visitante.get("/api/indicadores")

    dono, _, _ = nova_conta(ambiente, "dono", "doador")
    interessado, _, _ = nova_conta(ambiente, "interessado")
    _, comprador_id, _ = nova_conta(ambiente, "comprador")

    doacao = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": doacao["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "aceito"})
    assert dono.put(
        f"/api/itens/{doacao['id']}", json=corpo(doacao, status="doado")
    ).status_code == 200

    revenda = criar_item(dono, destino="revenda", valor=90.0, titulo="Outro notebook")
    for etapa in ("em_avaliacao", "recondicionado"):
        assert dono.put(
            f"/api/itens/{revenda['id']}", json=corpo(revenda, status=etapa)
        ).status_code == 200
    assert dono.put(
        f"/api/itens/{revenda['id']}",
        json=corpo(revenda, status="vendido", comprador_id=comprador_id),
    ).status_code == 200
    criar_item(dono, destino="descarte", valor=None, titulo="Item ainda disponível")

    resposta = dono.get("/api/indicadores")

    assert sem_sessao.status_code == 401, sem_sessao.text
    assert resposta.status_code == 200, resposta.text
    assert resposta.json() == {"doados": 1, "coletados": 0, "vendidos": 1, "total": 2}


def test_doacao_completa_registra_beneficiario_do_aceite(ambiente):
    dono, dono_id, _ = nova_conta(ambiente, "dono", "doador")
    interessado, interessado_id, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]})
    assert interesse.status_code == 201, interesse.text
    assert (
        dono.patch(
            f"/api/interesses/{interesse.json()['id']}", json={"status": "aceito"}
        ).status_code
        == 200
    )
    reservado = dono.get(f"/api/itens/{item['id']}").json()
    assert reservado["status"] == "reservado"

    doado = dono.put(
        f"/api/itens/{item['id']}", json=corpo(item, status="doado")
    )

    assert doado.status_code == 200, doado.text
    resultado = doado.json()
    assert resultado["status"] == "doado"
    assert resultado["beneficiario_id"] == interessado_id
    assert [evento["status"] for evento in resultado["historico"]] == [
        "disponivel",
        "reservado",
        "doado",
    ]
    documento = ambiente.itens.find_one({"titulo": "Notebook de teste"})
    assert str(documento["beneficiario_id"]) == interessado_id
    assert str(documento["proprietario_id"]) == dono_id


def test_descarte_exige_ponto_compativel_e_conclui(ambiente):
    dono, _, _ = nova_conta(ambiente, "dono", "doador")
    operador, _ = novo_operador(ambiente)
    compatível = criar_ponto(operador, "Ponto de notebook", ["notebook"])["id"]
    incompatível = criar_ponto(operador, "Ponto de celular", ["celular"])["id"]

    item = criar_item(dono, destino="descarte", valor=None)
    recusado = dono.put(
        f"/api/itens/{item['id']}",
        json=corpo(item, status="encaminhado", ponto_coleta_id=incompatível),
    )
    encaminhado = dono.put(
        f"/api/itens/{item['id']}",
        json=corpo(item, status="encaminhado", ponto_coleta_id=compatível),
    )
    coletado = dono.put(f"/api/itens/{item['id']}", json=corpo(item, status="coletado"))

    assert recusado.status_code == 400, recusado.text
    assert encaminhado.status_code == 200, encaminhado.text
    assert encaminhado.json()["ponto_coleta_id"] == compatível
    assert coletado.status_code == 200, coletado.text
    assert coletado.json()["status"] == "coletado"
    assert coletado.json()["ponto_coleta_id"] == compatível
    documento = ambiente.itens.find_one({"_id": ObjectId(item["id"])})
    assert str(documento["ponto_coleta_id"]) == compatível


def test_revenda_completa_e_segunda_conclusao(ambiente):
    dono, _, _ = nova_conta(ambiente, "dono", "doador")
    comprador, comprador_id, _ = nova_conta(ambiente, "comprador")
    item = criar_item(dono, destino="revenda", valor=300.0, condicao="reparavel")
    assert dono.put(
        f"/api/itens/{item['id']}", json=corpo(item, status="em_avaliacao")
    ).status_code == 200
    assert dono.put(
        f"/api/itens/{item['id']}",
        json=corpo(item, status="recondicionado", observacao="Placa substituída"),
    ).status_code == 200
    sem_comprador = dono.put(
        f"/api/itens/{item['id']}", json=corpo(item, status="vendido")
    )
    vendido = dono.put(
        f"/api/itens/{item['id']}",
        json=corpo(item, status="vendido", comprador_id=comprador_id),
    )
    segunda = dono.put(
        f"/api/itens/{item['id']}", json=corpo(item, status="recondicionado")
    )

    assert sem_comprador.status_code == 400, sem_comprador.text
    assert vendido.status_code == 200, vendido.text
    assert vendido.json()["status"] == "vendido"
    assert vendido.json()["comprador_id"] == comprador_id
    assert vendido.json()["valor"] == 300.0
    assert vendido.json()["historico"][-2]["observacao"] == "Placa substituída"
    assert segunda.status_code == 400, segunda.text
    assert ambiente.itens.count_documents({"status": "vendido"}) == 1


def test_referencias_do_fluxo_bloqueiam_exclusao(ambiente):
    dono, dono_id, _ = nova_conta(ambiente, "dono", "doador")
    interessado, interessado_id, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "aceito"})
    assert dono.put(
        f"/api/itens/{item['id']}", json=corpo(item, status="doado")
    ).status_code == 200

    excluir_beneficiario = interessado.delete(f"/api/usuarios/{interessado_id}")
    excluir_proprietario = dono.delete(f"/api/usuarios/{dono_id}")

    assert excluir_beneficiario.status_code == 409, excluir_beneficiario.text
    assert excluir_proprietario.status_code == 409, excluir_proprietario.text
    assert ambiente.usuarios.count_documents({"_id": ObjectId(interessado_id)}) == 1
    assert ambiente.usuarios.count_documents({"_id": ObjectId(dono_id)}) == 1
    operador, _ = novo_operador(ambiente)
    ponto = criar_ponto(operador, "Ponto referenciado", ["notebook"])
    descarte = criar_item(dono, destino="descarte", valor=None)
    assert dono.put(
        f"/api/itens/{descarte['id']}",
        json=corpo(descarte, status="encaminhado", ponto_coleta_id=ponto["id"]),
    ).status_code == 200
    excluir_ponto = operador.delete(f"/api/pontos-coleta/{ponto['id']}")

    assert excluir_ponto.status_code == 409, excluir_ponto.text
    assert ambiente.pontos.count_documents({"_id": ObjectId(ponto["id"])}) == 1

    sem_vinculo, sem_vinculo_id, _ = nova_conta(ambiente, "sem-vinculo")
    excluir_sem_vinculo = sem_vinculo.delete(f"/api/usuarios/{sem_vinculo_id}")

    assert excluir_sem_vinculo.status_code == 204, excluir_sem_vinculo.text
    assert ambiente.usuarios.count_documents({"_id": ObjectId(sem_vinculo_id)}) == 0
