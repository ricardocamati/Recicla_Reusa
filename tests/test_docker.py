from pathlib import Path


RAIZ = Path(__file__).parents[1]


def ler(nome: str) -> str:
    return (RAIZ / nome).read_text(encoding="utf-8")


def test_execucao_docker_possui_imagens_do_backend_e_frontend() -> None:
    assert (RAIZ / "Dockerfile").is_file()
    assert (RAIZ / "frontend" / "Dockerfile").is_file()
    assert (RAIZ / "frontend" / "nginx.conf").is_file()


def test_compose_sobe_mongo_backend_e_frontend() -> None:
    compose = ler("compose.yaml")

    for servico in ("mongo:", "backend:", "frontend:"):
        assert f"  {servico}" in compose

    assert "dockerfile: Dockerfile" in compose
    assert "context: ./frontend" in compose
    assert "MONGO_URI:" in compose
    assert "condition: service_healthy" in compose
    assert "BACKEND_PORT" in compose
    assert "FRONTEND_PORT" in compose


def test_documentacao_explica_subida_integrada_em_docker() -> None:
    readme = ler("README.md")

    assert "docker compose up -d --build" in readme
    assert "http://127.0.0.1:8080" in readme
    assert "http://127.0.0.1:8000/health" in readme
    assert "docker compose down" in readme
