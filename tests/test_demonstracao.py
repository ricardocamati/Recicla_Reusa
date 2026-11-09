"""Segurança e repetibilidade do povoamento; transporte isolado nos testes unitários."""
import httpx
import pytest
import os
from uuid import uuid4
from contextlib import ExitStack


@pytest.mark.parametrize("ampliar", [False, True])
def test_povoamento_real_e_reexecucao_sem_duplicar(monkeypatch, ampliar):
    uri = os.environ.get("INTERESSES_TEST_MONGO_URI")
    if not uri:
        pytest.skip("defina INTERESSES_TEST_MONGO_URI para integração do povoamento")
    from pymongo import MongoClient
    from fastapi.testclient import TestClient
    from app.main import criar_app
    from scripts.povoar_demonstracao import CONTAS, garantir_conta, provisionar_operador, povoar

    banco_nome = "teste_demo_" + uuid4().hex
    monkeypatch.setenv("MONGO_URI", uri)
    monkeypatch.setenv("MONGO_DATABASE", banco_nome)
    for nome in ("USUARIOS", "ITENS", "PONTOS_COLETA", "INTERESSES", "NOTIFICACOES"):
        monkeypatch.delenv("MONGO_COLLECTION_" + nome, raising=False)
    from app.config import Settings
    settings = Settings()
    with MongoClient(uri, serverSelectionTimeoutMS=5000) as mongo:
        assert banco_nome not in mongo.list_database_names()
        banco = mongo[banco_nome]
        try:
            with ExitStack() as stack:
                app = criar_app()
                stack.enter_context(TestClient(app))
                provisionar_operador(settings, "SenhaDemo123!")
                clientes = {k: stack.enter_context(TestClient(app, headers={"Origin": "http://localhost:5500"})) for k in CONTAS}
                perfis = {k: garantir_conta(clientes[k], v, "SenhaDemo123!") for k, v in CONTAS.items()}
                banco.sentinela.insert_one({"registro": "preservar"})
                resultado = povoar(clientes, perfis)
                assert len(resultado["itens"]) == 8
                assert banco.itens.count_documents({}) == 8
                assert banco.interesses.count_documents({}) == 5
                assert set(banco.itens.distinct("destino")) == {"doacao", "revenda"}
                assert resultado["indicadores"] == {"ofertas_ativas": 3, "pendencias": 2, "doados": 1, "vendidos": 1, "total": 2, "locais_ativos": 1}
                antes = {n: list(banco[n].find().sort("_id")) for n in banco.list_collection_names()}
                segundo = povoar(clientes, perfis)
                depois = {n: list(banco[n].find().sort("_id")) for n in banco.list_collection_names()}
                assert resultado == segundo
                assert antes == depois
                if ampliar:
                    from scripts.povoar_demonstracao import CONTAS_EXTRAS, povoar_ampliado
                    for chave, conta in CONTAS_EXTRAS.items():
                        clientes[chave] = stack.enter_context(TestClient(app, headers={"Origin": "http://localhost:5500"}))
                        perfis[chave] = garantir_conta(clientes[chave], conta, "SenhaDemo123!")
                    expandido = povoar_ampliado(clientes, perfis)
                    assert len(expandido["itens"]) == 48
                    assert banco.itens.count_documents({}) == 56
                    assert banco.usuarios.count_documents({}) == 8
                    assert banco.pontos_coleta.count_documents({}) == 3
                    assert banco.interesses.count_documents({}) == 53
                    assert set(banco.itens.distinct("destino")) == {"doacao", "revenda"}
                    assert len(banco.itens.distinct("categoria")) >= 10
                    assert len(banco.usuarios.distinct("endereco.cidade")) >= 3
                    assert expandido["indicadores"] == {"ofertas_ativas": 27, "pendencias": 14, "doados": 7, "vendidos": 7, "total": 14, "locais_ativos": 3}
                    for nome, documentos in antes.items():
                        for documento in documentos:
                            assert banco[nome].find_one({"_id": documento["_id"]}) == documento
                    snapshot = {n: list(banco[n].find().sort("_id")) for n in banco.list_collection_names()}
                    assert povoar_ampliado(clientes, perfis) == expandido
                    assert snapshot == {n: list(banco[n].find().sort("_id")) for n in banco.list_collection_names()}
        finally:
            mongo.drop_database(banco_nome)
            assert banco_nome not in mongo.list_database_names()


def test_manifesto_so_contem_ofertas_e_nao_tem_cenarios_legados(monkeypatch):
    from scripts import povoar_demonstracao as demo
    assert {c[2] for c in demo.CENARIOS} <= {"doacao", "revenda"}
    lotes = []
    def registrar(*args, cenarios, **kwargs):
        lotes.extend(cenarios)
        return {"itens": {c[1]: {} for c in cenarios}}
    monkeypatch.setattr(demo, "povoar", registrar)
    monkeypatch.setattr(demo, "listar_todos", lambda *a, **k: [])
    monkeypatch.setattr(demo, "garantir_registro", lambda *a, **k: {"id": str(len(lotes))})
    monkeypatch.setattr(demo, "chamar", lambda *a, **k: {})
    demo.povoar_ampliado({"ana": object(), "operador": object()}, {"operador": {"id": "operador"}})
    assert len(lotes) == 48
    assert {c[2] for c in lotes} <= {"doacao", "revenda"}
    assert {c[3] for c in lotes} <= {"disponivel", "reservado", "aguardando_confirmacao", "concluido"}


@pytest.mark.parametrize("contrato_atual", [True, False])
def test_cli_aplicar_confere_rotas_atuais_sem_depender_do_fluxo_removido(monkeypatch, capsys, contrato_atual):
    import secrets
    from scripts import povoar_demonstracao as demo
    from app import config
    from types import SimpleNamespace
    monkeypatch.setenv("DEMO_SENHA", secrets.token_urlsafe(16))
    monkeypatch.setattr(config, "Settings", lambda: SimpleNamespace())
    rotas = {"/api/itens": {}, "/api/interesses": {}, "/api/pontos-coleta": {}} if contrato_atual else {}
    chamadas = []
    def responder(req):
        chamadas.append(req.url.path)
        if req.url.path == "/openapi.json":
            return httpx.Response(200, json={"paths": rotas})
        assert req.url.path == "/api/auth/login"
        return httpx.Response(401, json={"detail": "sem sessão"})
    original = httpx.Client
    monkeypatch.setattr(demo.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(responder), **kw))
    provisionados = []
    def provisionar(*a):
        provisionados.append(True)
        return "operador"
    monkeypatch.setattr(demo, "provisionar_operador", provisionar)
    monkeypatch.setattr(demo, "garantir_conta", lambda *a: {"id": "operador"})
    monkeypatch.setattr(demo, "povoar", lambda *a: {"itens": {}})
    assert demo.main(["--aplicar"]) == (0 if contrato_atual else 1)
    assert bool(provisionados) == contrato_atual
    assert chamadas == (["/openapi.json", "/api/auth/login"] if contrato_atual else ["/openapi.json"])
    capsys.readouterr()


def test_cli_sem_aplicar_apenas_descreve_carga(monkeypatch, capsys):
    from scripts.povoar_demonstracao import main

    monkeypatch.delenv("DEMO_SENHA", raising=False)
    assert main([]) == 0
    assert "--aplicar" in capsys.readouterr().out


def test_cli_aplicar_exige_senha_sem_revelar_segredos(monkeypatch, capsys):
    from scripts.povoar_demonstracao import main

    monkeypatch.delenv("DEMO_SENHA", raising=False)
    assert main(["--aplicar"]) == 1
    assert "DEMO_SENHA" in capsys.readouterr().err


def test_conta_criada_e_relida_pela_sessao():
    from scripts.povoar_demonstracao import garantir_conta

    chamadas = []
    perfil = {"id": "pessoa-1", "nome": "Ana Demo", "email": "ana@example.test", "tipo": "pessoa"}

    def responder(request):
        chamadas.append((request.method, request.url.path))
        if request.url.path == "/api/auth/login":
            return httpx.Response(401 if len(chamadas) == 1 else 200, json={})
        if request.method == "POST":
            return httpx.Response(201, json=perfil)
        return httpx.Response(200, json=perfil)

    with httpx.Client(base_url="http://teste", transport=httpx.MockTransport(responder)) as cliente:
        assert garantir_conta(cliente, perfil, "senha-teste")["id"] == "pessoa-1"
    assert chamadas == [("POST", "/api/auth/login"), ("POST", "/api/usuarios"),
                        ("POST", "/api/auth/login"), ("GET", "/api/usuarios/me")]


@pytest.mark.parametrize("modo", ["identidade_errada", "senha_incorreta"])
def test_conta_alheia_ou_conflito_nao_sao_adotados(modo):
    from scripts.povoar_demonstracao import DemonstracaoError, garantir_conta

    def responder(request):
        if request.url.path == "/api/auth/login":
            return httpx.Response(401 if modo == "senha_incorreta" else 200, json={})
        if request.method == "POST":
            return httpx.Response(409, json={})
        return httpx.Response(200, json={"id": "alheio", "email": "outro@example.test", "nome": "Outro", "tipo": "pessoa"})

    with httpx.Client(base_url="http://teste", transport=httpx.MockTransport(responder)) as cliente:
        with pytest.raises(DemonstracaoError):
            garantir_conta(cliente, {"nome": "Ana Demo", "email": "ana@example.test", "tipo": "pessoa"}, "senha-teste")


def test_registro_existente_e_relido_sem_duplicar():
    from scripts.povoar_demonstracao import garantir_registro

    registro = {"id": "i1", "titulo": "Demo", "descricao": "marca", "proprietario_id": "u1"}
    metodos = []

    def responder(request):
        metodos.append(request.method)
        return httpx.Response(200, json=registro)

    with httpx.Client(base_url="http://teste", transport=httpx.MockTransport(responder)) as cliente:
        encontrado = garantir_registro(cliente, "/api/itens", [registro], {"titulo": "Demo", "descricao": "marca"}, "proprietario_id", "u1")
    assert encontrado == registro
    assert metodos == ["GET"]


@pytest.mark.parametrize("quantidade,dono", [(1, "alheio"), (2, "u1")])
def test_registro_alheio_ou_ambiguo_interrompe_sem_escrever(quantidade, dono):
    from scripts.povoar_demonstracao import DemonstracaoError, garantir_registro

    registros = [{"id": str(i), "titulo": "Demo", "descricao": "marca", "proprietario_id": dono} for i in range(quantidade)]
    with httpx.Client(base_url="http://teste", transport=httpx.MockTransport(lambda r: pytest.fail("não deveria escrever"))) as cliente:
        with pytest.raises(DemonstracaoError):
            garantir_registro(cliente, "/api/itens", registros, {"titulo": "Demo", "descricao": "marca"}, "proprietario_id", "u1")


def test_listagem_percorre_paginas_antes_de_concluir_ausencia():
    from scripts.povoar_demonstracao import listar_todos

    offsets = []

    def responder(request):
        offset = int(request.url.params["offset"])
        offsets.append(offset)
        registros = [{"id": str(i)} for i in range(205)]
        return httpx.Response(200, json=registros[offset:offset + 100])

    with httpx.Client(base_url="http://teste", transport=httpx.MockTransport(responder)) as cliente:
        registros = listar_todos(cliente, "/api/itens/meus")
    assert len(registros) == 205
    assert offsets == [0, 100, 200]


@pytest.mark.parametrize("existente", [False, True])
def test_ponto_e_relido_no_escopo_protegido_sem_misturar_query_e_path(existente):
    from scripts.povoar_demonstracao import garantir_registro

    ponto = {"id": "p1", "nome": "Local demo", "responsavel_id": "operador-1"}
    chamadas = []
    def responder(request):
        chamadas.append((request.method, request.url.path, dict(request.url.params)))
        if request.method == "POST":
            assert request.url.path == "/api/pontos-coleta"
            assert not request.url.params
            return httpx.Response(201, json=ponto)
        assert request.url.path == "/api/pontos-coleta/p1"
        assert request.url.params.get("escopo") == "meus"
        return httpx.Response(200, json=ponto)

    with httpx.Client(base_url="http://teste", transport=httpx.MockTransport(responder)) as cliente:
        resposta = garantir_registro(
            cliente, "/api/pontos-coleta", [ponto] if existente else [],
            {"nome": "Local demo"}, "responsavel_id", "operador-1",
            parametros_leitura={"escopo": "meus"},
        )
    assert resposta == ponto
    assert len(chamadas) == (1 if existente else 2)
