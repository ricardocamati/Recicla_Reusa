from typing import Any

from pymongo.collection import Collection

STATUS_CONTADOS = ("concluido",)


class MongoIndicadorRepository:
    """Totais calculados a partir dos itens concluídos, sem coleção própria."""

    def __init__(
        self,
        colecao_itens: Collection[dict[str, Any]],
        colecao_pontos: Collection[dict[str, Any]] | None = None,
    ) -> None:
        self._colecao_itens = colecao_itens
        self._colecao_pontos = colecao_pontos

    def contar_por_modalidade_e_status(self) -> dict[str, int]:
        pipeline = [
            {"$match": {"status": {"$in": list(STATUS_CONTADOS)}}},
            {
                "$group": {
                    "_id": {"modalidade": "$destino", "status": "$status"},
                    "total": {"$sum": 1},
                }
            },
        ]
        return {
            f"{documento['_id'].get('modalidade')}:{documento['_id'].get('status')}": documento[
                "total"
            ]
            for documento in self._colecao_itens.aggregate(pipeline)
        }

    def contar_locais_ativos(self) -> int:
        """Informação cadastral do diretório, nunca resultado de equipamentos."""
        if self._colecao_pontos is None:
            return 0
        return self._colecao_pontos.count_documents({"ativo": {"$ne": False}})

    def contar_por_situacao(self) -> dict[str, int]:
        # Registros antigos de descarte não são ofertas e não podem inflar os totais.
        pipeline = [
            {"$match": {"destino": {"$in": ["doacao", "revenda"]}}},
            {"$group": {"_id": "$status", "total": {"$sum": 1}}},
        ]
        return {
            documento["_id"]: documento["total"]
            for documento in self._colecao_itens.aggregate(pipeline)
            if documento.get("_id")
        }
