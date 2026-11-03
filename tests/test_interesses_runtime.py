"""API real sobre replica set isolado; não usa mongomock para transações.

Execute com INTERESSES_TEST_MONGO_URI apontando para a instância de teste.
Cada caso cria e remove somente seu próprio banco, identificado por UUID.
"""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4
from threading import Barrier
import os

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
    nome = "teste_interesses_runtime_" + uuid4().hex
    assert nome not in cliente_mongo.list_database_names()
    monkeypatch.setenv("MONGO_URI", uri)
    monkeypatch.setenv("MONGO_DATABASE", nome)
    monkeypatch.setenv("MONGO_COLLECTION_USUARIOS", "participantes_teste")
    monkeypatch.setenv("MONGO_COLLECTION_ITENS", "equipamentos_teste")
    monkeypatch.setenv("MONGO_COLLECTION_PONTOS_COLETA", "locais_teste")
    monkeypatch.setenv("MONGO_COLLECTION_INTERESSES", "solicitacoes_teste")
    app = criar_app()
    contexto = SimpleNamespace(
        app=app, banco=cliente_mongo[nome], clientes=[],
        usuarios=cliente_mongo[nome].participantes_teste,
        itens=cliente_mongo[nome].equipamentos_teste,
        interesses=cliente_mongo[nome].solicitacoes_teste,
    )
    try:
        with TestClient(app):
            yield contexto
    finally:
        for cliente in contexto.clientes:
            cliente.close()
        assert nome.startswith("teste_interesses_runtime_")
        cliente_mongo.drop_database(nome)
        assert nome not in cliente_mongo.list_database_names()
        cliente_mongo.close()


def nova_conta(ambiente, nome, tipo="beneficiario"):
    cliente = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.append(cliente)
    email = nome + "@example.test"
    resposta = cliente.post("/api/usuarios", json={
        "nome": "Pessoa " + nome, "email": email, "senha": "Teste12345", "tipo": tipo,
        "endereco": {"logradouro": "Rua Teste", "numero": "1", "cep": "87000000", "cidade": "Maringá"},
    })
    assert resposta.status_code == 201, resposta.text
    assert cliente.post("/api/auth/login", json={"email": email, "senha": "Teste12345"}).status_code == 200
    return cliente, resposta.json()["id"]


def criar_item(cliente, destino="doacao"):
    dados = {"titulo": "Notebook de teste", "descricao": "Fixture isolada", "categoria": "notebook",
             "marca": "Marca teste", "modelo": "Modelo teste", "condicao": "funcional", "destino": destino,
             "especificacoes": {"memoria_ram": "8 GB"}}
    if destino == "revenda":
        dados["valor"] = 100
    resposta = cliente.post("/api/itens", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_interesse(cliente, item):
    resposta = cliente.post("/api/interesses", json={"item_id": item["id"]})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_ct10_ct11_ct12_reserva_cancelamento_e_privacidade(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "doador")
    interessado, usuario_id = nova_conta(ambiente, "interessado")
    terceiro, _ = nova_conta(ambiente, "terceiro")
    item = criar_item(dono)
    assert dono.post("/api/interesses", json={"item_id": item["id"]}).status_code == 400
    interesse = criar_interesse(interessado, item)
    assert interesse["usuario_id"] == usuario_id
    assert interesse["data_adicao"] == interesse["data_modificacao"]
    assert interesse["data_adicao"].endswith("Z")
    assert interessado.post("/api/interesses", json={"item_id": item["id"]}).status_code == 409
    assert terceiro.get("/api/interesses/" + interesse["id"]).status_code == 404
    assert terceiro.get("/api/interesses").json() == []
    assert interessado.patch("/api/interesses/" + interesse["id"], json={"status": "aceito"}).status_code == 403
    aceito = dono.patch("/api/interesses/" + interesse["id"], json={"status": "aceito"})
    assert aceito.status_code == 200, aceito.text
    reservado = dono.get("/api/itens/" + item["id"])
    assert reservado.status_code == 200, reservado.text
    assert reservado.json()["status"] == "reservado"
    assert [evento["status"] for evento in reservado.json()["historico"]] == ["disponivel", "reservado"]
    assert "interesse_aceito_id" not in reservado.json()
    recebido = dono.get("/api/interesses", params={"escopo": "recebidos"}).json()
    assert [r["id"] for r in recebido] == [interesse["id"]]
    cancelado = interessado.patch("/api/interesses/" + interesse["id"], json={"status": "cancelado"})
    assert cancelado.status_code == 200, cancelado.text
    relido = dono.get("/api/itens/" + item["id"]).json()
    assert relido["status"] == "disponivel"
    assert [evento["status"] for evento in relido["historico"]] == ["disponivel", "reservado", "disponivel"]
    assert cancelado.json()["data_adicao"] == interesse["data_adicao"]
    assert ambiente.interesses.count_documents({}) == 1
    indices = ambiente.interesses.index_information()
    assert any(i.get("unique") and i["key"] == [("item_id", 1), ("usuario_id", 1)] for i in indices.values())


@pytest.mark.parametrize(
    "destino, status_esperado",
    [("doacao", "reservado"), ("revenda", "disponivel")],
)
def test_selecao_nula_pode_ser_aceita_por_api(ambiente, destino, status_esperado):
    from bson import ObjectId

    dono, _ = nova_conta(ambiente, "dono", "doador")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono, destino)
    item_oid = ObjectId(item["id"])
    ambiente.itens.update_one({"_id": item_oid}, {"$set": {"interesse_aceito_id": None}})
    assert "interesse_aceito_id" in ambiente.itens.find_one({"_id": item_oid})
    assert ambiente.itens.find_one({"_id": item_oid})["interesse_aceito_id"] is None

    interesse = criar_interesse(interessado, item)
    aceito = dono.patch("/api/interesses/" + interesse["id"], json={"status": "aceito"})

    assert aceito.status_code == 200, aceito.text
    persistido = ambiente.itens.find_one({"_id": item_oid})
    assert persistido["interesse_aceito_id"] == ObjectId(interesse["id"])
    assert persistido["status"] == status_esperado


def test_dois_aceites_reais_tem_um_vencedor_e_um_conflito(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "doador")
    primeiro, _ = nova_conta(ambiente, "primeiro")
    segundo, _ = nova_conta(ambiente, "segundo")
    item = criar_item(dono)
    interesses = [criar_interesse(primeiro, item), criar_interesse(segundo, item)]
    barreira = Barrier(2)
    def aceitar(interesse):
        barreira.wait(timeout=15)
        resposta = dono.patch("/api/interesses/" + interesse["id"], json={"status": "aceito"})
        return resposta.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(aceitar, interesses))
    assert sorted(resultados) == [200, 409], resultados
    assert ambiente.interesses.count_documents({"status": "aceito"}) == 1
    assert ambiente.interesses.count_documents({"status": "pendente"}) == 1
    persistido = ambiente.itens.find_one()
    assert persistido["status"] == "reservado"
    assert len(persistido["historico"]) == 2


def test_descarte_invalido_item_inexistente_e_preflight_patch(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "doador")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono, "descarte")
    assert interessado.post("/api/interesses", json={"item_id": item["id"]}).status_code == 400
    assert interessado.post("/api/interesses", json={"item_id": "f" * 24}).status_code == 404
    resposta = interessado.options("/api/interesses/" + "f" * 24, headers={
        "Origin": "http://localhost:5500", "Access-Control-Request-Method": "PATCH",
    })
    assert resposta.status_code == 200, resposta.text
    assert "PATCH" in resposta.headers["access-control-allow-methods"]


def test_recusa_e_venda_nao_antecipam_avaliacao(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "doador")
    primeiro, _ = nova_conta(ambiente, "primeiro")
    segundo, _ = nova_conta(ambiente, "segundo")
    item = criar_item(dono, "revenda")
    interesse = criar_interesse(primeiro, item)
    recusado = dono.patch("/api/interesses/" + interesse["id"], json={"status": "recusado"})
    assert recusado.status_code == 200, recusado.text
    assert primeiro.patch("/api/interesses/" + interesse["id"], json={"status": "aceito"}).status_code in (403, 409)
    outro = criar_interesse(segundo, item)
    aceito = dono.patch("/api/interesses/" + outro["id"], json={"status": "aceito"})
    assert aceito.status_code == 200, aceito.text
    assert dono.get("/api/itens/" + item["id"]).json()["status"] == "disponivel"
    cancelado = segundo.patch("/api/interesses/" + outro["id"], json={"status": "cancelado"})
    assert cancelado.status_code == 200, cancelado.text


def test_cancelar_aceito_apos_conclusao_nao_altera_interesse(ambiente):
    from bson import ObjectId
    dono, _ = nova_conta(ambiente, "dono", "doador")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = criar_interesse(interessado, item)
    assert dono.patch("/api/interesses/" + interesse["id"], json={"status": "aceito"}).status_code == 200
    ambiente.itens.update_one({"_id": ObjectId(item["id"])}, {"$set": {"status": "doado"}})
    resposta = interessado.patch("/api/interesses/" + interesse["id"], json={"status": "cancelado"})
    assert resposta.status_code == 409, resposta.text
    assert ambiente.interesses.find_one()["status"] == "aceito"


def test_rollback_real_apos_escrever_item_e_interesse(ambiente, monkeypatch):
    from pymongo.errors import OperationFailure
    from app.exceptions import InteresseError
    from datetime import datetime, UTC
    dono, dono_id = nova_conta(ambiente, "dono", "doador")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = criar_interesse(interessado, item)
    antes_item = ambiente.itens.find_one()
    antes_interesse = ambiente.interesses.find_one()
    repo = ambiente.app.state.mongo_interesse_repository
    real = repo._colecao
    class FalhaAposEscrita:
        def __getattr__(self, nome):
            return getattr(real, nome)
        def update_one(self, *args, **kwargs):
            real.update_one(*args, **kwargs)
            raise OperationFailure("falha controlada para validar rollback", code=123)
    monkeypatch.setattr(repo, "_colecao", FalhaAposEscrita())
    with pytest.raises(InteresseError) as erro:
        repo.decidir(interesse["id"], "aceito", dono_id, datetime.now(UTC))
    assert erro.value.status_code == 503
    assert ambiente.itens.find_one() == antes_item
    assert ambiente.interesses.find_one() == antes_interesse


def test_consultas_rejeitam_extras_e_detalhe_prioriza_visibilidade(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "doador")
    interessado, _ = nova_conta(ambiente, "interessado")
    terceiro, _ = nova_conta(ambiente, "terceiro")
    interesse = criar_interesse(interessado, criar_item(dono))
    assert dono.get("/api/interesses", params={"extra": "valor"}).status_code == 400
    assert dono.patch("/api/interesses/invalido", json={}).status_code == 404
    resposta = terceiro.patch("/api/interesses/" + interesse["id"], content="{", headers={"Content-Type": "application/json"})
    assert resposta.status_code == 404


def test_referencias_de_interesse_bloqueiam_exclusao_e_reserva_direta(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "doador")
    interessado, usuario_id = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    campos = ("titulo", "descricao", "categoria", "marca", "modelo", "condicao", "destino", "valor", "especificacoes")
    dados = {k: item[k] for k in campos}
    assert dono.put("/api/itens/" + item["id"], json=dados | {"status": "reservado"}).status_code == 409
    criar_interesse(interessado, item)
    assert dono.delete("/api/itens/" + item["id"]).status_code == 409
    assert interessado.delete("/api/usuarios/" + usuario_id).status_code == 409
    assert dono.put("/api/itens/" + item["id"], json=dados | {"destino": "descarte"}).status_code == 409
