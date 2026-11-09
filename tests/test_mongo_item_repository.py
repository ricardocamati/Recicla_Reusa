from dataclasses import replace
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
        especificacoes={"memoria_ram": "8 GB"},
        historico=[],
        data_adicao=instante,
        data_modificacao=instante,
    )


def test_catalogo_mongo_nao_deixa_modalidade_fora_da_allowlist_escapar():
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    repo = MongoItemRepository(colecao)
    repo.criar(item())
    colecao.insert_one({
        "_id": ObjectId(),
        "titulo": "Documento antigo de descarte",
        "descricao": "sem fluxo novo",
        "categoria": "informatica",
        "marca": "Dell",
        "modelo": "Inspiron",
        "condicao": "funcional",
        "destino": "descarte",
        "status": "disponivel",
        "proprietario_id": ObjectId(PROPRIETARIO_ID),
        "data_adicao": datetime(2026, 1, 1, tzinfo=UTC),
        "data_modificacao": datetime(2026, 1, 1, tzinfo=UTC),
    })
    # model_construct simula um chamador interno que contorne a validação do schema.
    filtros = FiltrosItem.model_construct(destino="descarte")
    encontrados = repo.listar(filtros, somente_catalogo=True)
    assert {registro.destino for registro in encontrados} == {"doacao"}


def test_catalogo_mongo_preserva_filtro_explicito_de_modalidade():
    repo = MongoItemRepository(mongomock.MongoClient(tz_aware=True).teste.itens)
    repo.criar(item())
    venda = repo.criar(replace(item(), destino="revenda", valor=100))
    encontrados = repo.listar(FiltrosItem(destino="revenda"), somente_catalogo=True)
    assert [registro.id for registro in encontrados] == [venda.id]


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
    assert documento["especificacoes"] == {"memoria_ram": "8 GB"}
    assert documento["historico"] == []
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


def test_repositorio_normaliza_datas_na_precisao_do_mongodb() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).recicla_reusa.itens
    repositorio = MongoItemRepository(colecao)
    item_com_microssegundos = replace(
        item(),
        data_adicao=datetime(2026, 9, 8, 12, 0, 0, 123456, tzinfo=UTC),
        data_modificacao=datetime(2026, 9, 8, 12, 0, 0, 123456, tzinfo=UTC),
    )

    criado = repositorio.criar(item_com_microssegundos)
    recuperado = repositorio.buscar_por_id(criado.id or "")

    assert recuperado is not None
    assert criado.data_adicao.microsecond == 123000
    assert criado.data_modificacao.microsecond == 123000
    assert recuperado.data_adicao == criado.data_adicao
    assert recuperado.data_modificacao == criado.data_modificacao


def test_repositorio_persiste_referencias_do_fluxo() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    repositorio = MongoItemRepository(colecao)
    comprador_id = ObjectId()
    criado = repositorio.criar(replace(item(), destino="revenda", valor=100, status="reservado", comprador_id=str(comprador_id)))
    recuperado = repositorio.buscar_por_id(criado.id or "")
    assert recuperado is not None
    assert recuperado.comprador_id == str(comprador_id)
    documento = colecao.find_one({"_id": ObjectId(criado.id)})
    assert documento["comprador_id"] == comprador_id
    criado.descricao = "Descrição atualizada"
    repositorio.atualizar(criado)
    relido = repositorio.buscar_por_id(criado.id or "")
    assert relido.comprador_id == str(comprador_id)
    assert relido.descricao == "Descrição atualizada"


def test_leitura_de_oferta_sem_referencias_de_participantes() -> None:
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    repositorio = MongoItemRepository(colecao)
    documento = repositorio._para_documento(item())
    assert documento.pop("beneficiario_id") is None
    assert documento.pop("comprador_id") is None
    identificador = colecao.insert_one(documento).inserted_id

    relido = repositorio.buscar_por_id(str(identificador))

    assert relido is not None
    assert relido.beneficiario_id is None
    assert relido.comprador_id is None


def test_leitura_ignora_campos_do_fluxo_de_descarte_removido() -> None:
    """Bancos anteriores guardam campos que o modelo não tem mais; ler não pode quebrar."""
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    repositorio = MongoItemRepository(colecao)
    documento = repositorio._para_documento(item())
    documento["ponto_coleta_id"] = ObjectId()
    documento["destinacao_informada"] = {"tipo_local": "ecoponto", "nome": "Antigo"}
    identificador = colecao.insert_one(documento).inserted_id

    relido = repositorio.buscar_por_id(str(identificador))

    assert relido is not None
    assert relido.destino == "doacao" and relido.status == "disponivel"
    assert not hasattr(relido, "ponto_coleta_id")
    # Regravar mantém o documento legível e não reintroduz o campo no modelo.
    relido.descricao = "Descrição atualizada"
    repositorio.atualizar(relido)
    regravado = repositorio.buscar_por_id(str(identificador))
    assert regravado.descricao == "Descrição atualizada"
    assert not hasattr(regravado, "ponto_coleta_id")
    assert not hasattr(regravado, "destinacao_informada")
    # O documento antigo não é migrado nem apagado: os campos simplesmente não são lidos.
    assert "ponto_coleta_id" in colecao.find_one({"_id": identificador})


def test_leitura_ignora_selecao_interna_do_interesse():
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    repo = MongoItemRepository(colecao)
    doc = repo._para_documento(item())
    doc["interesse_aceito_id"] = ObjectId()
    doc["_lock_interesses"] = 1
    identificador = colecao.insert_one(doc).inserted_id
    relido = repo.buscar_por_id(str(identificador))
    assert relido is not None
    assert not hasattr(relido, "interesse_aceito_id")


def test_edicao_nao_apaga_selecao_de_interesse():
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    repo = MongoItemRepository(colecao)
    criado = repo.criar(item())
    selecionado = ObjectId()
    colecao.update_one({"_id": ObjectId(criado.id)}, {"$set": {"interesse_aceito_id": selecionado}})
    criado.titulo = "Título editado"
    repo.atualizar(criado, status_esperado="disponivel")
    assert colecao.find_one()["interesse_aceito_id"] == selecionado
