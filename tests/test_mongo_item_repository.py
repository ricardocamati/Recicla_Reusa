from datetime import UTC, datetime

import mongomock
from bson import ObjectId

from app.models.item import Item
from app.repositories.mongo_item_repository import MongoItemRepository
from app.schemas.item import FiltrosItem


PROPRIETARIO_ID = str(ObjectId())


def item(item_id: str | None = None) -> Item:
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    return Item(
        id=item_id,
        titulo="Notebook usado",
        descricao="Funcionando",
        categoria="informatica",
        marca="Dell",
        modelo="Inspiron 15",
        condicao="funcional",
        destino="doacao",
        valor=None,
        status="disponivel",
        proprietario_id=PROPRIETARIO_ID,
        data_adicao=instante,
        data_modificacao=instante,
    )


def test_repositorio_persiste_filtra_atualiza_e_exclui_item() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).recicla_reusa.itens
    repositorio = MongoItemRepository(colecao)

    criado = repositorio.criar(item())
    recuperado = repositorio.buscar_por_id(criado.id or "")

    assert recuperado is not None
    assert recuperado.proprietario_id == PROPRIETARIO_ID
    documento = colecao.find_one({"_id": colecao.find_one()["_id"]})
    assert documento["proprietario_id"] == ObjectId(PROPRIETARIO_ID)
    assert "endereco" not in documento
    assert len(repositorio.listar(FiltrosItem(categoria="informatica"))) == 1
    assert repositorio._colecao.index_information()["item_proprietario"]["key"] == [("proprietario_id", 1)]

    criado.titulo = "Notebook atualizado"
    criado.data_modificacao = datetime(2026, 9, 8, 12, 5, tzinfo=UTC)
    repositorio.atualizar(criado)
    atualizado = repositorio.buscar_por_id(criado.id or "")
    assert atualizado is not None
    assert atualizado.titulo == "Notebook atualizado"
    assert atualizado.data_modificacao == datetime(2026, 9, 8, 12, 5, tzinfo=UTC)

    repositorio.excluir(criado.id or "")
    assert repositorio.buscar_por_id(criado.id or "") is None


def test_repositorio_retorna_none_para_id_invalido() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).recicla_reusa.itens
    repositorio = MongoItemRepository(colecao)

    assert repositorio.buscar_por_id("abc") is None
