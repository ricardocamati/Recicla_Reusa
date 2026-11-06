"""Indicadores: cada item conta uma vez, só depois da confirmação."""
import mongomock
from datetime import UTC, datetime

from app.repositories.mongo_indicador_repository import MongoIndicadorRepository
from app.services.indicador_service import IndicadorService


def montar(itens: list[tuple[str, str]]):
    colecao = mongomock.MongoClient(tz_aware=True).teste.itens
    instante = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
    for indice, (modalidade, status) in enumerate(itens):
        colecao.insert_one(
            {
                "titulo": f"Item {indice}",
                "destino": modalidade,
                "status": status,
                "data_adicao": instante,
                "data_modificacao": instante,
            }
        )
    return colecao


def test_contabiliza_somente_concluidos_por_modalidade() -> None:
    colecao = montar(
        [
            ("doacao", "concluido"),
            ("doacao", "concluido"),
            ("descarte", "recebido"),
            ("revenda", "concluido"),
            ("doacao", "aguardando_confirmacao"),
            ("doacao", "reservado"),
            ("revenda", "disponivel"),
        ]
    )

    indicadores = IndicadorService(MongoIndicadorRepository(colecao)).obter()

    assert indicadores.doados == 2
    assert indicadores.coletados == 1
    assert indicadores.vendidos == 1
    assert indicadores.total == 4
    assert indicadores.ofertas_ativas == 1
    assert indicadores.pendencias == 2


def test_base_sem_confirmacao_retorna_zero() -> None:
    indicadores = IndicadorService(
        MongoIndicadorRepository(
            montar([("doacao", "aguardando_confirmacao"), ("revenda", "reservado")])
        )
    ).obter()

    assert (indicadores.doados, indicadores.coletados, indicadores.vendidos) == (0, 0, 0)
    assert indicadores.total == 0
