from datetime import UTC, datetime

import mongomock
import pytest

from scripts.migrar_papeis_v2_1 import migrar

AGORA = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)


def usuario(_id: str, tipo: str) -> dict:
    return {
        "_id": mongomock.ObjectId(_id),
        "nome": f"Conta {_id[-4:]}",
        "email": f"{_id}@example.com",
        "tipo": tipo,
        "senha_hash": "x",
        "endereco": {
            "logradouro": "Rua A",
            "numero": "1",
            "complemento": None,
            "cep": "87000000",
            "cidade": "Maringá",
        },
        "data_adicao": AGORA,
        "data_modificacao": AGORA,
    }


def banco_com_legado() -> mongomock.MongoClient:
    cliente = mongomock.MongoClient()
    banco = cliente["teste_migracao"]
    banco["usuarios"].insert_many(
        [usuario("1" * 24, "doador"), usuario("2" * 24, "beneficiario")]
    )
    banco["itens"].insert_one(
        {
            "_id": mongomock.ObjectId("3" * 24),
            "titulo": "Notebook",
            "proprietario_id": mongomock.ObjectId("1" * 24),
            "beneficiario_id": mongomock.ObjectId("2" * 24),
        }
    )
    banco["interesses"].insert_one(
        {
            "_id": mongomock.ObjectId("4" * 24),
            "item_id": mongomock.ObjectId("3" * 24),
            "usuario_id": mongomock.ObjectId("2" * 24),
        }
    )
    return cliente


def test_simulacao_relata_sem_alterar_o_banco() -> None:
    cliente = banco_com_legado()
    banco = cliente["teste_migracao"]

    relatorio = migrar(banco, aplicar=False)

    assert relatorio.encontrados == {"doador": 1, "beneficiario": 1}
    assert relatorio.migrados == 0
    assert relatorio.problemas == []
    assert relatorio.invalidos == []
    assert banco["usuarios"].count_documents({"tipo": "pessoa"}) == 0


def test_aplicacao_troca_perfis_e_preserva_datas() -> None:
    cliente = banco_com_legado()
    banco = cliente["teste_migracao"]

    relatorio = migrar(banco, aplicar=True)

    assert relatorio.migrados == 2
    assert banco["usuarios"].count_documents({"tipo": "pessoa"}) == 2
    assert banco["usuarios"].count_documents({"tipo": {"$in": ["doador", "beneficiario"]}}) == 0
    for documento in banco["usuarios"].find({}):
        # mongomock devolve datetime sem fuso; o valor não é reescrito na migração.
        assert documento["data_adicao"].replace(tzinfo=UTC) == AGORA
        assert documento["data_modificacao"].replace(tzinfo=UTC) == AGORA


def test_segunda_execucao_e_idempotente() -> None:
    banco = banco_com_legado()["teste_migracao"]
    migrar(banco, aplicar=True)

    relatorio = migrar(banco, aplicar=True)

    assert relatorio.migrados == 0
    assert relatorio.encontrados == {}
    assert relatorio.problemas == []


def test_referencia_de_operador_em_item_e_denunciada() -> None:
    cliente = banco_com_legado()
    banco = cliente["teste_migracao"]
    banco["usuarios"].insert_one(usuario("5" * 24, "ponto_coleta"))
    banco["itens"].insert_one(
        {
            "_id": mongomock.ObjectId("6" * 24),
            "titulo": "Monitor",
            "proprietario_id": mongomock.ObjectId("5" * 24),
        }
    )

    relatorio = migrar(banco, aplicar=True)

    assert any("proprietário não-pessoa" in problema for problema in relatorio.problemas)


def test_perfil_desconhecido_e_apontado_como_invalido() -> None:
    banco = banco_com_legado()["teste_migracao"]
    banco["usuarios"].insert_one(usuario("7" * 24, "administrador"))

    relatorio = migrar(banco, aplicar=True)

    assert relatorio.invalidos == ["7" * 24]


@pytest.mark.parametrize("perfil", ["doador", "beneficiario"])
def test_perfis_antigos_contam_como_pessoa_na_simulacao(perfil: str) -> None:
    banco = mongomock.MongoClient()["teste_migracao"]
    banco["usuarios"].insert_one(usuario("8" * 24, perfil))
    banco["itens"].insert_one(
        {
            "_id": mongomock.ObjectId("9" * 24),
            "titulo": "Tablet",
            "proprietario_id": mongomock.ObjectId("8" * 24),
        }
    )

    relatorio = migrar(banco, aplicar=False)

    assert relatorio.problemas == []
