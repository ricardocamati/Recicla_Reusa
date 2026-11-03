import re
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection

from app.exceptions import ReferenciaAtivaError
from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Endereco


class MongoPontoColetaRepository:
    def __init__(
        self,
        colecao: Collection[dict[str, Any]],
        *,
        criar_indices: bool = True,
        colecao_itens: Collection[dict[str, Any]] | None = None,
    ) -> None:
        self._colecao = colecao
        self._colecao_itens = colecao_itens
        if criar_indices:
            self.criar_indices()

    def criar_indices(self) -> None:
        self._colecao.create_index("responsavel_id", name="ponto_responsavel")
        self._colecao.create_index("categorias_aceitas", name="ponto_categorias")
        self._colecao.create_index(
            [("responsavel_id", 1), ("nome", 1)],
            name="ponto_responsavel_nome",
            unique=True,
        )

    def criar(self, ponto: PontoColeta) -> PontoColeta:
        self._normalizar(ponto)
        resultado = self._colecao.insert_one(self._para_documento(ponto))
        ponto.id = str(resultado.inserted_id)
        return ponto

    def listar(
        self,
        *,
        cidade: str | None = None,
        categoria: str | None = None,
        responsavel_id: str | None = None,
        offset: int = 0,
        limite: int = 20,
    ) -> list[PontoColeta]:
        consulta: dict[str, Any] = {}
        if cidade:
            consulta["endereco.cidade"] = {
                "$regex": f"^{re.escape(cidade.strip())}$",
                "$options": "i",
            }
        if categoria:
            consulta["categorias_aceitas"] = categoria
        if responsavel_id:
            object_id = self._converter_id(responsavel_id)
            if object_id is None:
                return []
            consulta["responsavel_id"] = object_id
        documentos = (
            self._colecao.find(consulta)
            .sort("nome", 1)
            .skip(offset)
            .limit(limite)
        )
        return [self._para_modelo(documento) for documento in documentos]

    def buscar_por_id(self, ponto_id: str) -> PontoColeta | None:
        object_id = self._converter_id(ponto_id)
        if object_id is None:
            return None
        documento = self._colecao.find_one({"_id": object_id})
        return self._para_modelo(documento) if documento else None

    def atualizar(self, ponto: PontoColeta, *, responsavel_id: str) -> bool:
        if ponto.id is None:
            raise ValueError("Ponto sem identificador não pode ser atualizado")
        self._normalizar(ponto)
        filtro = {"_id": ObjectId(ponto.id), "responsavel_id": ObjectId(responsavel_id)}
        resultado = self._colecao.replace_one(filtro, self._para_documento(ponto))
        return resultado.matched_count == 1

    def excluir(self, ponto_id: str, *, responsavel_id: str) -> bool:
        object_id = self._converter_id(ponto_id)
        object_responsavel = self._converter_id(responsavel_id)
        if object_id is None or object_responsavel is None:
            return False
        if (self._colecao_itens is not None
                and self._colecao_itens.count_documents({"ponto_coleta_id": object_id})):
            raise ReferenciaAtivaError()
        resultado = self._colecao.delete_one(
            {"_id": object_id, "responsavel_id": object_responsavel}
        )
        return resultado.deleted_count == 1

    def contar_por_responsavel(self, responsavel_id: str) -> int:
        object_id = self._converter_id(responsavel_id)
        if object_id is None:
            return 0
        return self._colecao.count_documents({"responsavel_id": object_id})

    def aceita_categoria(self, ponto_id: str, categoria: str) -> bool | None:
        ponto = self.buscar_por_id(ponto_id)
        if ponto is None:
            return None
        return categoria in ponto.categorias_aceitas

    @staticmethod
    def _converter_id(valor: str) -> ObjectId | None:
        try:
            return ObjectId(valor)
        except (InvalidId, TypeError):
            return None

    @classmethod
    def _normalizar(cls, ponto: PontoColeta) -> None:
        ponto.data_adicao = cls._normalizar_data(ponto.data_adicao)
        ponto.data_modificacao = cls._normalizar_data(ponto.data_modificacao)

    @staticmethod
    def _normalizar_data(instante: datetime) -> datetime:
        instante_utc = (
            instante.replace(tzinfo=UTC)
            if instante.tzinfo is None
            else instante.astimezone(UTC)
        )
        return instante_utc.replace(microsecond=instante_utc.microsecond // 1000 * 1000)

    @staticmethod
    def _para_documento(ponto: PontoColeta) -> dict[str, Any]:
        documento = asdict(ponto)
        documento.pop("id")
        try:
            documento["responsavel_id"] = ObjectId(documento["responsavel_id"])
        except (InvalidId, TypeError) as erro:
            raise ValueError("responsavel_id deve ser um ObjectId válido") from erro
        return documento

    @staticmethod
    def _para_modelo(documento: dict[str, Any]) -> PontoColeta:
        dados = dict(documento)
        dados["id"] = str(dados.pop("_id"))
        dados["responsavel_id"] = str(dados["responsavel_id"])
        dados["endereco"] = Endereco(**dados["endereco"])
        dados["data_adicao"] = MongoPontoColetaRepository._normalizar_data(dados["data_adicao"])
        dados["data_modificacao"] = MongoPontoColetaRepository._normalizar_data(
            dados["data_modificacao"]
        )
        return PontoColeta(**dados)
