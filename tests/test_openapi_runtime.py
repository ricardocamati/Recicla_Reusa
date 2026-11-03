from pathlib import Path

from app.main import criar_app

RAIZ = Path(__file__).parents[1]
SNAPSHOT = RAIZ / "docs" / "openapi.json"


def test_snapshot_openapi_corresponde_ao_runtime() -> None:
    from scripts.gerar_openapi import gerar

    assert SNAPSHOT.is_file(), "gere com python scripts/gerar_openapi.py"
    assert SNAPSHOT.read_text(encoding="utf-8") == gerar()


def test_openapi_versionada_cobre_os_contratos_documentados() -> None:
    esquema = criar_app().openapi()
    caminhos = esquema["paths"]

    esperados = {
        "/api/usuarios",
        "/api/usuarios/me",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/itens",
        "/api/itens/{item_id}",
        "/api/interesses",
        "/api/interesses/{interesse_id}",
        "/api/pontos-coleta",
        "/api/pontos-coleta/{ponto_id}",
        "/api/notificacoes",
        "/api/notificacoes/{notificacao_id}",
        "/api/indicadores",
    }
    assert esperados <= set(caminhos)
    assert any("get" in operacoes for operacoes in caminhos.values())
