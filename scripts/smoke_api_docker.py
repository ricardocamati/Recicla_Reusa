from __future__ import annotations

import argparse
from http.cookiejar import CookieJar
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4


class ClienteApi:
    def __init__(self, base_url: str, origem: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self.origem = origem

    def requisitar(
        self,
        caminho: str,
        *,
        metodo: str = "GET",
        dados: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        corpo = None
        cabecalhos = {"Accept": "application/json", "Origin": self.origem}
        if dados is not None:
            corpo = json.dumps(dados).encode("utf-8")
            cabecalhos["Content-Type"] = "application/json"
        requisicao = Request(
            f"{self.base_url}{caminho}",
            data=corpo,
            headers=cabecalhos,
            method=metodo,
        )
        try:
            with self.opener.open(requisicao, timeout=15) as resposta:
                conteudo = resposta.read()
                return resposta.status, self._json(conteudo)
        except HTTPError as erro:
            return erro.code, self._json(erro.read())
        except (URLError, TimeoutError) as erro:
            raise RuntimeError(f"falha HTTP em {caminho}: {erro}") from erro

    @staticmethod
    def _json(conteudo: bytes) -> Any:
        if not conteudo:
            return None
        try:
            return json.loads(conteudo.decode("utf-8"))
        except json.JSONDecodeError:
            return conteudo.decode("utf-8", errors="replace")


def exigir(status: int, esperado: int | set[int], etapa: str) -> None:
    permitidos = {esperado} if isinstance(esperado, int) else esperado
    if status not in permitidos:
        esperado_texto = ",".join(str(valor) for valor in sorted(permitidos))
        raise RuntimeError(f"{etapa}: esperado {esperado_texto}, recebido {status}")


def payload_usuario(email: str) -> dict[str, Any]:
    return {
        "nome": "Smoke Docker",
        "email": email,
        "senha": "Smoke2026",
        "tipo": "doador",
        "endereco": {
            "logradouro": "Rua de Evidência",
            "numero": "100",
            "cep": "87000-000",
            "cidade": "Maringá",
        },
    }


def payload_item() -> dict[str, Any]:
    return {
        "titulo": "Item de evidência",
        "descricao": "Registro temporário da validação",
        "categoria": "informatica",
        "marca": "Marca",
        "modelo": "Modelo",
        "condicao": "funcional",
        "destino": "doacao",
        "valor": None,
    }


def executar_crud(args: argparse.Namespace) -> int:
    if not args.crud:
        print("Use --crud para autorizar o fluxo mutável e sua limpeza.")
        return 2

    cliente = ClienteApi(args.base_url, args.origin)
    email = f"smoke-{uuid4().hex}@example.com"
    senha = "Smoke2026"
    usuario_id: str | None = None
    item_id: str | None = None
    falha: Exception | None = None

    try:
        status, usuario = cliente.requisitar(
            "/api/usuarios",
            metodo="POST",
            dados=payload_usuario(email),
        )
        exigir(status, 201, "cadastro")
        usuario_id = usuario["id"]
        print("cadastro=201")

        status, _ = cliente.requisitar(
            "/api/auth/login",
            metodo="POST",
            dados={"email": email, "senha": senha},
        )
        exigir(status, 200, "login")
        print("login=200")

        status, _ = cliente.requisitar("/api/usuarios/me")
        exigir(status, 200, "perfil")
        print("me=200")

        status, item = cliente.requisitar(
            "/api/itens",
            metodo="POST",
            dados=payload_item(),
        )
        exigir(status, 201, "item_criacao")
        item_id = item["id"]
        print("item_criacao=201")

        status, _ = cliente.requisitar(
            f"/api/itens/{item_id}",
            metodo="PUT",
            dados={**payload_item(), "titulo": "Item atualizado"},
        )
        exigir(status, 200, "item_atualizacao")
        print("item_atualizacao=200")

        status, _ = cliente.requisitar(f"/api/itens/{item_id}", metodo="DELETE")
        exigir(status, 204, "item_exclusao")
        item_id = None
        print("item_exclusao=204")

        status, _ = cliente.requisitar("/api/auth/logout", metodo="POST")
        exigir(status, 204, "logout")
        print("logout=204")

        status, _ = cliente.requisitar("/api/usuarios/me")
        exigir(status, 401, "me_apos_logout")
        print("me_apos_logout=401")
    except (KeyError, RuntimeError, TypeError, ValueError) as erro:
        falha = erro
    finally:
        if usuario_id is not None:
            try:
                status_login, _ = cliente.requisitar(
                    "/api/auth/login",
                    metodo="POST",
                    dados={"email": email, "senha": senha},
                )
                if status_login == 200:
                    if item_id is not None:
                        status_item, _ = cliente.requisitar(
                            f"/api/itens/{item_id}",
                            metodo="DELETE",
                        )
                        if status_item in {204, 404}:
                            print(f"cleanup_item={status_item}")
                        else:
                            print(f"cleanup_item=fail status={status_item}")
                            if falha is None:
                                falha = RuntimeError("limpeza do item temporário falhou")
                    status_delete, _ = cliente.requisitar(
                        f"/api/usuarios/{usuario_id}",
                        metodo="DELETE",
                    )
                    if status_delete in {204, 404}:
                        print(f"cleanup_usuario={status_delete}")
                    else:
                        print(f"cleanup_usuario=fail status={status_delete}")
                        if falha is None:
                            falha = RuntimeError("limpeza do usuário temporário falhou")
                    cliente.requisitar("/api/auth/logout", metodo="POST")
                else:
                    print(f"cleanup_usuario=fail login_status={status_login}")
                    if falha is None:
                        falha = RuntimeError("não foi possível autenticar para limpar o usuário temporário")
            except (RuntimeError, TypeError, ValueError) as erro:
                print("cleanup_usuario=fail erro_de_rede")
                if falha is None:
                    falha = erro

    if falha is not None:
        print(f"smoke_crud=fail detalhe={falha}")
        return 1
    print("smoke_crud=pass")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa CRUD HTTP temporário contra uma stack Recicla/Reusa já iniciada."
    )
    parser.add_argument("--crud", action="store_true", help="habilita a criação e limpeza temporárias")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--origin", default="http://localhost:8080")
    return executar_crud(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
