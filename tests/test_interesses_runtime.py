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


def nova_conta(ambiente, nome, tipo="pessoa"):
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
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
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
    assert interessado.patch("/api/interesses/" + interesse["id"], json={"status": "selecionado"}).status_code == 403
    aceito = dono.patch("/api/interesses/" + interesse["id"], json={"status": "selecionado"})
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
    [("doacao", "reservado"), ("revenda", "reservado")],
)
def test_selecao_nula_pode_ser_aceita_por_api(ambiente, destino, status_esperado):
    from bson import ObjectId

    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono, destino)
    item_oid = ObjectId(item["id"])
    ambiente.itens.update_one({"_id": item_oid}, {"$set": {"interesse_aceito_id": None}})
    assert "interesse_aceito_id" in ambiente.itens.find_one({"_id": item_oid})
    assert ambiente.itens.find_one({"_id": item_oid})["interesse_aceito_id"] is None

    interesse = criar_interesse(interessado, item)
    aceito = dono.patch("/api/interesses/" + interesse["id"], json={"status": "selecionado"})

    assert aceito.status_code == 200, aceito.text
    persistido = ambiente.itens.find_one({"_id": item_oid})
    assert persistido["interesse_aceito_id"] == ObjectId(interesse["id"])
    assert persistido["status"] == status_esperado


def test_dois_aceites_reais_tem_um_vencedor_e_um_conflito(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    primeiro, _ = nova_conta(ambiente, "primeiro")
    segundo, _ = nova_conta(ambiente, "segundo")
    item = criar_item(dono)
    interesses = [criar_interesse(primeiro, item), criar_interesse(segundo, item)]
    barreira = Barrier(2)
    def aceitar(interesse):
        barreira.wait(timeout=15)
        resposta = dono.patch("/api/interesses/" + interesse["id"], json={"status": "selecionado"})
        return resposta.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(aceitar, interesses))
    assert sorted(resultados) == [200, 409], resultados
    assert ambiente.interesses.count_documents({"status": "selecionado"}) == 1
    assert ambiente.interesses.count_documents({"status": "pendente"}) == 1
    persistido = ambiente.itens.find_one()
    assert persistido["status"] == "reservado"
    assert len(persistido["historico"]) == 2


def test_recusa_e_venda_nao_antecipam_avaliacao(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    primeiro, _ = nova_conta(ambiente, "primeiro")
    segundo, _ = nova_conta(ambiente, "segundo")
    item = criar_item(dono, "revenda")
    interesse = criar_interesse(primeiro, item)
    recusado = dono.patch("/api/interesses/" + interesse["id"], json={"status": "recusado"})
    assert recusado.status_code == 200, recusado.text
    assert primeiro.patch("/api/interesses/" + interesse["id"], json={"status": "selecionado"}).status_code in (403, 409)
    outro = criar_interesse(segundo, item)
    aceito = dono.patch("/api/interesses/" + outro["id"], json={"status": "selecionado"})
    assert aceito.status_code == 200, aceito.text
    assert dono.get("/api/itens/" + item["id"]).json()["status"] == "reservado"
    cancelado = segundo.patch("/api/interesses/" + outro["id"], json={"status": "cancelado"})
    assert cancelado.status_code == 200, cancelado.text
    assert dono.get("/api/itens/" + item["id"]).json()["status"] == "disponivel"


def test_cancelar_aceito_apos_conclusao_nao_altera_interesse(ambiente):
    from bson import ObjectId
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = criar_interesse(interessado, item)
    assert dono.patch("/api/interesses/" + interesse["id"], json={"status": "selecionado"}).status_code == 200
    ambiente.itens.update_one({"_id": ObjectId(item["id"])}, {"$set": {"status": "doado"}})
    resposta = interessado.patch("/api/interesses/" + interesse["id"], json={"status": "cancelado"})
    assert resposta.status_code == 409, resposta.text
    assert ambiente.interesses.find_one()["status"] == "selecionado"


def test_rollback_real_apos_escrever_item_e_interesse(ambiente, monkeypatch):
    from pymongo.errors import OperationFailure
    from app.exceptions import InteresseError
    from datetime import datetime, UTC
    dono, dono_id = nova_conta(ambiente, "dono", "pessoa")
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
        repo.decidir(interesse["id"], "selecionado", dono_id, datetime.now(UTC))
    assert erro.value.status_code == 503
    assert ambiente.itens.find_one() == antes_item
    assert ambiente.interesses.find_one() == antes_interesse


def test_consultas_rejeitam_extras_e_detalhe_prioriza_visibilidade(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    terceiro, _ = nova_conta(ambiente, "terceiro")
    interesse = criar_interesse(interessado, criar_item(dono))
    assert dono.get("/api/interesses", params={"extra": "valor"}).status_code == 400
    assert dono.patch("/api/interesses/invalido", json={}).status_code == 404
    resposta = terceiro.patch("/api/interesses/" + interesse["id"], content="{", headers={"Content-Type": "application/json"})
    assert resposta.status_code == 404


def test_referencias_de_interesse_bloqueiam_exclusao_e_reserva_direta(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, usuario_id = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    campos = ("titulo", "descricao", "categoria", "marca", "modelo", "condicao", "destino", "valor", "especificacoes")
    dados = {k: item[k] for k in campos}
    assert dono.put("/api/itens/" + item["id"], json=dados | {"status": "reservado"}).status_code == 409
    criar_interesse(interessado, item)
    assert dono.delete("/api/itens/" + item["id"]).status_code == 409
    assert interessado.delete("/api/usuarios/" + usuario_id).status_code == 409
    # Modalidade só muda enquanto rascunho; publicado com interesse, o comando é recusado.
    troca = dono.put("/api/itens/" + item["id"], json=dados | {"destino": "descarte"})
    assert troca.status_code == 400
    assert dono.get("/api/itens/" + item["id"]).json()["destino"] == "doacao"


def test_conta_unica_oferece_e_interessa_nas_duas_pontas(ambiente):
    from datetime import UTC, datetime

    from app.security.passwords import hash_password

    ana, ana_id = nova_conta(ambiente, "ana")
    bia, bia_id = nova_conta(ambiente, "bia")
    item_ana = criar_item(ana)
    item_bia = criar_item(bia)

    # A mesma conta oferece e demonstra interesse na oferta da outra pessoa.
    interesse_de_bia = criar_interesse(bia, item_ana)
    interesse_de_ana = criar_interesse(ana, item_bia)
    assert interesse_de_bia["usuario_id"] == bia_id
    assert interesse_de_ana["usuario_id"] == ana_id

    recebidos_ana = ana.get("/api/interesses", params={"escopo": "recebidos"}).json()
    recebidos_bia = bia.get("/api/interesses", params={"escopo": "recebidos"}).json()
    assert [i["item_id"] for i in recebidos_ana] == [item_ana["id"]]
    assert [i["item_id"] for i in recebidos_bia] == [item_bia["id"]]

    # Operador é provisionado, não se cadastra, e não recebe comandos de compra.
    agora = datetime.now(UTC)
    ambiente.usuarios.insert_one(
        {
            "nome": "Operador",
            "email": "operador@example.test",
            "tipo": "ponto_coleta",
            "senha_hash": hash_password("Teste12345"),
            "endereco": {
                "logradouro": "Rua do Ponto",
                "numero": "10",
                "complemento": None,
                "cep": "87000000",
                "cidade": "Maringá",
            },
            "data_adicao": agora,
            "data_modificacao": agora,
        }
    )
    operador = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.append(operador)
    login = operador.post(
        "/api/auth/login",
        json={"email": "operador@example.test", "senha": "Teste12345"},
    )
    assert login.status_code == 200, login.text

    negado_interesse = operador.post("/api/interesses", json={"item_id": item_ana["id"]})
    negado_recebidos = operador.get("/api/interesses", params={"escopo": "recebidos"})
    negado_item = operador.post(
        "/api/itens",
        json={
            "titulo": "Oferta indevida",
            "descricao": "Operador não oferta",
            "categoria": "notebook",
            "marca": "Marca teste",
            "modelo": "Modelo teste",
            "condicao": "funcional",
            "destino": "doacao",
            "especificacoes": {},
        },
    )
    assert negado_interesse.status_code == 403
    assert negado_recebidos.status_code == 403
    assert negado_item.status_code == 403


def test_retomada_reabertura_e_uma_relacao_por_par(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    autor, autor_id = nova_conta(ambiente, "autor")
    item = criar_item(dono)
    interesse = criar_interesse(autor, item)

    # Uma relação por par item/pessoa.
    assert autor.post("/api/interesses", json={"item_id": item["id"]}).status_code == 409

    cancelado = autor.post(
        f"/api/interesses/{interesse['id']}/acoes", json={"acao": "desistir"}
    )
    assert cancelado.status_code == 200, cancelado.text
    assert cancelado.json()["status"] == "cancelado"
    assert cancelado.json()["tentativa"] == 1

    # Autor retoma o próprio cancelado; a tentativa avança e o histórico acumula.
    retomado = autor.post(
        f"/api/interesses/{interesse['id']}/acoes", json={"acao": "retomar"}
    )
    assert retomado.status_code == 200, retomado.text
    corpo = retomado.json()
    assert corpo["status"] == "pendente"
    assert corpo["tentativa"] == 2
    assert [evento["status"] for evento in corpo["historico"]] == [
        "pendente",
        "cancelado",
        "pendente",
    ]

    # Recusa exige motivo e não pode ser retomada pelo autor.
    sem_motivo = dono.post(
        f"/api/interesses/{interesse['id']}/acoes", json={"acao": "recusar"}
    )
    assert sem_motivo.status_code == 400
    recusado = dono.post(
        f"/api/interesses/{interesse['id']}/acoes",
        json={"acao": "recusar", "motivo": "Item já prometido"},
    )
    assert recusado.status_code == 200, recusado.text
    assert recusado.json()["status"] == "recusado"
    assert recusado.json()["motivo"] == "Item já prometido"
    # Recusado não volta por vontade do autor: precisa do comando do proprietário.
    assert autor.post(
        f"/api/interesses/{interesse['id']}/acoes", json={"acao": "retomar"}
    ).status_code == 400

    # Só o proprietário reabre o recusado, incrementando a tentativa.
    reaberto = dono.post(
        f"/api/interesses/{interesse['id']}/acoes", json={"acao": "reabrir"}
    )
    assert reaberto.status_code == 200, reaberto.text
    assert reaberto.json()["status"] == "pendente"
    assert reaberto.json()["tentativa"] == 3
    assert reaberto.json()["motivo"] is None


def test_reserva_desistencia_e_liberacao_revertem_o_item(ambiente):
    from bson import ObjectId

    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    primeiro, _ = nova_conta(ambiente, "primeiro")
    segundo, _ = nova_conta(ambiente, "segundo")
    item = criar_item(dono, "revenda")
    interesse_primeiro = criar_interesse(primeiro, item)
    interesse_segundo = criar_interesse(segundo, item)

    selecionado = dono.post(
        f"/api/interesses/{interesse_primeiro['id']}/acoes", json={"acao": "selecionar"}
    )
    assert selecionado.status_code == 200, selecionado.text
    assert selecionado.json()["status"] == "selecionado"
    assert selecionado.json()["preco_selecionado"] == item["valor"]
    item_reservado = dono.get("/api/itens/" + item["id"]).json()
    assert item_reservado["status"] == "reservado"
    # Os demais pendentes permanecem e não entra interesse novo durante a reserva.
    assert ambiente.interesses.find_one({"_id": ObjectId(interesse_segundo["id"])})["status"] == "pendente"
    assert segundo.post("/api/interesses", json={"item_id": item["id"]}).status_code == 409

    # Desistência do selecionado devolve o item e preserva o outro pendente.
    desistiu = primeiro.post(
        f"/api/interesses/{interesse_primeiro['id']}/acoes", json={"acao": "desistir"}
    )
    assert desistiu.status_code == 200, desistiu.text
    assert desistiu.json()["status"] == "cancelado"
    assert dono.get("/api/itens/" + item["id"]).json()["status"] == "disponivel"
    assert ambiente.interesses.find_one({"_id": ObjectId(interesse_segundo["id"])})["status"] == "pendente"

    # Nova seleção e liberação pelo proprietário, que exige motivo.
    assert dono.post(
        f"/api/interesses/{interesse_segundo['id']}/acoes", json={"acao": "selecionar"}
    ).status_code == 200
    sem_motivo = dono.post(
        f"/api/interesses/{interesse_segundo['id']}/acoes", json={"acao": "liberar"}
    )
    assert sem_motivo.status_code == 400
    liberado = dono.post(
        f"/api/interesses/{interesse_segundo['id']}/acoes",
        json={"acao": "liberar", "motivo": "Não compareceu na data combinada"},
    )
    assert liberado.status_code == 200, liberado.text
    assert liberado.json()["status"] == "cancelado"
    assert liberado.json()["motivo"] == "Não compareceu na data combinada"
    assert dono.get("/api/itens/" + item["id"]).json()["status"] == "disponivel"
