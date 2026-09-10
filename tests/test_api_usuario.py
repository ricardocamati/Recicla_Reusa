from datetime import UTC, datetime
from collections.abc import Callable
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

    def buscar_por_email(self, email: str) -> Usuario | None:
        return next((u for u in self.usuarios.values() if u.email == email), None)

    def atualizar(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id or ""] = usuario
        return usuario

    def excluir(self, usuario_id: str) -> None:
        del self.usuarios[usuario_id]


@pytest.fixture
def repositorio() -> RepositorioEmMemoria:
    return RepositorioEmMemoria()


@pytest.fixture
def instante() -> datetime:
    return datetime(2026, 9, 8, 12, 0, tzinfo=UTC)


def cliente(
    repositorio: RepositorioEmMemoria,
    instante: datetime | Callable[[], datetime],
) -> AsyncClient:
    relogio = instante if callable(instante) else lambda: instante
    return AsyncClient(
        transport=ASGITransport(
            app=criar_app(repositorio, relogio=relogio),
        ),
        base_url="http://testserver",
        headers={"Origin": "http://localhost:5500"},
    )


def payload(**alteracoes: Any) -> dict[str, Any]:
    dados = {
        "nome": "Maria da Silva",
        "email": "maria@example.com",
        "senha": "Senha123",
        "tipo": "doador",
        "endereco": {
            "logradouro": "Avenida Brasil",
            "numero": "1200",
            "complemento": "Sala 3",
            "cep": "87000-000",
            "cidade": "Maringá",
        },
    }
    dados.update(alteracoes)
    return dados


@pytest.mark.anyio
async def test_cadastro_persiste_endereco_datas_e_nao_expoe_senha(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        resposta = await api.post("/api/usuarios", json=payload())

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["endereco"]["cep"] == "87000000"
    assert corpo["data_adicao"] == corpo["data_modificacao"]
    assert "senha" not in corpo
    assert "senha_hash" not in corpo
    persistido = next(iter(repositorio.usuarios.values()))
    assert persistido.endereco.cidade == "Maringá"
    assert persistido.senha_hash != "Senha123"


@pytest.mark.anyio
async def test_listagem_de_terceiros_expoe_somente_resumo_publico(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        criado = await api.post("/api/usuarios", json=payload())
        listado = await api.get("/api/usuarios")
        consultado = await api.get(f"/api/usuarios/{criado.json()['id']}")

    assert listado.status_code == 200
    assert set(listado.json()[0]) == {"id", "nome", "tipo", "cidade"}
    assert consultado.status_code == 200
    assert set(consultado.json()) == {"id", "nome", "tipo", "cidade"}


@pytest.mark.anyio
async def test_atualizacao_autenticada_preserva_tipo_e_data_adicao(
    repositorio: RepositorioEmMemoria,
) -> None:
    instantes = iter(
        [
            datetime(2026, 9, 8, 12, 0, tzinfo=UTC),
            datetime(2026, 9, 8, 12, 1, tzinfo=UTC),
        ]
    )
    async with cliente(repositorio, lambda: next(instantes, datetime(2026, 9, 8, 12, 1, tzinfo=UTC))) as api:
        criado = await api.post("/api/usuarios", json=payload())
        await api.post("/api/auth/login", json={"email": "maria@example.com", "senha": "Senha123"})
        atualizado = await api.put(
            f"/api/usuarios/{criado.json()['id']}",
            json={
                "nome": "Maria Silva Atualizada",
                "email": "maria.atualizada@example.com",
                "endereco": {
                    "logradouro": "Rua Nova",
                    "numero": "10",
                    "cep": "87000001",
                    "cidade": "Sarandi",
                },
            },
        )

    assert atualizado.status_code == 200
    corpo = atualizado.json()
    assert corpo["tipo"] == "doador"
    assert corpo["data_adicao"] == "2026-09-08T12:00:00Z"
    assert corpo["data_modificacao"] == "2026-09-08T12:01:00Z"
    assert corpo["endereco"]["cep"] == "87000001"


@pytest.mark.anyio
async def test_atualizacao_de_outro_usuario_retorna_403(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        primeiro = await api.post("/api/usuarios", json=payload())
        segundo = await api.post(
            "/api/usuarios",
            json=payload(email="joao@example.com", nome="João da Silva"),
        )
        await api.post("/api/auth/login", json={"email": "maria@example.com", "senha": "Senha123"})
        resposta = await api.put(
            f"/api/usuarios/{segundo.json()['id']}",
            json={
                "nome": "Alteração indevida",
                "email": "joao.novo@example.com",
                "endereco": payload()["endereco"],
            },
        )

    assert primeiro.status_code == 201
    assert resposta.status_code == 403
    assert repositorio.usuarios[segundo.json()["id"]].nome == "João da Silva"


@pytest.mark.anyio
async def test_login_me_logout_e_sessao_http_only(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        await api.post("/api/usuarios", json=payload())
        login = await api.post(
            "/api/auth/login",
            json={"email": "MARIA@EXAMPLE.COM", "senha": "Senha123"},
        )
        perfil = await api.get("/api/usuarios/me")
        logout = await api.post("/api/auth/logout")
        depois = await api.get("/api/usuarios/me")

    assert login.status_code == 200
    assert "senha" not in login.json()
    assert "recicla_sessao" in login.cookies
    cookie = login.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "max-age=1800" in cookie
    assert perfil.status_code == 200
    assert perfil.json()["email"] == "maria@example.com"
    assert logout.status_code == 204
    assert depois.status_code == 401


@pytest.mark.anyio
async def test_login_invalido_tem_resposta_generica(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        await api.post("/api/usuarios", json=payload())
        senha_errada = await api.post(
            "/api/auth/login",
            json={"email": "maria@example.com", "senha": "Errada123"},
        )
        email_inexistente = await api.post(
            "/api/auth/login",
            json={"email": "naoexiste@example.com", "senha": "Errada123"},
        )

    assert senha_errada.status_code == email_inexistente.status_code == 401
    assert senha_errada.json()["detail"] == email_inexistente.json()["detail"]
    assert "recicla_sessao" not in senha_errada.cookies


@pytest.mark.anyio
async def test_cadastro_rejeita_ponto_de_coleta_e_email_duplicado(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        primeiro = await api.post("/api/usuarios", json=payload())
        duplicado = await api.post(
            "/api/usuarios",
            json=payload(email="MARIA@EXAMPLE.COM"),
        )
        ponto = await api.post(
            "/api/usuarios",
            json=payload(email="coleta@example.com", tipo="ponto_coleta"),
        )

    assert primeiro.status_code == 201
    assert duplicado.status_code == 409
    assert ponto.status_code == 400


@pytest.mark.anyio
async def test_cadastro_rejeita_endereco_e_senha_invalidos(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        endereco = await api.post(
            "/api/usuarios",
            json=payload(endereco={"logradouro": "Rua A", "numero": "1", "cep": "123", "cidade": "Maringá"}),
        )
        senha = await api.post(
            "/api/usuarios",
            json=payload(email="senha@example.com", senha="curta"),
        )

    assert endereco.status_code == 400
    assert senha.status_code == 400
    assert "cep" in str(endereco.json()["detail"])
    assert "senha" in str(senha.json()["detail"])


@pytest.mark.anyio
async def test_exclusao_exige_sessao_e_propriedade(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        primeiro = await api.post("/api/usuarios", json=payload())
        segundo = await api.post(
            "/api/usuarios",
            json=payload(email="joao@example.com", nome="João da Silva"),
        )
        primeiro_id = primeiro.json()["id"]
        segundo_id = segundo.json()["id"]
        sem_sessao = await api.delete(f"/api/usuarios/{primeiro_id}")
        await api.post("/api/auth/login", json={"email": "maria@example.com", "senha": "Senha123"})
        outro = await api.delete(f"/api/usuarios/{segundo_id}")
        proprio = await api.delete(f"/api/usuarios/{primeiro_id}")
        depois = await api.get(f"/api/usuarios/{primeiro_id}")

    assert sem_sessao.status_code == 401
    assert outro.status_code == 403
    assert proprio.status_code == 204
    assert depois.status_code == 404


@pytest.mark.anyio
async def test_mutacao_autenticada_valida_origem_e_prioriza_403(
    repositorio: RepositorioEmMemoria,
    instante: datetime,
) -> None:
    async with cliente(repositorio, instante) as api:
        criado = await api.post("/api/usuarios", json=payload())
        usuario_id = criado.json()["id"]
        await api.post("/api/auth/login", json={"email": "maria@example.com", "senha": "Senha123"})
        dados_atualizacao = {
            "nome": "Maria protegida",
            "email": "maria.protegida@example.com",
            "endereco": payload()["endereco"],
        }

        origem_invalida = await api.put(
            f"/api/usuarios/{usuario_id}",
            json=dados_atualizacao,
            headers={"Origin": "https://origem-nao-permitida.example"},
        )
        api.headers.pop("Origin", None)
        sem_origem = await api.put(
            f"/api/usuarios/{usuario_id}",
            json=dados_atualizacao,
        )
        referer_permitido = await api.put(
            f"/api/usuarios/{usuario_id}",
            json=dados_atualizacao,
            headers={"Referer": "http://localhost:5500/perfil.html"},
        )
        outro_id_inexistente = await api.put(
            "/api/usuarios/nao-existe",
            json=dados_atualizacao,
            headers={"Origin": "http://localhost:5500"},
        )

    assert origem_invalida.status_code == 403
    assert sem_origem.status_code == 403
    assert referer_permitido.status_code == 200
    assert outro_id_inexistente.status_code == 403
