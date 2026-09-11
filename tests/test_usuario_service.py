from datetime import UTC, datetime

import pytest

from app.exceptions import EmailDuplicadoError, UsuarioNaoEncontradoError
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

    def buscar_por_email(self, email: str) -> Usuario | None:
        return next((u for u in self.usuarios.values() if u.email == email.lower()), None)

    def atualizar(self, usuario: Usuario) -> Usuario:
        assert usuario.id is not None
        self.usuarios[usuario.id] = usuario
        return usuario

    def excluir(self, usuario_id: str) -> None:
        self.usuarios.pop(usuario_id, None)


def request(
    nome: str = "Maria",
    email: str = "maria@example.com",
) -> UsuarioCreateRequest:
    return UsuarioCreateRequest(
        nome=nome,
        email=email,
        senha="Senha123",
        tipo="doador",
        logradouro="Rua das Flores",
        numero="10A",
        complemento="Casa 2",
        cep="87000000",
        cidade="Maringá",
    )


def update_request(
    nome: str = "Maria Silva",
    email: str = "maria.silva@example.com",
) -> UsuarioUpdateRequest:
    return UsuarioUpdateRequest(
        nome=nome,
        email=email,
        logradouro="Avenida Brasil",
        numero="200",
        cep="87010000",
        cidade="Sarandi",
    )


def test_criar_usuario_registra_datas_endereco_e_id() -> None:
    instante = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    repositorio = RepositorioFake()
    service = UsuarioService(repositorio, relogio=lambda: instante)

    resposta = service.criar(request())

    assert resposta.id == "1"
    assert resposta.nome == "Maria"
    assert resposta.cep == "87000000"
    assert resposta.data_adicao == instante
    assert resposta.data_modificacao == instante
    assert repositorio.usuarios["1"].senha_hash != "Senha123"


def test_atualizar_preserva_id_tipo_e_data_adicao_e_altera_modificacao() -> None:
    repositorio = RepositorioFake()
    instantes = iter(
        [
            datetime(2026, 9, 7, 12, 0, tzinfo=UTC),
            datetime(2026, 9, 7, 13, 0, tzinfo=UTC),
        ]
    )
    service = UsuarioService(repositorio, relogio=lambda: next(instantes))
    criado = service.criar(request())

    resposta = service.atualizar(criado.id or "", update_request())

    assert resposta.id == criado.id
    assert resposta.tipo == "doador"
    assert resposta.data_adicao == datetime(2026, 9, 7, 12, 0, tzinfo=UTC)
    assert resposta.data_modificacao == datetime(2026, 9, 7, 13, 0, tzinfo=UTC)
    assert resposta.cidade == "Sarandi"


def test_email_normalizado_nao_pode_ser_repetido() -> None:
    repositorio = RepositorioFake()
    service = UsuarioService(repositorio)
    service.criar(request(email="maria@example.com"))

    with pytest.raises(EmailDuplicadoError):
        service.criar(request(email=" MARIA@EXAMPLE.COM "))


def test_autenticacao_valida_senha_e_rejeita_credencial_invalida() -> None:
    repositorio = RepositorioFake()
    service = UsuarioService(repositorio)
    criado = service.criar(request())

    assert service.autenticar("MARIA@EXAMPLE.COM", "Senha123") is not None
    assert service.autenticar("maria@example.com", "errada") is None
    assert service.autenticar("ausente@example.com", "Senha123") is None
    assert criado.id == "1"


def test_usuario_inexistente_gera_erro_de_dominio() -> None:
    with pytest.raises(UsuarioNaoEncontradoError, match="nao-existe"):
        UsuarioService(RepositorioFake()).buscar_por_id("nao-existe")
