"""Fluxos completos sobre replica set real; cada caso usa banco próprio por UUID."""
import os
from types import SimpleNamespace
from uuid import uuid4

from datetime import UTC, datetime
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
    monkeypatch.setenv("MONGO_COLLECTION_NOTIFICACOES", "avisos_fluxo")
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


def selecionar(dono, interesse):
    resposta = dono.patch(
        f"/api/interesses/{interesse['id']}", json={"status": "selecionado"}
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def combinar(autor, interesse, local="Portaria do bloco A", previsao=None):
    resposta = autor.put(
        f"/api/interesses/{interesse['id']}/combinacao",
        json={"local_texto": local, "previsao": previsao, "observacao": "Levar documento"},
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def aceitar(contraparte, interesse, revisao=None):
    numero = revisao or interesse["combinacao"]["revisao"]
    resposta = contraparte.post(
        f"/api/interesses/{interesse['id']}/combinacao/aceite", json={"revisao": numero}
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_indicadores_contam_apenas_apos_confirmacao(ambiente):
    dono, _, _ = nova_conta(ambiente, "dono", "pessoa")
    pessoa_a, _, _ = nova_conta(ambiente, "pessoa-a")
    pessoa_b, _, _ = nova_conta(ambiente, "pessoa-b")
    doacao = criar_item(dono)
    revenda = criar_item(dono, destino="revenda", valor=200.0)
    selecionar(dono, pessoa_a.post("/api/interesses", json={"item_id": doacao["id"]}).json())
    selecionar(dono, pessoa_b.post("/api/interesses", json={"item_id": revenda["id"]}).json())

    for item, pessoa in ((doacao, pessoa_a), (revenda, pessoa_b)):
        proposta = combinar(pessoa, {"id": ambiente.interesses.find_one({"item_id": ObjectId(item["id"])})["_id"]})
        assert pessoa.post(
            f"/api/interesses/{proposta['id']}/combinacao/aceite",
            json={"revisao": proposta["combinacao"]["revisao"]},
        ).status_code == 403
        aceitar(dono, proposta)

    antes = dono.get("/api/indicadores").json()
    assert antes == {
        "doados": 0,
        "locais_ativos": 0,
        "ofertas_ativas": 0,
        "pendencias": 2,
        "vendidos": 0,
        "total": 0,
    }

    assert dono.post(f"/api/itens/{doacao['id']}/entrega").status_code == 200
    assert dono.get("/api/indicadores").json()["doados"] == 0
    assert pessoa_a.post(f"/api/itens/{doacao['id']}/recebimento").status_code == 200
    depois = dono.get("/api/indicadores").json()
    assert depois == {
        "doados": 1,
        "locais_ativos": 0,
        "ofertas_ativas": 0,
        "pendencias": 1,
        "vendidos": 0,
        "total": 1,
    }

    assert pessoa_a.post(f"/api/itens/{doacao['id']}/recebimento").status_code == 200
    assert dono.get("/api/indicadores").json()["doados"] == 1


def test_entrega_bilateral_exige_combinacao_e_selecionado(ambiente):
    dono, _, _ = nova_conta(ambiente, "dono", "pessoa")
    selecionado, _, _ = nova_conta(ambiente, "selecionado")
    outro, _, _ = nova_conta(ambiente, "outro")
    item = criar_item(dono)
    interesse = selecionado.post("/api/interesses", json={"item_id": item["id"]}).json()
    externo = outro.post("/api/interesses", json={"item_id": item["id"]}).json()
    selecionar(dono, interesse)

    assert dono.post(f"/api/itens/{item['id']}/entrega").status_code == 409

    proposta = combinar(dono, interesse)
    assert proposta["combinacao"]["aceito_por"] is None
    assert dono.post(
        f"/api/interesses/{interesse['id']}/combinacao/aceite",
        json={"revisao": proposta["combinacao"]["revisao"]},
    ).status_code == 403

    aceito = aceitar(selecionado, proposta)
    assert aceito["combinacao"]["aceito_por"] is not None

    declarado = dono.post(f"/api/itens/{item['id']}/entrega")
    assert declarado.status_code == 200, declarado.text
    assert declarado.json()["status"] == "aguardando_confirmacao"

    assert outro.post(f"/api/itens/{item['id']}/recebimento").status_code == 403
    assert dono.post(f"/api/itens/{item['id']}/recebimento").status_code == 403

    confirmado = selecionado.post(f"/api/itens/{item['id']}/recebimento")
    assert confirmado.status_code == 200, confirmado.text
    assert confirmado.json()["status"] == "concluido"

    encerrados = {str(documento["usuario_id"]): documento for documento in ambiente.interesses.find({})}
    assert encerrados[interesse["usuario_id"]]["resultado"] == "concluido"
    assert encerrados[externo["usuario_id"]]["resultado"] == "item_concluido"
    assert encerrados[externo["usuario_id"]]["status"] == "encerrado"


def test_venda_direta_congela_preco_e_conclui_uma_vez(ambiente):
    dono, _, _ = nova_conta(ambiente, "dono", "pessoa")
    comprador, _, _ = nova_conta(ambiente, "comprador")
    item = criar_item(dono, destino="revenda", valor=300.0)
    interesse = comprador.post("/api/interesses", json={"item_id": item["id"]}).json()
    selecionado = selecionar(dono, interesse)

    assert selecionado["preco_selecionado"] == 300.0
    assert dono.post(f"/api/itens/{item['id']}/entrega").status_code == 409

    primeira = combinar(comprador, interesse, local="Estação central")
    revisada = combinar(dono, interesse, local="Estação central, portão 2")
    assert revisada["combinacao"]["revisao"] == primeira["combinacao"]["revisao"] + 1
    assert revisada["combinacao"]["aceito_por"] is None
    assert comprador.post(
        f"/api/interesses/{interesse['id']}/combinacao/aceite",
        json={"revisao": primeira["combinacao"]["revisao"]},
    ).status_code == 409
    aceitar(comprador, revisada)

    assert dono.post(f"/api/itens/{item['id']}/entrega").status_code == 200
    assert comprador.post(f"/api/itens/{item['id']}/recebimento").status_code == 200
    reenvio = comprador.post(f"/api/itens/{item['id']}/recebimento")
    assert reenvio.status_code == 200
    assert reenvio.json()["status"] == "concluido"
    assert dono.get("/api/indicadores").json()["vendidos"] == 1


def test_referencias_do_fluxo_bloqueiam_exclusao(ambiente):
    dono, dono_id, _ = nova_conta(ambiente, "dono", "pessoa")
    interessado, interessado_id, _ = nova_conta(ambiente, "interessado")
    item = criar_item(dono)
    interesse = interessado.post("/api/interesses", json={"item_id": item["id"]}).json()
    selecionar(dono, interesse)
    proposta = combinar(dono, interesse)
    aceitar(interessado, proposta)
    assert dono.post(f"/api/itens/{item['id']}/entrega").status_code == 200
    assert interessado.post(f"/api/itens/{item['id']}/recebimento").status_code == 200

    excluir_beneficiario = interessado.delete(f"/api/usuarios/{interessado_id}")
    excluir_proprietario = dono.delete(f"/api/usuarios/{dono_id}")

    assert excluir_beneficiario.status_code == 409, excluir_beneficiario.text
    assert excluir_proprietario.status_code == 409, excluir_proprietario.text
    assert ambiente.usuarios.count_documents({"_id": ObjectId(interessado_id)}) == 1
    assert ambiente.usuarios.count_documents({"_id": ObjectId(dono_id)}) == 1
    sem_vinculo, sem_vinculo_id, _ = nova_conta(ambiente, "sem-vinculo")
    excluir_sem_vinculo = sem_vinculo.delete(f"/api/usuarios/{sem_vinculo_id}")

    assert excluir_sem_vinculo.status_code == 204, excluir_sem_vinculo.text
    assert ambiente.usuarios.count_documents({"_id": ObjectId(sem_vinculo_id)}) == 0
