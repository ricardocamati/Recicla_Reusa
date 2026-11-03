"""Notificações sobre replica set real; cada caso usa banco próprio por UUID."""
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.main import criar_app
from app.models.notificacao import EventoNotificacao
from app.repositories.notificacao_documento import montar_documento, registrar


@pytest.fixture
def ambiente(monkeypatch):
    uri = os.environ.get("INTERESSES_TEST_MONGO_URI")
    if not uri:
        pytest.skip("defina INTERESSES_TEST_MONGO_URI para executar contra replica set real")
    cliente_mongo = MongoClient(uri, serverSelectionTimeoutMS=5000)
    assert cliente_mongo.admin.command("hello").get("setName"), "teste exige replica set"
    nome = "teste_notificacoes_runtime_" + uuid4().hex
    assert nome not in cliente_mongo.list_database_names()
    monkeypatch.setenv("MONGO_URI", uri)
    monkeypatch.setenv("MONGO_DATABASE", nome)
    monkeypatch.setenv("MONGO_COLLECTION_USUARIOS", "participantes_aviso")
    monkeypatch.setenv("MONGO_COLLECTION_ITENS", "equipamentos_aviso")
    monkeypatch.setenv("MONGO_COLLECTION_PONTOS_COLETA", "locais_aviso")
    monkeypatch.setenv("MONGO_COLLECTION_INTERESSES", "solicitacoes_aviso")
    monkeypatch.setenv("MONGO_COLLECTION_NOTIFICACOES", "avisos_teste")
    app = criar_app()
    banco = cliente_mongo[nome]
    contexto = SimpleNamespace(
        app=app,
        banco=banco,
        clientes=[],
        usuarios=banco.participantes_aviso,
        itens=banco.equipamentos_aviso,
        interesses=banco.solicitacoes_aviso,
        avisos=banco.avisos_teste,
    )
    try:
        with TestClient(app):
            yield contexto
    finally:
        for cliente in contexto.clientes:
            cliente.close()
        assert nome.startswith("teste_notificacoes_runtime_")
        cliente_mongo.drop_database(nome)
        assert nome not in cliente_mongo.list_database_names()
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
    assert (
        cliente.post(
            "/api/auth/login", json={"email": email, "senha": "Teste12345"}
        ).status_code
        == 200
    )
    return cliente, resposta.json()["id"]


def criar_item(cliente, **alteracoes):
    dados = {
        "titulo": "Notebook avisado",
        "descricao": "Fixture isolada",
        "categoria": "notebook",
        "marca": "Marca teste",
        "modelo": "Modelo teste",
        "condicao": "funcional",
        "destino": "doacao",
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


def test_decisao_do_interesse_notifica_o_interessado(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, interessado_id = nova_conta(ambiente, "interessado")
    aceito_item = criar_item(dono)
    recusado_item = criar_item(dono, titulo="Segundo notebook")
    aceite = interessado.post("/api/interesses", json={"item_id": aceito_item["id"]}).json()
    recusa = interessado.post(
        "/api/interesses", json={"item_id": recusado_item["id"]}
    ).json()

    assert dono.patch(
        f"/api/interesses/{aceite['id']}", json={"status": "selecionado"}
    ).status_code == 200
    assert dono.patch(
        f"/api/interesses/{recusa['id']}", json={"status": "recusado"}
    ).status_code == 200

    avisos = interessado.get("/api/notificacoes").json()
    tipos = sorted(aviso["tipo"] for aviso in avisos)
    assert tipos == ["interesse_aceito", "interesse_recusado"]
    assert all(aviso["usuario_id"] == interessado_id for aviso in avisos)
    assert all(aviso["lida"] is False for aviso in avisos)
    assert {aviso["item_id"] for aviso in avisos} == {
        aceito_item["id"],
        recusado_item["id"],
    }


def test_aceite_notifica_os_demais_interessados_da_reserva(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    escolhido, _ = nova_conta(ambiente, "escolhido")
    outro, _ = nova_conta(ambiente, "outro")
    item = criar_item(dono)
    do_escolhido = escolhido.post("/api/interesses", json={"item_id": item["id"]}).json()
    outro.post("/api/interesses", json={"item_id": item["id"]})

    dono.patch(f"/api/interesses/{do_escolhido['id']}", json={"status": "selecionado"})

    avisos_escolhido = escolhido.get("/api/notificacoes").json()
    avisos_outro = outro.get("/api/notificacoes").json()
    assert [aviso["tipo"] for aviso in avisos_escolhido] == ["interesse_aceito"]
    assert [aviso["tipo"] for aviso in avisos_outro] == ["status_item_alterado"]
    assert "reservado" in avisos_outro[0]["mensagem"]


def test_cancelamento_do_interessado_notifica_o_proprietario(ambiente):
    dono, dono_id = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()

    assert interessado.patch(
        f"/api/interesses/{interesse['id']}", json={"status": "cancelado"}
    ).status_code == 200

    avisos = dono.get("/api/notificacoes").json()
    assert [aviso["tipo"] for aviso in avisos] == ["interesse_cancelado"]
    assert avisos[0]["usuario_id"] == dono_id


def test_mudanca_de_status_e_conclusao_notificam_quem_tem_interesse(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    assert dono.patch(
        f"/api/interesses/{interesse['id']}", json={"status": "selecionado"}
    ).status_code == 200
    proposta = dono.put(
        f"/api/interesses/{interesse['id']}/combinacao",
        json={"local_texto": "Portaria", "observacao": None},
    ).json()
    assert interessado.post(
        f"/api/interesses/{interesse['id']}/combinacao/aceite",
        json={"revisao": proposta["combinacao"]["revisao"]},
    ).status_code == 200

    assert dono.post(f"/api/itens/{item['id']}/entrega").status_code == 200
    assert dono.get("/api/indicadores").json()["doados"] == 0
    assert interessado.post(f"/api/itens/{item['id']}/recebimento").status_code == 200

    avisos = interessado.get("/api/notificacoes").json()
    assert sorted(aviso["tipo"] for aviso in avisos) == [
        "entrega_declarada",
        "interesse_aceito",
        "item_concluido",
    ]
    assert {aviso["item_id"] for aviso in avisos} == {item["id"]}
    assert avisos[0]["tipo"] == "item_concluido"
    assert "concluído" in avisos[0]["mensagem"]


def test_listagem_e_leitura_sao_restritas_ao_destinatario(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    terceiro, _ = nova_conta(ambiente, "terceiro")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "selecionado"})

    avisos = interessado.get("/api/notificacoes").json()
    assert len(avisos) == 1
    aviso = avisos[0]
    assert terceiro.get("/api/notificacoes").json() == []
    negado = terceiro.patch(f"/api/notificacoes/{aviso['id']}", json={"lida": True})
    lido = interessado.patch(f"/api/notificacoes/{aviso['id']}", json={"lida": True})
    ilegivel = interessado.patch("/api/notificacoes/abc", json={"lida": True})
    nao_lida = interessado.get("/api/notificacoes", params={"lida": "false"}).json()
    lidas = interessado.get("/api/notificacoes", params={"lida": "true"}).json()

    assert negado.status_code == 404, negado.text
    assert lido.status_code == 200, lido.text
    assert lido.json()["lida"] is True
    assert lido.json()["data_leitura"] is not None
    assert lido.json()["data_adicao"] == aviso["data_adicao"]
    assert lido.json()["data_modificacao"] >= aviso["data_modificacao"]
    assert ilegivel.status_code == 404, ilegivel.text
    assert nao_lida == []
    assert [lida["id"] for lida in lidas] == [aviso["id"]]


def test_evento_repetido_nao_duplica_aviso(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, interessado_id = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "selecionado"})
    assert ambiente.avisos.count_documents({}) == 1

    evento = EventoNotificacao(
        tipo="interesse_aceito",
        titulo="Interesse aceito",
        mensagem="Seu interesse no item foi aceito.",
        evento_id=f"interesse:{interesse['id']}:aceito",
    )
    from datetime import UTC, datetime

    documento = montar_documento(
        usuario_id=interessado_id,
        item_id=item["id"],
        interesse_id=interesse["id"],
        evento=evento,
        instante=datetime.now(UTC),
    )
    registrar(ambiente.avisos, documento)
    registrar(ambiente.avisos, documento)

    filtro = {"usuario_id": ObjectId(interessado_id), "evento_id": evento.evento_id}
    assert ambiente.avisos.count_documents(filtro) == 1
    assert ambiente.avisos.count_documents({}) == 1


def test_usuario_sem_interesse_nao_recebe_aviso(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    sem_interesse, _ = nova_conta(ambiente, "sem-interesse")
    item = criar_item(dono, destino="revenda", valor=100.0)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "selecionado"})
    proposta = dono.put(
        f"/api/interesses/{interesse['id']}/combinacao",
        json={"local_texto": "Estação", "observacao": None},
    ).json()
    interessado.post(
        f"/api/interesses/{interesse['id']}/combinacao/aceite",
        json={"revisao": proposta["combinacao"]["revisao"]},
    )
    assert dono.post(f"/api/itens/{item['id']}/entrega").status_code == 200

    avisos = interessado.get("/api/notificacoes").json()
    assert [aviso["tipo"] for aviso in avisos] == [
        "entrega_declarada",
        "interesse_aceito",
    ]
    assert sem_interesse.get("/api/notificacoes").json() == []
    assert dono.get("/api/notificacoes").json() == []


def test_falha_ao_registrar_aviso_desfaz_a_declaracao(ambiente, monkeypatch):
    import app.repositories.mongo_item_repository as modulo

    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "selecionado"})
    proposta = dono.put(
        f"/api/interesses/{interesse['id']}/combinacao",
        json={"local_texto": "Portaria", "observacao": None},
    ).json()
    interessado.post(
        f"/api/interesses/{interesse['id']}/combinacao/aceite",
        json={"revisao": proposta["combinacao"]["revisao"]},
    )

    def falhar(*args, **kwargs):
        raise RuntimeError("falha controlada")

    monkeypatch.setattr(modulo, "registrar", falhar)
    with pytest.raises(RuntimeError):
        dono.post(f"/api/itens/{item['id']}/entrega")

    documento = ambiente.itens.find_one({"_id": ObjectId(item["id"])})
    assert documento["status"] == "reservado"
    assert documento["historico"][-1]["status"] == "reservado"
    assert ambiente.avisos.count_documents({}) == 1  # apenas o aviso da seleção


def test_api_rejeita_parametro_extra_e_corpo_invalido(ambiente):
    dono, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    dono.patch(f"/api/interesses/{interesse['id']}", json={"status": "selecionado"})
    aviso = interessado.get("/api/notificacoes").json()[0]

    extra = interessado.get("/api/notificacoes", params={"desconhecido": "1"})
    invalido = interessado.patch(f"/api/notificacoes/{aviso['id']}", json={"lida": False})
    inexistente = interessado.patch("/api/notificacoes/abc", json={"lida": True})

    assert extra.status_code == 400, extra.text
    assert extra.json()["detail"][0]["type"] == "extra_forbidden"
    assert invalido.status_code == 400, invalido.text
    assert inexistente.status_code == 404, inexistente.text
