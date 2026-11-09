from typing import Any

from pymongo.collection import Collection

STATUS_CONTADOS = ("concluido",)


class MongoIndicadorRepository:
    """Totais calculados a partir dos itens concluídos, sem coleção própria."""

    def __init__(self, colecao_itens: Collection[dict[str, Any]]) -> None:
        self._colecao_itens = colecao_itens

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

    def contar_por_situacao(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$status", "total": {"$sum": 1}}}]
        return {
            documento["_id"]: documento["total"]
            for documento in self._colecao_itens.aggregate(pipeline)
            if documento.get("_id")
        }
