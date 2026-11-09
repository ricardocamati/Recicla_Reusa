"""Etapa 19: avisos, indicadores e demonstração coerentes com o diretório público.

Os documentos antigos de descarte são inseridos diretamente em BSON: os comandos
que os criavam foram retirados, e a fixture representa dados históricos, não uso da API.
"""
from datetime import UTC, datetime
from uuid import uuid4

from bson import ObjectId
from fastapi.testclient import TestClient

from app.config import Settings
from tests.test_diretorio_runtime import snapshot
from tests.test_interesses_runtime import ambiente

INSTANTE = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


def _legado(banco, proprietario_id, **campos):
    documento = {
        "_id": ObjectId(),
        "titulo": "Registro histórico de descarte",
        "descricao": "Documento anterior ao diretório",
        "categoria": "notebook",
        "marca": "Marca antiga",
        "modelo": "Modelo antigo",
        "condicao": "sem_conserto",
        "destino": "descarte",
        "status": "disponivel",
        "proprietario_id": proprietario_id,
        "especificacoes": {},
        "historico": [],
        "data_adicao": INSTANTE,
        "data_modificacao": INSTANTE,
    }
    documento.update(campos)
    banco[Settings().mongo_collection_itens].insert_one(documento)
    return documento


def test_indicadores_ignoram_documentos_historicos_de_descarte(ambiente):
    banco = ambiente.banco
    dono = ObjectId()
    _legado(banco, dono, status="disponivel")
    _legado(banco, dono, status="recebido")
    _legado(banco, dono, status="destinacao_informada")
    # O caminho de doados/vendidos/total também não pode aceitar modalidade retirada.
    _legado(banco, dono, status="concluido")
    conta = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.append(conta)
    email = f"pessoa-{uuid4().hex[:8]}@example.test"
    assert conta.post("/api/usuarios", json={
        "nome": "Pessoa indicadores", "email": email, "senha": "Teste12345",
        "endereco": {"logradouro": "Rua Teste", "numero": "1", "cep": "87000000", "cidade": "Maringá"},
    }).status_code == 201
    assert conta.post("/api/auth/login", json={"email": email, "senha": "Teste12345"}).status_code == 200

    indicadores = conta.get("/api/indicadores").json()

    assert indicadores == {
        "doados": 0, "vendidos": 0, "ofertas_ativas": 0, "pendencias": 0, "total": 0,
        "locais_ativos": 0,
    }
    assert "coletados" not in indicadores and "indicados" not in indicadores


def test_consulta_e_gestao_do_diretorio_nao_criam_avisos_nem_mudam_indicadores(ambiente):
    banco = ambiente.banco
    from app.schemas.usuario import PontoColetaProvisionRequest
    from app.services.usuario_service import UsuarioService

    email = f"operador-{uuid4().hex[:8]}@example.test"
    UsuarioService(ambiente.app.state.mongo_repository).provisionar_ponto_coleta(
        PontoColetaProvisionRequest(
            nome="Ponto de Coleta Teste", email=email, senha="Teste12345",
            endereco={"logradouro": "Rua Teste", "numero": "2", "cep": "87000000", "cidade": "Maringá"},
        )
    )
    operador = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.append(operador)
    assert operador.post("/api/auth/login", json={"email": email, "senha": "Teste12345"}).status_code == 200
    avisos_iniciais = list(banco[Settings().mongo_collection_notificacoes].find())
    indicadores_iniciais = operador.get("/api/indicadores").json()
    criado = operador.post("/api/pontos-coleta", json={
        "nome": "Local do teste de avisos",
        "endereco": {"logradouro": "Rua Pública", "numero": "10", "cep": "87000000", "cidade": "Maringá"},
        "categorias_aceitas": ["notebook"], "horario_atendimento": "9h às 17h",
    })
    assert criado.status_code == 201, criado.text
    ponto_id = criado.json()["id"]
    # Cadastrar o local é cadastral: cria aviso nenhum e não mexe em resultados.
    assert list(banco[Settings().mongo_collection_notificacoes].find()) == avisos_iniciais
    apos_cadastro = operador.get("/api/indicadores").json()
    assert apos_cadastro == {**indicadores_iniciais, "locais_ativos": indicadores_iniciais["locais_ativos"] + 1}

    antes_avisos = list(banco[Settings().mongo_collection_notificacoes].find())
    antes_indicadores = operador.get("/api/indicadores").json()
    with TestClient(ambiente.app) as visitante:
        for _ in range(3):
            assert visitante.get("/api/pontos-coleta", params={"cidade": "MARINGÁ"}).status_code == 200
            assert visitante.get(f"/api/pontos-coleta/{ponto_id}").status_code == 200
    assert operador.put(f"/api/pontos-coleta/{ponto_id}", json={
        "nome": "Local atualizado", "horario_atendimento": "10h às 18h",
        "endereco": {"logradouro": "Rua Pública", "numero": "10", "cep": "87000000", "cidade": "Maringá"},
        "categorias_aceitas": ["notebook", "monitor"],
    }).status_code == 200
    assert operador.post(f"/api/pontos-coleta/{ponto_id}/situacao", json={"ativo": False}).status_code == 200
    assert operador.post(f"/api/pontos-coleta/{ponto_id}/situacao", json={"ativo": True}).status_code == 200

    assert list(banco[Settings().mongo_collection_notificacoes].find()) == antes_avisos
    assert operador.get("/api/indicadores").json() == antes_indicadores


def test_locais_ativos_sao_informacao_cadastral_separada(ambiente):
    from app.schemas.indicador import IndicadorResponse
    from app.services.indicador_service import IndicadorService

    banco = ambiente.banco
    pontos = banco[Settings().mongo_collection_pontos_coleta]
    pontos.insert_many([
        {"_id": ObjectId(), "nome": "Local ativo A", "ativo": True, "responsavel_id": ObjectId(),
         "endereco": {"logradouro": "Rua", "numero": "1", "cep": "87000000", "cidade": "Maringá"},
         "categorias_aceitas": ["notebook"], "horario_atendimento": "9h",
         "data_adicao": INSTANTE, "data_modificacao": INSTANTE},
        {"_id": ObjectId(), "nome": "Local ativo B", "ativo": True, "responsavel_id": ObjectId(),
         "endereco": {"logradouro": "Rua", "numero": "2", "cep": "87000000", "cidade": "Maringá"},
         "categorias_aceitas": ["monitor"], "horario_atendimento": "9h",
         "data_adicao": INSTANTE, "data_modificacao": INSTANTE},
        {"_id": ObjectId(), "nome": "Local inativo", "ativo": False, "responsavel_id": ObjectId(),
         "endereco": {"logradouro": "Rua", "numero": "3", "cep": "87000000", "cidade": "Maringá"},
         "categorias_aceitas": ["monitor"], "horario_atendimento": "9h",
         "data_adicao": INSTANTE, "data_modificacao": INSTANTE},
    ])
    indicadores = IndicadorService(ambiente.app.state.mongo_indicador_repository).obter()

    assert indicadores.locais_ativos == 2
    assert indicadores.total == 0
    # A contagem cadastral é explicitamente separada e não entra no total de equipamentos.
    assert set(IndicadorResponse.model_fields) == {
        "doados", "vendidos", "ofertas_ativas", "pendencias", "total", "locais_ativos",
    }


def test_confirmacao_de_oferta_conta_uma_vez_e_consulta_nao_altera_o_total(ambiente):
    banco = ambiente.banco
    dono = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    interessado = TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"})
    ambiente.clientes.extend([dono, interessado])
    contas = {}
    for nome, cliente in (("dono", dono), ("interessado", interessado)):
        email = f"{nome}-{uuid4().hex[:8]}@example.test"
        assert cliente.post("/api/usuarios", json={
            "nome": f"Pessoa {nome}", "email": email, "senha": "Teste12345",
            "endereco": {"logradouro": "Rua Teste", "numero": "3", "cep": "87000000", "cidade": "Maringá"},
        }).status_code == 201
        assert cliente.post("/api/auth/login", json={"email": email, "senha": "Teste12345"}).status_code == 200
        contas[nome] = email
    item = dono.post("/api/itens", json={
        "titulo": "Doação confirmada uma vez", "descricao": "Fixture da etapa 19",
        "categoria": "notebook", "marca": "Marca", "modelo": "Modelo",
        "condicao": "funcional", "destino": "doacao",
    })
    assert item.status_code == 201, item.text
    item_id = item.json()["id"]
    interesse = interessado.post("/api/interesses", json={"item_id": item_id})
    assert interesse.status_code == 201, interesse.text
    assert dono.patch(
        f"/api/interesses/{interesse.json()['id']}", json={"status": "selecionado"}
    ).status_code == 200
    combinacao = interessado.put(
        f"/api/interesses/{interesse.json()['id']}/combinacao",
        json={"local_texto": "Portaria do teste"},
    )
    assert combinacao.status_code == 200, combinacao.text
    revisao = combinacao.json()["combinacao"]["revisao"]
    assert dono.post(
        f"/api/interesses/{interesse.json()['id']}/combinacao/aceite", json={"revisao": revisao}
    ).status_code == 200
    assert dono.post(f"/api/itens/{item_id}/entrega").status_code == 200

    for _ in range(2):
        assert interessado.post(f"/api/itens/{item_id}/recebimento").status_code == 200
    assert dono.get("/api/indicadores").json() == {
        "doados": 1, "vendidos": 0, "ofertas_ativas": 0, "pendencias": 0, "total": 1,
        "locais_ativos": 0,
    }
    antes = snapshot(banco)
    with TestClient(ambiente.app) as visitante:
        for _ in range(3):
            assert visitante.get("/api/pontos-coleta").status_code == 200
    assert snapshot(banco) == antes
    assert dono.get("/api/indicadores").json()["total"] == 1
