from typing import Any

from pymongo.collection import Collection

STATUS_CONCLUIDOS = ("doado", "coletado", "vendido")


class MongoIndicadorRepository:
    """Totais calculados a partir dos itens concluídos, sem coleção própria."""

    def __init__(self, colecao_itens: Collection[dict[str, Any]]) -> None:
        self._colecao_itens = colecao_itens

    def contar_por_status(self) -> dict[str, int]:
        pipeline = [
            {"$match": {"status": {"$in": list(STATUS_CONCLUIDOS)}}},
            {"$group": {"_id": "$status", "total": {"$sum": 1}}},
        ]
        return {
            documento["_id"]: documento["total"]
            for documento in self._colecao_itens.aggregate(pipeline)
        }
