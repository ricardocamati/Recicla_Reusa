"""Leitura do diretório sobre MongoDB real, sem usar a base de demonstração."""
from contextlib import ExitStack

from bson import BSON, ObjectId
from fastapi.testclient import TestClient

from app.config import Settings
from tests.test_diretorio_publico import PUBLICOS
from tests.test_interesses_runtime import ambiente  # fixture: banco exclusivo por UUID
from tests.test_pontos_coleta_v2 import INSTANTE


def snapshot(banco):
    return {
        nome: [BSON.encode(doc) for doc in banco[nome].find().sort("_id", 1)]
        for nome in sorted(banco.list_collection_names())
    }


def test_diretorio_nao_modifica_colecoes_de_ofertas_e_locais(ambiente):
    from scripts.povoar_demonstracao import CONTAS, garantir_conta, povoar, provisionar_operador

    # A própria fixture configura nomes de coleção não padrão no wiring real.
    with ExitStack() as stack:
        provisionar_operador(Settings(), "SenhaTesteDiretorio123!")
        clientes = {
            k: stack.enter_context(TestClient(ambiente.app, headers={"Origin": "http://localhost:5500"}))
            for k in CONTAS
        }
        perfis = {k: garantir_conta(clientes[k], v, "SenhaTesteDiretorio123!") for k, v in CONTAS.items()}
        povoar(clientes, perfis)
        colecao_pontos = ambiente.banco[Settings().mongo_collection_pontos_coleta]
        ponto = colecao_pontos.find_one()
        assert ponto is not None
        # Legado anterior ao campo ativo: preservar sem normalização persistida.
        colecao_pontos.update_one({"_id": ponto["_id"]}, {"$unset": {"ativo": ""}})
        assert len(ambiente.banco.list_collection_names()) == 5
        autenticado = next(iter(clientes.values()))
        indicadores_antes = autenticado.get("/api/indicadores").json()
        antes = snapshot(ambiente.banco)
        with TestClient(ambiente.app) as visitante:
            for _ in range(2):
                lista = visitante.get("/api/pontos-coleta", params={"cidade": ponto["endereco"]["cidade"].upper()})
                assert lista.status_code == 200, lista.text
                assert len(lista.json()) == 1
                assert set(lista.json()[0]) == PUBLICOS
                detalhe = visitante.get(f"/api/pontos-coleta/{ponto['_id']}")
                assert detalhe.status_code == 200 and set(detalhe.json()) == PUBLICOS
                assert not visitante.cookies
                assert visitante.get("/api/pontos-coleta?ativo=false").status_code == 400
                assert visitante.get("/api/usuarios/me").status_code == 401
                assert visitante.get("/api/itens").status_code == 401
                assert visitante.get("/api/pontos-coleta?escopo=meus").status_code == 401
        assert snapshot(ambiente.banco) == antes
        assert autenticado.get("/api/indicadores").json() == indicadores_antes
        assert "ativo" not in colecao_pontos.find_one({"_id": ponto["_id"]})


def test_filtro_real_antes_de_paginar_e_desempate_nome_id(ambiente):
    colecao = ambiente.banco[Settings().mongo_collection_pontos_coleta]
    dono = ObjectId()
    def doc(oid, **extras):
        return {
            "_id": oid, "nome": "Mesmo nome", "responsavel_id": dono,
            "endereco": {"logradouro": "Rua Pública", "numero": "10", "complemento": None, "cep": "87000000", "cidade": "Maringá"},
            "categorias_aceitas": ["notebook"], "horario_atendimento": "8h às 17h", "ativo": True,
            "data_adicao": INSTANTE, "data_modificacao": INSTANTE, **extras,
        }
    # Insere os IDs empatados em ordem inversa à ordem desejada.
    ids = [ObjectId("000000000000000000000003"), ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]
    colecao.insert_many([doc(ObjectId(), nome=f"Anterior {i:03}", categorias_aceitas=["monitor"]) for i in range(105)])
    colecao.insert_one(doc(ObjectId(), nome="Anterior inativo", ativo=False))
    colecao.insert_many([doc(oid, responsavel_id=ObjectId()) for oid in ids])
    antes = snapshot(ambiente.banco)
    with TestClient(ambiente.app) as api:
        resposta = api.get("/api/pontos-coleta", params={"cidade": "  mArInGá  ", "categoria": "notebook", "offset": 1, "limite": 1})
        assert resposta.status_code == 200, resposta.text
        assert [p["id"] for p in resposta.json()] == [str(sorted(ids)[1])]
        completa = api.get("/api/pontos-coleta", params={"cidade": "Maringá", "categoria": "notebook"})
        assert [p["id"] for p in completa.json()] == [str(x) for x in sorted(ids)]
        assert api.get("/api/pontos-coleta?cidade=Londrina").json() == []
        inativo = colecao.find_one({"ativo": False})
        assert api.get(f"/api/pontos-coleta/{inativo['_id']}").status_code == 404
    assert snapshot(ambiente.banco) == antes
