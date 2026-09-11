from datetime import UTC, datetime

import mongomock
import pytest

from app.exceptions import EmailDuplicadoError
from app.models.usuario import Usuario
from app.schemas.usuario import PontoColetaProvisionRequest
from app.services.usuario_service import UsuarioService


class RepositorioUsuariosFake:
    def __init__(self) -> None:
        self.usuarios: dict[str, Usuario] = {}
        self.proximo_id = 1

    def criar(self, usuario: Usuario) -> Usuario:
        usuario.id = str(self.proximo_id)
        self.proximo_id += 1
        self.usuarios[usuario.id] = usuario
        return usuario

    def buscar_por_email(self, email: str) -> Usuario | None:
        return next((usuario for usuario in self.usuarios.values() if usuario.email == email), None)


def request(**alteracoes) -> PontoColetaProvisionRequest:
    dados = {
        "nome": "Ponto de Coleta Central",
        "email": "coleta.central@example.com",
        "senha": "Senha123",
        "logradouro": "Rua da Reciclagem",
        "numero": "100",
        "cep": "87000-000",
        "cidade": "Maringá",
    }
    dados.update(alteracoes)
    return PontoColetaProvisionRequest(**dados)


def test_provisiona_ponto_coleta_por_servico_sem_expor_senha() -> None:
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    repositorio = RepositorioUsuariosFake()
    servico = UsuarioService(repositorio, relogio=lambda: instante)

    resposta = servico.provisionar_ponto_coleta(request())

    assert resposta.tipo == "ponto_coleta"
    assert resposta.email == "coleta.central@example.com"
    assert resposta.data_adicao == instante
    assert resposta.data_modificacao == instante
    assert "senha" not in resposta.model_dump()
    persistido = repositorio.usuarios[resposta.id]
    assert persistido.tipo == "ponto_coleta"
    assert persistido.senha_hash != "Senha123"
    assert persistido.cidade == "Maringá"


def test_provisionamento_rejeita_email_duplicado() -> None:
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    repositorio = RepositorioUsuariosFake()
    servico = UsuarioService(repositorio, relogio=lambda: instante)

    servico.provisionar_ponto_coleta(request())

    with pytest.raises(EmailDuplicadoError):
        servico.provisionar_ponto_coleta(request(email="COLETA.CENTRAL@EXAMPLE.COM"))


def test_request_de_provisionamento_nao_aceita_tipo_do_corpo() -> None:
    with pytest.raises(ValueError):
        request(tipo="doador")


def test_comando_provisiona_conta_controlada_no_mongo(monkeypatch, capsys) -> None:
    import app.provisionar_ponto_coleta as provisionador

    mongo = mongomock.MongoClient(tz_aware=True)
    monkeypatch.setattr(provisionador, "MongoClient", lambda _: mongo)
    monkeypatch.setattr(provisionador, "getpass", lambda _: "Senha123")

    class Configuracao:
        mongo_uri = "mongodb://teste"
        mongo_database = "recicla_reusa"
        mongo_collection_usuarios = "usuarios"

    monkeypatch.setattr(provisionador, "Settings", Configuracao)

    codigo = provisionador.main(
        [
            "--nome",
            "Ponto de Coleta CLI",
            "--email",
            "cli.coleta@example.com",
            "--logradouro",
            "Rua CLI",
            "--numero",
            "20",
            "--cep",
            "87000-001",
            "--cidade",
            "Sarandi",
        ]
    )

    assert codigo == 0
    assert "Ponto de coleta provisionado:" in capsys.readouterr().out
    documento = mongo["recicla_reusa"]["usuarios"].find_one(
        {"email": "cli.coleta@example.com"},
    )
    assert documento is not None
    assert documento["tipo"] == "ponto_coleta"
    assert documento["senha_hash"] != "Senha123"
