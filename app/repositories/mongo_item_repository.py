from dataclasses import asdict
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection

from app.models.item import Item
from app.schemas.item import FiltrosItem


class MongoItemRepository:
    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        *,
        criar_indices: bool = True,
    ) -> None:
        self._colecao = colecao
        if criar_indices:
            self.criar_indices()

    def criar_indices(self) -> None:
        self._colecao.create_index("proprietario_id", name="item_proprietario")
        self._colecao.create_index("categoria", name="item_categoria")
        self._colecao.create_index("condicao", name="item_condicao")
        self._colecao.create_index("destino", name="item_destino")
        self._colecao.create_index("status", name="item_status")

    def criar(self, item: Item) -> Item:
        resultado = self._colecao.insert_one(self._para_documento(item))
        item.id = str(resultado.inserted_id)
        return item

    def listar(self, filtros: FiltrosItem) -> list[Item]:
        consulta = {
            campo: valor
            for campo, valor in filtros.model_dump().items()
            if valor is not None
        }
        documentos = self._colecao.find(consulta).sort("data_adicao", -1)
        return [self._para_modelo(documento) for documento in documentos]

    def buscar_por_id(self, item_id: str) -> Item | None:
        object_id = self._converter_id(item_id)
        if object_id is None:
            return None
        documento = self._colecao.find_one({"_id": object_id})
        return self._para_modelo(documento) if documento else None

    def atualizar(self, item: Item) -> Item:
        if item.id is None:
            raise ValueError("Item sem identificador não pode ser atualizado")
        self._colecao.replace_one(
            {"_id": ObjectId(item.id)},
            self._para_documento(item),
        )
        return item

    def excluir(self, item_id: str) -> None:
        object_id = self._converter_id(item_id)
        if object_id is not None:
            self._colecao.delete_one({"_id": object_id})

    @staticmethod
    def _converter_id(item_id: str) -> ObjectId | None:
        try:
            return ObjectId(item_id)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    def _para_documento(item: Item) -> dict[str, Any]:
        documento = asdict(item)
        documento.pop("id")
        try:
            documento["proprietario_id"] = ObjectId(documento["proprietario_id"])
        except (InvalidId, TypeError) as erro:
            raise ValueError("proprietario_id deve ser um ObjectId válido") from erro
        return documento

    @staticmethod
    def _para_modelo(documento: dict[str, Any]) -> Item:
        dados = dict(documento)
        dados["id"] = str(dados.pop("_id"))
        dados["proprietario_id"] = str(dados["proprietario_id"])
        return Item(**dados)
