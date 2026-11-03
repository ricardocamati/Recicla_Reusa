"""Pré-requisitos da reserva transacional na stack entregue."""
from pathlib import Path

from app.config import Settings

RAIZ = Path(__file__).parents[1]


def test_colecao_de_interesses_e_configuravel(monkeypatch):
    monkeypatch.setenv("MONGO_COLLECTION_INTERESSES", "pedidos_teste")
    assert Settings(_env_file=None).mongo_collection_interesses == "pedidos_teste"


def test_stack_prepara_replica_set_para_reserva_transacional():
    compose = (RAIZ / "compose.yaml").read_text(encoding="utf-8")
    assert "/opt/recicla-mongo/entrypoint.sh" in compose
    assert "/opt/recicla-mongo/healthcheck.js" in compose
    entrada = (RAIZ / "docker/mongo/entrypoint.sh").read_text(encoding="utf-8")
    assert "--replSet rs0" in entrada
    assert "--keyFile" in entrada
    assert "docker-entrypoint.sh" in entrada


def test_healthcheck_exige_primary_sem_reconfigurar_replica_existente():
    script = (RAIZ / "docker/mongo/healthcheck.js").read_text(encoding="utf-8")
    assert "isWritablePrimary" in script
    assert "NotYetInitialized" in script
    assert "rs.initiate" in script
    assert "rs.reconfig" not in script
