from datetime import UTC, datetime

import pytest

from app.exceptions import UsuarioNaoEncontradoError
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreateRequest, UsuarioUpdateRequest
from app.services.usuario_service import UsuarioService


class RepositorioFake:
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
        assert usuario.id is not None
        self.usuarios[usuario.id] = usuario
        return usuario

    def excluir(self, usuario_id: str) -> None:
        del self.usuarios[usuario_id]


def request(nome: str = "Maria") -> UsuarioCreateRequest:
    return UsuarioCreateRequest(
        nome=nome,
        email="maria@example.com",
        tipo="doador",
        cidade="Maringá",
    )


def test_criar_usuario_registra_data_e_id() -> None:
    instante = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    service = UsuarioService(RepositorioFake(), relogio=lambda: instante)

    resposta = service.criar(request())

    assert resposta.id == "1"
    assert resposta.nome == "Maria"
    assert resposta.data_cadastro == instante


def test_atualizar_preserva_id_e_data() -> None:
    repositorio = RepositorioFake()
    instante = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    service = UsuarioService(repositorio, relogio=lambda: instante)
    criado = service.criar(request())

    resposta = service.atualizar(
        criado.id,
        UsuarioUpdateRequest(
            nome="Maria Silva",
            email="maria.silva@example.com",
            tipo="beneficiario",
            cidade="Sarandi",
        ),
    )

    assert resposta.id == criado.id
    assert resposta.data_cadastro == instante
    assert resposta.tipo == "beneficiario"


def test_usuario_inexistente_gera_erro_de_dominio() -> None:
    with pytest.raises(UsuarioNaoEncontradoError, match="nao-existe"):
        UsuarioService(RepositorioFake()).buscar_por_id("nao-existe")
