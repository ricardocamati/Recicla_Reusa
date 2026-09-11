from pathlib import Path


RAIZ = Path(__file__).parents[1]


def ler(nome: str) -> str:
    return (RAIZ / nome).read_text(encoding="utf-8")


def test_execucao_docker_possui_imagens_do_backend_e_frontend() -> None:
    assert (RAIZ / "Dockerfile").is_file()
    assert (RAIZ / "frontend" / "Dockerfile").is_file()

    frontend_dockerfile = ler("frontend/Dockerfile")
    assert "FROM python:3.11-slim" in frontend_dockerfile
    assert '"python", "-m", "http.server"' in frontend_dockerfile
    assert '"--directory", "/app"' in frontend_dockerfile
    assert '"--bind", "0.0.0.0"' in frontend_dockerfile
    assert not (RAIZ / "frontend" / "nginx.conf").exists()


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


def test_evidencia_docker_possui_verificador_reprodutivel() -> None:
    caminho = RAIZ / "scripts" / "validar_stack_docker.py"
    assert caminho.is_file()

    script = caminho.read_text(encoding="utf-8")
    assert '"docker", "compose"' in script
    assert "mongosh" in script
    assert "/health" in script
    assert "127.0.0.1:8080" in script

    smoke = RAIZ / "scripts" / "smoke_api_docker.py"
    assert smoke.is_file()
    smoke_script = smoke.read_text(encoding="utf-8")
    assert "HTTPCookieProcessor" in smoke_script
    assert "/api/itens" in smoke_script
    assert "finally" in smoke_script
