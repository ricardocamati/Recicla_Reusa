from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import criar_app
from app.models.usuario import Usuario


class RepositorioEmMemoria:
    def __init__(self) -> None:
        self.usuarios: dict[str, Usuario] = {}
        self.proximo_id = 1

    def criar(self, usuario: Usuario) -> Usuario:
        usuario.id = str(self.proximo_id)
        self.proximo_id += 1
        self.usuarios[usuario.id] = usuario
        return usuario

    def listar(self) -> list[Usuario]:
        return list(self.usuarios.values())

    def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        return self.usuarios.get(usuario_id)

    def atualizar(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id or ""] = usuario
        return usuario

    def excluir(self, usuario_id: str) -> None:
        del self.usuarios[usuario_id]


def cliente() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=criar_app(RepositorioEmMemoria())),
        base_url="http://testserver",
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def payload(**alteracoes: Any) -> dict[str, Any]:
    dados = {
        "nome": "Maria",
        "email": "maria@example.com",
        "tipo": "doador",
        "cidade": "Maringá",
    }
    dados.update(alteracoes)
    return dados


@pytest.mark.anyio
async def test_crud_de_usuarios() -> None:
    async with cliente() as api:
        criado = await api.post("/api/usuarios", json=payload())
        listado = await api.get("/api/usuarios")
        consultado = await api.get("/api/usuarios/1")
        atualizado = await api.put(
            "/api/usuarios/1", json=payload(nome="Maria Silva")
        )
        excluido = await api.delete("/api/usuarios/1")
        ausente = await api.get("/api/usuarios/1")

    assert criado.status_code == 201
    assert criado.headers["location"] == "/api/usuarios/1"
    assert listado.json()[0]["nome"] == "Maria"
    assert consultado.json()["email"] == "maria@example.com"
    assert atualizado.json()["nome"] == "Maria Silva"
    assert excluido.status_code == 204
    assert ausente.status_code == 404


@pytest.mark.anyio
async def test_validacao_de_usuario_retorna_400() -> None:
    async with cliente() as api:
        resposta = await api.post("/api/usuarios", json=payload(email="invalido"))

    assert resposta.status_code == 400
    assert "email" in resposta.json()["fieldErrors"]
