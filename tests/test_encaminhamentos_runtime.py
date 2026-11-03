"""Encaminhamento de descarte ao ponto sobre replica set real."""
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
    nome = "teste_encaminhamento_" + uuid4().hex
    monkeypatch.setenv("MONGO_URI", uri)
    monkeypatch.setenv("MONGO_DATABASE", nome)
    monkeypatch.setenv("MONGO_COLLECTION_USUARIOS", "contas_enc")
    monkeypatch.setenv("MONGO_COLLECTION_ITENS", "itens_enc")
    monkeypatch.setenv("MONGO_COLLECTION_PONTOS_COLETA", "pontos_enc")
    monkeypatch.setenv("MONGO_COLLECTION_INTERESSES", "interesses_enc")
    monkeypatch.setenv("MONGO_COLLECTION_NOTIFICACOES", "avisos_enc")
    monkeypatch.setenv("MONGO_COLLECTION_ENCAMINHAMENTOS", "entregas_enc")
    app = criar_app()
    banco = cliente_mongo[nome]
    contexto = SimpleNamespace(
        app=app,
        banco=banco,
        clientes=[],
        itens=banco.itens_enc,
        pontos=banco.pontos_enc,
        avisos=banco.avisos_enc,
        entregas=banco.entregas_enc,
    )
    try:
        with TestClient(app):
            yield contexto
    finally:
        for cliente in contexto.clientes:
            cliente.close()
        assert nome.startswith("teste_encaminhamento_")
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
    servico = UsuarioService(ambiente.app.state.mongo_repository)
    servico.provisionar_ponto_coleta(
        PontoColetaProvisionRequest(
            nome="Operação Teste",
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


def criar_ponto(operador, nome, categorias=("notebook",)):
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
            "categorias_aceitas": list(categorias),
            "horario_atendimento": "Segunda a sexta",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_descarte(cliente, titulo="Geladeira antiga", categoria="eletrodomestico"):
    resposta = cliente.post(
        "/api/itens",
        json={
            "titulo": titulo,
            "descricao": "Descarte guiado",
            "categoria": categoria,
            "marca": "Marca teste",
            "modelo": "Modelo teste",
            "condicao": "sem_conserto",
            "destino": "descarte",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def encaminhar(cliente, item, ponto):
    return cliente.post(
        "/api/encaminhamentos", json={"item_id": item["id"], "ponto_id": ponto["id"]}
    )


def test_descarte_publicado_aguarda_ponto_fora_do_catalogo(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    item = criar_descarte(dono)
    assert item["status"] == "aguardando_ponto"
    catalogo = dono.get("/api/itens").json()
    assert "descarte" not in [linha["destino"] for linha in catalogo]

    resposta = dono.put(
        f"/api/itens/{item['id']}",
        json={
            "titulo": item["titulo"],
            "descricao": item["descricao"],
            "categoria": item["categoria"],
            "marca": item["marca"],
            "modelo": item["modelo"],
            "condicao": item["condicao"],
            "destino": "descarte",
            "status": "disponivel",
        },
    )
    assert resposta.status_code == 400
    assert "encaminhamentos" in resposta.json()["detail"]


def test_encaminhar_exige_ponto_ativo_e_compativel(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    ponto_notebook = criar_ponto(operador, "Ponto Notebook", ["notebook"])
    item = criar_descarte(dono)

    incompativel = encaminhar(dono, item, ponto_notebook)
    assert incompativel.status_code == 409
    assert "categoria" in incompativel.json()["detail"]

    ponto_certo = criar_ponto(operador, "Ponto Eletro", ["eletrodomestico"])
    criado = encaminhar(dono, item, ponto_certo)
    assert criado.status_code == 201, criado.text
    assert criado.json()["status"] == "entrega_prevista"

    documento = ambiente.itens.find_one({"titulo": item["titulo"]})
    assert documento["status"] == "entrega_prevista"
    assert documento["ponto_coleta_id"] is not None

    repetido = encaminhar(dono, item, ponto_certo)
    assert repetido.status_code == 409


def test_categoria_travada_com_entrega_prevista(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    ponto = criar_ponto(operador, "Ponto Fixo", ["eletrodomestico"])
    item = criar_descarte(dono)
    assert encaminhar(dono, item, ponto).status_code == 201

    troca = dono.put(
        f"/api/itens/{item['id']}",
        json={
            "titulo": item["titulo"],
            "descricao": item["descricao"],
            "categoria": "notebook",
            "marca": item["marca"],
            "modelo": item["modelo"],
            "condicao": item["condicao"],
            "destino": "descarte",
        },
    )
    assert troca.status_code == 409
    assert "entrega prevista" in troca.json()["detail"]


def test_cancelar_e_trocar_preservam_historico(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    ponto_a = criar_ponto(operador, "Ponto A", ["eletrodomestico"])
    ponto_b = criar_ponto(operador, "Ponto B", ["eletrodomestico"])
    item = criar_descarte(dono)
    primeiro = encaminhar(dono, item, ponto_a).json()

    troca = dono.post(
        f"/api/encaminhamentos/{primeiro['id']}/acoes",
        json={"acao": "trocar", "novo_ponto_id": ponto_b["id"], "motivo": "Mais perto"},
    )
    assert troca.status_code == 200, troca.text
    assert troca.json()["ponto_id"] == ponto_b["id"]
    assert troca.json()["status"] == "entrega_prevista"

    historico = ambiente.entregas.find_one({"_id": __import__("bson").ObjectId(primeiro["id"])})
    assert historico["status"] == "cancelado"

    cancelado = dono.post(
        f"/api/encaminhamentos/{troca.json()['id']}/acoes", json={"acao": "cancelar"}
    )
    assert cancelado.status_code == 200
    documento = ambiente.itens.find_one({"titulo": item["titulo"]})
    assert documento["status"] == "aguardando_ponto"
    assert documento["ponto_coleta_id"] is None


def test_operador_de_outro_ponto_nao_confirma(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    outro = novo_operador(ambiente, "outro")
    ponto = criar_ponto(operador, "Ponto Correto", ["eletrodomestico"])
    criar_ponto(outro, "Ponto Alheio", ["eletrodomestico"])
    item = criar_descarte(dono)
    entrega = encaminhar(dono, item, ponto).json()

    negado = outro.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes", json={"acao": "receber"}
    )
    assert negado.status_code == 403

    assert dono.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes", json={"acao": "receber"}
    ).status_code == 403

    recebido = operador.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes", json={"acao": "receber"}
    )
    assert recebido.status_code == 200, recebido.text
    assert recebido.json()["status"] == "recebido"
    assert ambiente.itens.find_one({"titulo": item["titulo"]})["status"] == "recebido"
    assert dono.get("/api/indicadores").json()["coletados"] == 1

    repetido = operador.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes", json={"acao": "receber"}
    )
    assert repetido.status_code == 200
    assert dono.get("/api/indicadores").json()["coletados"] == 1


def test_nao_recebido_exige_motivo_e_devolve_item(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    operador = novo_operador(ambiente)
    ponto = criar_ponto(operador, "Ponto Falha", ["eletrodomestico"])
    item = criar_descarte(dono)
    entrega = encaminhar(dono, item, ponto).json()

    sem_motivo = operador.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes", json={"acao": "nao_recebido"}
    )
    assert sem_motivo.status_code == 400

    falha = operador.post(
        f"/api/encaminhamentos/{entrega['id']}/acoes",
        json={"acao": "nao_recebido", "motivo": "Item não corresponde ao descrito"},
    )
    assert falha.status_code == 200, falha.text
    assert falha.json()["status"] == "nao_recebido"
    assert ambiente.itens.find_one({"titulo": item["titulo"]})["status"] == "aguardando_ponto"


def test_ponto_inativado_bloqueia_novos_mas_preserva_previstos(ambiente):
    dono, _ = nova_conta(ambiente, "dono")
    vizinho, _ = nova_conta(ambiente, "vizinho")
    operador = novo_operador(ambiente)
    ponto = criar_ponto(operador, "Ponto Ativo", ["eletrodomestico"])
    item = criar_descarte(dono)
    entrega = encaminhar(dono, item, ponto).json()

    item_vizinho = criar_descarte(vizinho, "Fogão velho")
    inativado = operador.post(
        f"/api/pontos-coleta/{ponto['id']}/situacao", json={"ativo": False}
    )
    assert inativado.status_code == 200
    assert inativado.json()["ativo"] is False

    bloqueado = encaminhar(vizinho, item_vizinho, ponto)
    assert bloqueado.status_code == 409
    assert "inativo" in bloqueado.json()["detail"]

    assert ambiente.entregas.count_documents({"_id": __import__("bson").ObjectId(entrega["id"])}) == 1
    assert dono.get("/api/notificacoes").json()[0]["tipo"] == "ponto_inativado"
