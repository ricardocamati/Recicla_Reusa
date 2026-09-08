from dataclasses import asdict
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection

from app.models.usuario import Usuario


class MongoUsuarioRepository:
    def __init__(self, colecao: Collection[dict[str, Any]]) -> None:
        self._colecao = colecao

    def criar(self, usuario: Usuario) -> Usuario:
        resultado = self._colecao.insert_one(self._para_documento(usuario))
        usuario.id = str(resultado.inserted_id)
        return usuario

    def listar(self) -> list[Usuario]:
        documentos = self._colecao.find().sort("data_cadastro", -1)
        return [self._para_modelo(documento) for documento in documentos]

    def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        object_id = self._converter_id(usuario_id)
        if object_id is None:
            return None
        documento = self._colecao.find_one({"_id": object_id})
        return self._para_modelo(documento) if documento else None

    def atualizar(self, usuario: Usuario) -> Usuario:
        if usuario.id is None:
            raise ValueError("Usuário sem identificador não pode ser atualizado")
        self._colecao.replace_one({"_id": ObjectId(usuario.id)}, self._para_documento(usuario))
        return usuario

    def excluir(self, usuario_id: str) -> None:
        self._colecao.delete_one({"_id": ObjectId(usuario_id)})

    @staticmethod
    def _converter_id(usuario_id: str) -> ObjectId | None:
        try:
            return ObjectId(usuario_id)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    def _para_documento(usuario: Usuario) -> dict[str, Any]:
        documento = asdict(usuario)
        documento.pop("id")
        return documento

    @staticmethod
    def _para_modelo(documento: dict[str, Any]) -> Usuario:
        dados = dict(documento)
        dados["id"] = str(dados.pop("_id"))
        return Usuario(**dados)
