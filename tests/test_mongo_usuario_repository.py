from datetime import UTC, datetime

import mongomock

from app.models.usuario import Usuario
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository


def test_repositorio_persiste_e_remove_usuario() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).recicla_reusa.usuarios
    repositorio = MongoUsuarioRepository(colecao)
    usuario = Usuario(
        nome="João",
        email="joao@example.com",
        tipo="beneficiario",
        cidade="Maringá",
        data_cadastro=datetime(2026, 9, 7, tzinfo=UTC),
    )

    criado = repositorio.criar(usuario)
    recuperado = repositorio.buscar_por_id(criado.id or "")

    assert recuperado is not None
    assert recuperado.email == "joao@example.com"
    assert len(repositorio.listar()) == 1

    repositorio.excluir(criado.id or "")
    assert repositorio.buscar_por_id(criado.id or "") is None
