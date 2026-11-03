"""Normaliza os perfis da v2.0 para a conta única de pessoa da v2.1.

Uso:
    MONGO_URI=... MONGO_DATABASE=... python scripts/migrar_papeis_v2_1.py
    MONGO_URI=... MONGO_DATABASE=... python scripts/migrar_papeis_v2_1.py --aplicar

Sem ``--aplicar`` o script apenas relata o que mudaria. A migração troca
``doador`` e ``beneficiario`` por ``pessoa`` e confere se as referências
existentes continuam apontando para contas compatíveis; datas de auditoria
não são reescritas.
"""
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.config import Settings  # noqa: E402

PERFIS_ANTIGOS = ("doador", "beneficiario")
PERFIS_VALIDOS = ("pessoa", "ponto_coleta")


@dataclass
class Relatorio:
    """Resultado da inspeção/migração, sem alterar o banco no modo de simulação."""

    encontrados: Counter = field(default_factory=Counter)
    migrados: int = 0
    invalidos: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)


def _ids(colecao, filtro: dict[str, Any]) -> set[str]:
    return {str(documento["_id"]) for documento in colecao.find(filtro, {"_id": 1})}


def migrar(banco: Database, *, aplicar: bool = False) -> Relatorio:
    """Troca os perfis antigos por ``pessoa`` e valida as referências."""
    usuarios = banco[Settings().mongo_collection_usuarios]
    itens = banco[Settings().mongo_collection_itens]
    interesses = banco[Settings().mongo_collection_interesses]
    pontos = banco[Settings().mongo_collection_pontos_coleta]
    relatorio = Relatorio()

    antigos = list(usuarios.find({"tipo": {"$in": list(PERFIS_ANTIGOS)}}))
    relatorio.encontrados = Counter(documento.get("tipo") for documento in antigos)
    if aplicar and antigos:
        resultado = usuarios.update_many(
            {"tipo": {"$in": list(PERFIS_ANTIGOS)}},
            {"$set": {"tipo": "pessoa"}},
        )
        relatorio.migrados = resultado.modified_count

    for documento in usuarios.find({}):
        tipo = documento.get("tipo")
        if tipo in PERFIS_ANTIGOS and not aplicar:
            # A simulação projeta o resultado da troca.
            continue
        if tipo not in PERFIS_VALIDOS:
            relatorio.invalidos.append(str(documento["_id"]))

    pessoas = _ids(usuarios, {"tipo": "pessoa"})
    if not aplicar:
        # Na simulação, os perfis antigos contam como pessoa para prever o resultado.
        pessoas |= _ids(usuarios, {"tipo": {"$in": list(PERFIS_ANTIGOS)}})
    operadores = _ids(usuarios, {"tipo": "ponto_coleta"})

    for item in itens.find({}):
        proprietario = str(item.get("proprietario_id"))
        if proprietario not in pessoas:
            relatorio.problemas.append(f"item {item['_id']} com proprietário não-pessoa")
        for campo in ("beneficiario_id", "comprador_id"):
            referencia = item.get(campo)
            if referencia is not None and str(referencia) not in pessoas:
                relatorio.problemas.append(f"item {item['_id']} com {campo} inválido")

    for interesse in interesses.find({}):
        if str(interesse.get("usuario_id")) not in pessoas:
            relatorio.problemas.append(
                f"interesse {interesse['_id']} com interessado não-pessoa"
            )

    for ponto in pontos.find({}):
        responsavel = ponto.get("responsavel_id")
        if responsavel is not None and str(responsavel) not in operadores:
            relatorio.problemas.append(
                f"ponto {ponto['_id']} com responsável que não é operador"
            )

    return relatorio


def main(argv: list[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    aplicar = "--aplicar" in argumentos
    configuracao = Settings()
    cliente = MongoClient(configuracao.mongo_uri, serverSelectionTimeoutMS=5000)
    try:
        banco = cliente[configuracao.mongo_database]
        relatorio = migrar(banco, aplicar=aplicar)
        modo = "aplicado" if aplicar else "simulação (use --aplicar)"
        print(f"modo={modo} banco={configuracao.mongo_database}")
        print(
            "perfis_antigos="
            + (", ".join(f"{perfil}={qtd}" for perfil, qtd in sorted(relatorio.encontrados.items())) or "nenhum")
        )
        print(f"migrados={relatorio.migrados}")
        print(f"invalidos={len(relatorio.invalidos)}")
        print(f"problemas={len(relatorio.problemas)}")
        for problema in relatorio.problemas:
            print(f"- {problema}")
        return 0 if not relatorio.problemas and not relatorio.invalidos else 1
    finally:
        cliente.close()


if __name__ == "__main__":
    sys.exit(main())
