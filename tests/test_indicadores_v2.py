"""Indicadores: somente itens concluídos entram nos totais."""
import mongomock
from datetime import UTC, datetime

from app.repositories.mongo_indicador_repository import MongoIndicadorRepository
from app.services.indicador_service import IndicadorService


def montar(statuses: list[str]):
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    for indice, status in enumerate(statuses):
        colecao.insert_one(
            {
                "titulo": f"Item {indice}",
                "status": status,
                "data_adicao": instante,
                "data_modificacao": instante,
            }
        )
    return colecao


def test_contabiliza_somente_status_concluidos() -> None:
    colecao = montar(
        ["doado", "doado", "coletado", "vendido", "disponivel", "reservado", "encaminhado"]
    )

    indicadores = IndicadorService(MongoIndicadorRepository(colecao)).obter()

    assert indicadores.doados == 2
    assert indicadores.coletados == 1
    assert indicadores.vendidos == 1
    assert indicadores.total == 4


def test_base_sem_itens_concluidos_retorna_zero() -> None:
    indicadores = IndicadorService(
        MongoIndicadorRepository(montar(["disponivel", "em_avaliacao"]))
    ).obter()

    assert (indicadores.doados, indicadores.coletados, indicadores.vendidos) == (0, 0, 0)
    assert indicadores.total == 0
