from datetime import UTC, datetime
import os
import uuid

import pytest
from bson import ObjectId
from pymongo import MongoClient

from app.exceptions import InteresseError
from app.models.interesse import Interesse
from app.repositories.mongo_interesse_repository import MongoInteresseRepository


URI = os.environ.get("INTERESSES_TEST_MONGO_URI")
pytestmark = pytest.mark.skipif(not URI, reason="INTERESSES_TEST_MONGO_URI não configurada")


def _participantes(db, *, destino="doacao"):
    dono, interessado = ObjectId(), ObjectId()
    item = ObjectId()
    db.usuarios.insert_many([
        {"_id": dono, "tipo": "pessoa"},
        {"_id": interessado, "tipo": "pessoa"},
    ])
    db.itens.insert_one({
        "_id": item,
        "proprietario_id": dono,
        "destino": destino,
        "status": "disponivel",
        "historico": [],
        "data_adicao": datetime.now(UTC),
        "data_modificacao": datetime.now(UTC),
    })
    return dono, interessado, item


def test_transacao_aceita_e_cancela_doacao_sem_efeito_parcial():
    client = MongoClient(URI, serverSelectionTimeoutMS=3000)
    db_name = f"test_interesses_{uuid.uuid4().hex}"
    db = client[db_name]
    try:
        dono, interessado, item = _participantes(db)
        repo = MongoInteresseRepository(db.interesses, db.itens, db.usuarios)
        agora = datetime(2026, 10, 1, 12, 0, 0, 123456, tzinfo=UTC)
        created = repo.criar(Interesse(str(item), str(interessado), "pendente", agora, agora))

        accepted = repo.decidir(created.id, "aceito", str(dono), agora)
        stored_item = db.itens.find_one({"_id": item})
        stored_interest = db.interesses.find_one({"_id": ObjectId(created.id)})
        assert accepted.status == "aceito"
        assert stored_interest["status"] == "aceito"
        assert stored_item["status"] == "reservado"
        assert stored_item["interesse_aceito_id"] == ObjectId(created.id)
        assert stored_item["data_modificacao"].microsecond % 1000 == 0
        assert stored_item["historico"][-1]["status"] == "reservado"

        canceled = repo.decidir(created.id, "cancelado", str(interessado), agora)
        released = db.itens.find_one({"_id": item})
        assert canceled.status == "cancelado"
        assert released["status"] == "disponivel"
        assert "interesse_aceito_id" not in released
        assert [event["status"] for event in released["historico"]] == ["reservado", "disponivel"]
    finally:
        client.drop_database(db_name)
        client.close()


def test_indice_unico_rejeita_segundo_interesse_do_mesmo_par():
    client = MongoClient(URI, serverSelectionTimeoutMS=3000)
    db_name = f"test_interesses_{uuid.uuid4().hex}"
    db = client[db_name]
    try:
        _, interessado, item = _participantes(db)
        repo = MongoInteresseRepository(db.interesses, db.itens, db.usuarios)
        agora = datetime.now(UTC)
        primeiro = Interesse(str(item), str(interessado), "pendente", agora, agora)
        repo.criar(primeiro)
        segundo = Interesse(str(item), str(interessado), "pendente", agora, agora)
        with pytest.raises(InteresseError) as erro:
            repo.criar(segundo)
        assert erro.value.status_code == 409
        assert db.interesses.count_documents({"item_id": item, "usuario_id": interessado}) == 1
    finally:
        client.drop_database(db_name)
        client.close()
