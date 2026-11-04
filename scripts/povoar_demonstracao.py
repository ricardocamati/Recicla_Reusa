"""Povoamento aditivo da demonstração local; nunca apaga ou redefine dados."""
from __future__ import annotations

import httpx

ENDERECO = {"logradouro": "Rua Fictícia da Demonstração", "numero": "100", "cep": "87000000", "cidade": "Maringá"}


def conferir_identidade(perfil: dict, esperado: dict) -> None:
    if not perfil.get("id") or any(perfil.get(k) != esperado[k] for k in ("email", "nome", "tipo")):
        raise DemonstracaoError("A sessão não corresponde à conta de demonstração esperada")


def garantir_conta(cliente, esperado: dict, senha: str) -> dict:
    resposta = cliente.post("/api/auth/login", json={"email": esperado["email"], "senha": senha})
    criado = None
    if resposta.status_code == 401:
        if esperado["tipo"] != "pessoa":
            raise DemonstracaoError("Conta operacional ausente ou senha inválida; provisionamento local necessário")
        criado = chamar(cliente, "POST", "/api/usuarios", codigos=(201,), json={
            **{k: esperado[k] for k in ("nome", "email")}, "senha": senha, "endereco": ENDERECO,
        })
        conferir_identidade(criado, esperado)
        chamar(cliente, "POST", "/api/auth/login", json={"email": esperado["email"], "senha": senha})
    elif resposta.status_code != 200:
        raise DemonstracaoError(f"Login indisponível: HTTP {resposta.status_code}")
    perfil = chamar(cliente, "GET", "/api/usuarios/me")
    conferir_identidade(perfil, esperado)
    if criado is not None and perfil["id"] != criado["id"]:
        raise DemonstracaoError("O login não confirmou o ID criado")
    return perfil


class DemonstracaoError(RuntimeError):
    """Interrompe a carga sem anunciar sucesso parcial ou revelar segredos."""


def chamar(cliente, metodo: str, caminho: str, *, codigos=(200,), **kwargs):
    resposta = cliente.request(metodo, caminho, **kwargs)
    if resposta.status_code not in codigos:
        raise DemonstracaoError(f"{metodo} {caminho}: HTTP {resposta.status_code}")
    return resposta.json() if resposta.content else None


def garantir_registro(cliente, caminho, registros, identidade, campo_dono, dono_id, *, corpo=None):
    candidatos = [r for r in registros if all(r.get(k) == v for k, v in identidade.items())]
    if len(candidatos) > 1 or (candidatos and candidatos[0].get(campo_dono) != dono_id):
        raise DemonstracaoError("Registro de demonstração ambíguo ou pertencente a outra conta")
    if candidatos:
        registro = chamar(cliente, "GET", f"{caminho}/{candidatos[0]['id']}")
    else:
        criado = chamar(cliente, "POST", caminho, codigos=(201,), json=corpo or identidade)
        registro = chamar(cliente, "GET", f"{caminho}/{criado['id']}")
    if registro.get(campo_dono) != dono_id or not all(registro.get(k) == v for k, v in identidade.items()):
        raise DemonstracaoError("O registro relido não confirmou a identidade da demonstração")
    return registro


def listar_todos(cliente, caminho: str, **filtros) -> list[dict]:
    registros = []
    while True:
        pagina = chamar(cliente, "GET", caminho, params={**filtros, "offset": len(registros), "limite": 100})
        registros.extend(pagina)
        if len(pagina) < 100:
            return registros

CONTAS = {
    "ana": {"nome": "Ana — Demonstração", "email": "ana.demo@example.test", "tipo": "pessoa"},
    "bruno": {"nome": "Bruno — Demonstração", "email": "bruno.demo@example.test", "tipo": "pessoa"},
    "carla": {"nome": "Carla — Demonstração", "email": "carla.demo@example.test", "tipo": "pessoa"},
    "operador": {"nome": "Operador — Demonstração", "email": "operador.demo@example.test", "tipo": "ponto_coleta"},
}
MARCA = "Dados fictícios de demonstração Recicla/Reusa v2.1."


def provisionar_operador(settings, senha: str) -> str:
    """Única escrita administrativa: provisiona operador sem alterar conta existente."""
    from pymongo import MongoClient
    from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
    from app.services.usuario_service import UsuarioService
    from app.schemas.usuario import PontoColetaProvisionRequest
    from app.security.passwords import verify_password

    esperado = CONTAS["operador"]
    with MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000) as mongo:
        if not mongo.admin.command("hello").get("setName"):
            raise DemonstracaoError("A demonstração exige MongoDB replica set")
        repo = MongoUsuarioRepository(mongo[settings.mongo_database][settings.mongo_collection_usuarios])
        existente = repo.buscar_por_email(esperado["email"])
        if existente is not None:
            conferir_identidade({"id": existente.id, "nome": existente.nome, "email": existente.email, "tipo": existente.tipo}, esperado)
            if not verify_password(senha, existente.senha_hash):
                raise DemonstracaoError("Senha do operador existente difere; nada foi redefinido")
            return existente.id
        usuario = UsuarioService(repo).provisionar_ponto_coleta(PontoColetaProvisionRequest(
            **{k: esperado[k] for k in ("nome", "email")}, senha=senha, endereco=ENDERECO,
        ))
        relido = repo.buscar_por_id(usuario.id)
        if relido is None or relido.email != esperado["email"]:
            raise DemonstracaoError("Operador provisionado não foi confirmado no banco")
        return usuario.id


# Dono, título, modalidade, situação final, contraparte opcional.
CENARIOS = (
    ("ana", "Notebook em preparação", "doacao", "rascunho", None),
    ("ana", "Monitor para doar", "doacao", "disponivel", None),
    ("ana", "Notebook usado à venda", "revenda", "disponivel", None),
    ("ana", "Teclado reservado", "doacao", "reservado", "bruno"),
    ("ana", "Celular entregue aguardando confirmação", "doacao", "aguardando_confirmacao", "bruno"),
    ("ana", "Tablet doado e recebido", "doacao", "concluido", "bruno"),
    ("ana", "Impressora aguardando ponto", "descarte", "aguardando_ponto", None),
    ("ana", "Televisor com entrega prevista", "descarte", "entrega_prevista", None),
    ("ana", "Periféricos recebidos no ponto", "descarte", "recebido", None),
    ("ana", "Monitor com destinação informada", "descarte", "destinacao_informada", None),
    ("carla", "Notebook de Carla para doação", "doacao", "disponivel", "ana"),
    ("bruno", "Notebook vendido para Ana", "revenda", "concluido", "ana"),
)


def povoar(clientes: dict, perfis: dict) -> dict:
    """Cria os cenários pela API e relê cada efeito; não apaga nem reinicia ciclos."""
    operador = clientes["operador"]
    ponto = garantir_registro(
        operador, "/api/pontos-coleta", listar_todos(operador, "/api/pontos-coleta", escopo="meus"),
        {"nome": "Ponto Escola — Demonstração"}, "responsavel_id", perfis["operador"]["id"],
        corpo={"nome": "Ponto Escola — Demonstração", "endereco": ENDERECO,
               "categorias_aceitas": ["informatica", "notebook", "monitor", "impressora", "televisao", "perifericos"],
               "horario_atendimento": "Demonstração fictícia: segunda a sexta, 08h às 17h"},
    )
    if not ponto.get("ativo"):
        raise DemonstracaoError("O ponto demo foi inativado; não será reativado automaticamente")
    registros = {}
    for dono, titulo, destino, alvo, contraparte in CENARIOS:
        cliente = clientes[dono]
        titulo = "[Demo] " + titulo
        existentes = []
        for grupo in ("ativos", "em_andamento", "encerrados"):
            existentes.extend(listar_todos(cliente, "/api/itens/meus", grupo=grupo))
        item = garantir_registro(
            cliente, "/api/itens", existentes, {"titulo": titulo, "descricao": MARCA},
            "proprietario_id", perfis[dono]["id"],
            corpo={"titulo": titulo, "descricao": MARCA, "categoria": "notebook" if destino != "descarte" else "perifericos",
                   "marca": "Marca fictícia", "modelo": "Modelo de demonstração", "condicao": "funcional" if destino != "descarte" else "sem_conserto",
                   "destino": destino, "valor": 350.0 if destino == "revenda" else None,
                   "especificacoes": {"origem": "Demonstração", "memoria": "8 GB"}, "publicar": alvo != "rascunho"},
        )
        item_id = item["id"]
        if item["destino"] != destino:
            raise DemonstracaoError("Modalidade de um item demo foi alterada; carga interrompida")
        if contraparte:
            pessoa = clientes[contraparte]
            interesses = listar_todos(pessoa, "/api/interesses", escopo="meus", item_id=item_id)
            interesse = garantir_registro(
                pessoa, "/api/interesses", interesses, {"item_id": item_id}, "usuario_id", perfis[contraparte]["id"],
            )
            if alvo != "disponivel":
                if item["status"] == "disponivel" and interesse["status"] == "pendente":
                    chamar(cliente, "POST", f"/api/interesses/{interesse['id']}/acoes", json={"acao": "selecionar"})
                    interesse = chamar(pessoa, "GET", f"/api/interesses/{interesse['id']}")
                    item = chamar(cliente, "GET", f"/api/itens/{item_id}")
                if item["status"] == "reservado" and interesse["status"] == "selecionado":
                    combinacao = interesse.get("combinacao")
                    if not combinacao:
                        chamar(cliente, "PUT", f"/api/interesses/{interesse['id']}/combinacao", json={
                            "local_texto": "Portaria fictícia da escola — demonstração", "observacao": "Combinação com dados fictícios"})
                        interesse = chamar(pessoa, "GET", f"/api/interesses/{interesse['id']}")
                        combinacao = interesse["combinacao"]
                    if combinacao["proposto_por"] != perfis[dono]["id"]:
                        raise DemonstracaoError("Combinação demo foi alterada; não será substituída")
                    if not combinacao.get("aceito_por"):
                        chamar(pessoa, "POST", f"/api/interesses/{interesse['id']}/combinacao/aceite", json={"revisao": combinacao["revisao"]})
                        interesse = chamar(pessoa, "GET", f"/api/interesses/{interesse['id']}")
                    if interesse["combinacao"]["aceito_por"] != perfis[contraparte]["id"]:
                        raise DemonstracaoError("Aceite demo não confirmado pela contraparte")
                    if alvo in ("aguardando_confirmacao", "concluido"):
                        chamar(cliente, "POST", f"/api/itens/{item_id}/entrega")
                        item = chamar(cliente, "GET", f"/api/itens/{item_id}")
                if alvo == "concluido" and item["status"] == "aguardando_confirmacao":
                    chamar(pessoa, "POST", f"/api/itens/{item_id}/recebimento")
        elif alvo in ("entrega_prevista", "recebido"):
            tentativas = listar_todos(cliente, "/api/encaminhamentos", item_id=item_id)
            if not tentativas and item["status"] == "aguardando_ponto":
                criada = chamar(cliente, "POST", "/api/encaminhamentos", codigos=(201,), json={"item_id": item_id, "ponto_id": ponto["id"]})
                tentativas = [chamar(cliente, "GET", f"/api/encaminhamentos/{criada['id']}")]
            if len(tentativas) != 1 or tentativas[0]["ponto_id"] != ponto["id"]:
                raise DemonstracaoError("Tentativa demo alterada ou ambígua; nada será refeito")
            tentativa = tentativas[0]
            if alvo == "recebido" and tentativa["status"] == "entrega_prevista":
                chamar(operador, "POST", f"/api/encaminhamentos/{tentativa['id']}/acoes", json={"acao": "receber"})
                tentativa = chamar(operador, "GET", f"/api/encaminhamentos/{tentativa['id']}")
                if tentativa["status"] != "recebido":
                    raise DemonstracaoError("Recebimento no ponto não foi confirmado")
        elif alvo == "destinacao_informada" and item["status"] == "aguardando_ponto":
            chamar(cliente, "POST", f"/api/itens/{item_id}/destinacao", json={
                "tipo_local": "ecoponto", "nome": "Ecoponto fictício do bairro", "cidade": "Maringá",
                "observacao": "Exemplo informado pelo autor; sem verificação externa"})
        relido = chamar(cliente, "GET", f"/api/itens/{item_id}")
        if relido["status"] != alvo:
            raise DemonstracaoError(f"Cenário {titulo}: estado atual {relido['status']}; esperado {alvo}. Não houve reset.")
        registros[titulo] = {"id": relido["id"], "status": relido["status"]}
    return {"itens": registros, "ponto_id": ponto["id"], "indicadores": chamar(clientes["ana"], "GET", "/api/indicadores")}

def main(argumentos=None) -> int:
    import argparse
    import os
    import sys
    import json
    from pathlib import Path
    from contextlib import ExitStack
    from urllib.parse import urlparse

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Cria dados; sem esta opção apenas descreve a carga")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--origin", default="http://127.0.0.1:8080")
    args = parser.parse_args(argumentos)
    if not args.aplicar:
        print(f"Plano: {len(CONTAS)} contas fictícias, {len(CENARIOS)} itens, um ponto e seus relacionamentos. Use --aplicar para gravar; nada é apagado.")
        return 0
    senha = os.environ.get("DEMO_SENHA", "")
    if len(senha) < 8:
        print("Defina DEMO_SENHA com ao menos oito caracteres; não use uma senha real.", file=sys.stderr)
        return 1
    if urlparse(args.api_url).hostname not in ("127.0.0.1", "localhost", "::1"):
        print("O povoamento é permitido apenas em uma API local.", file=sys.stderr)
        return 1
    from app.config import Settings
    from pymongo.errors import PyMongoError
    settings = Settings()
    try:
        with ExitStack() as stack:
            clientes = {k: stack.enter_context(httpx.Client(base_url=args.api_url, headers={"Origin": args.origin}, timeout=20)) for k in CONTAS}
            esquema = chamar(clientes["ana"], "GET", "/openapi.json")
            if "/api/encaminhamentos" not in esquema.get("paths", {}) or "/api/itens/{item_id}/destinacao" not in esquema["paths"]:
                raise DemonstracaoError("Atualize o backend para a v2.1 antes de povoar")
            # Se o operador já autentica, comprovar o ID da API no banco antes de escrever.
            from pymongo import MongoClient
            r = clientes["operador"].post("/api/auth/login", json={"email": CONTAS["operador"]["email"], "senha": senha})
            if r.status_code == 200:
                perfil = chamar(clientes["operador"], "GET", "/api/usuarios/me")
                conferir_identidade(perfil, CONTAS["operador"])
                with MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000) as mongo:
                    from bson import ObjectId
                    doc = mongo[settings.mongo_database][settings.mongo_collection_usuarios].find_one({"_id": ObjectId(perfil["id"]), "email": perfil["email"]})
                    if doc is None:
                        raise DemonstracaoError("MONGO_DATABASE/MONGO_URI não correspondem à API")
            elif r.status_code != 401:
                raise DemonstracaoError("Não foi possível conferir a conta operacional")
            operador_id = provisionar_operador(settings, senha)
            perfis = {k: garantir_conta(clientes[k], v, senha) for k, v in CONTAS.items()}
            if perfis["operador"]["id"] != operador_id:
                raise DemonstracaoError("API e banco não confirmaram o mesmo operador")
            resultado = povoar(clientes, perfis)
            print(json.dumps(resultado, ensure_ascii=False, indent=2))
            print("Demonstração confirmada. Contas:")
            for conta in CONTAS.values():
                print(f"  {conta['email']} ({conta['tipo']})")
            print("Senha: valor fornecido em DEMO_SENHA. Nenhuma senha existente foi redefinida.")
        return 0
    except (DemonstracaoError, httpx.HTTPError, PyMongoError):
        print("Carga interrompida: confira a API, a identidade das contas, o banco configurado e os estados demo. Dados existentes não foram apagados; pode haver carga parcial. Não houve redefinição de contas.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
