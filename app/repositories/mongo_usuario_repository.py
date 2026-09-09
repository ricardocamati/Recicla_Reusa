from dataclasses import asdict
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.exceptions import EmailDuplicadoError
from app.models.usuario import Endereco, Usuario


class MongoUsuarioRepository:
    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        *,
        criar_indice: bool = True,
    ) -> None:
        self._colecao = colecao
        if criar_indice:
            self.criar_indice_email()

    def criar_indice_email(self) -> None:
        self._colecao.create_index("email", unique=True, name="usuario_email_unico")

    def criar(self, usuario: Usuario) -> Usuario:
        usuario.email = usuario.email.strip().lower()
        try:
            resultado = self._colecao.insert_one(self._para_documento(usuario))
        except DuplicateKeyError as erro:
            raise EmailDuplicadoError(usuario.email) from erro
        usuario.id = str(resultado.inserted_id)
        return usuario

    def listar(self) -> list[Usuario]:
        documentos = self._colecao.find().sort("data_adicao", -1)
        return [self._para_modelo(documento) for documento in documentos]

    def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        object_id = self._converter_id(usuario_id)
        if object_id is None:
            return None
        documento = self._colecao.find_one({"_id": object_id})
        return self._para_modelo(documento) if documento else None

    def buscar_por_email(self, email: str) -> Usuario | None:
        documento = self._colecao.find_one({"email": email.lower()})
        return self._para_modelo(documento) if documento else None

    def atualizar(self, usuario: Usuario) -> Usuario:
        if usuario.id is None:
            raise ValueError("Usuário sem identificador não pode ser atualizado")
        usuario.email = usuario.email.strip().lower()
        try:
            resultado = self._colecao.replace_one(
                {"_id": ObjectId(usuario.id)},
                self._para_documento(usuario),
            )
        except DuplicateKeyError as erro:
            raise EmailDuplicadoError(usuario.email) from erro
        if resultado.matched_count == 0:
            return usuario
        return usuario

    def excluir(self, usuario_id: str) -> None:
        object_id = self._converter_id(usuario_id)
        if object_id is not None:
            self._colecao.delete_one({"_id": object_id})

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
        dados["endereco"] = Endereco(**dados["endereco"])
        return Usuario(**dados)
