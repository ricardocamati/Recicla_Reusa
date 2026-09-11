from datetime import UTC, datetime

import mongomock
import pytest
from bson import ObjectId

from app.exceptions import EmailDuplicadoError
from app.models.usuario import Usuario
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.security.passwords import hash_password


def usuario(email: str = "joao@example.com") -> Usuario:
    instante = datetime(2026, 9, 7, tzinfo=UTC)
    return Usuario(
        nome="João",
        email=email,
        tipo="beneficiario",
        logradouro="Rua A",
        numero="1",
        complemento=None,
        cep="87000000",
        cidade="Maringá",
        senha_hash=hash_password("Senha123"),
        data_adicao=instante,
        data_modificacao=instante,
    )


def test_repositorio_persiste_endereco_datas_e_remove_usuario() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).recicla_reusa.usuarios
    repositorio = MongoUsuarioRepository(colecao)

    criado = repositorio.criar(usuario())
    documento = colecao.find_one({"_id": ObjectId(criado.id or "")})
    recuperado = repositorio.buscar_por_id(criado.id or "")

    assert documento is not None
    assert "endereco" not in documento
    assert documento["logradouro"] == "Rua A"
    assert documento["numero"] == "1"
    assert documento["complemento"] is None
    assert documento["cep"] == "87000000"
    assert documento["cidade"] == "Maringá"
    assert recuperado is not None
    assert recuperado.email == "joao@example.com"
    assert recuperado.cep == "87000000"
    assert not hasattr(recuperado, "endereco")
    assert recuperado.data_adicao == datetime(2026, 9, 7, tzinfo=UTC)
    assert len(repositorio.listar()) == 1
    assert repositorio.buscar_por_email("JOAO@EXAMPLE.COM") is not None
    assert list(repositorio.buscar_por_ids([criado.id or "", "invalido"])) == [criado.id]
    assert repositorio._colecao.index_information()["usuario_email_unico"]["unique"] is True

    criado.cidade = "Sarandi"
    repositorio.atualizar(criado)
    documento_atualizado = colecao.find_one({"_id": ObjectId(criado.id or "")})
    assert documento_atualizado is not None
    assert "endereco" not in documento_atualizado
    assert documento_atualizado["cidade"] == "Sarandi"

    repositorio.excluir(criado.id or "")
    assert repositorio.buscar_por_id(criado.id or "") is None


def test_repositorio_rejeita_email_duplicado_por_indice() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).recicla_reusa.usuarios
    repositorio = MongoUsuarioRepository(colecao)
    repositorio.criar(usuario())

    with pytest.raises(EmailDuplicadoError):
        repositorio.criar(usuario("JOAO@EXAMPLE.COM"))
