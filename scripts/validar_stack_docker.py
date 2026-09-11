from __future__ import annotations

import argparse
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SERVICOS_OBRIGATORIOS = {"mongo", "backend", "frontend"}


def executar(comando: list[str]) -> str:
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        check=False,
    )
    if resultado.returncode != 0:
        detalhe = resultado.stderr.strip() or resultado.stdout.strip()
        raise RuntimeError(f"comando retornou {resultado.returncode}: {detalhe}")
    return resultado.stdout.strip()


def consultar_http(url: str) -> tuple[int, int]:
    requisicao = Request(url, headers={"Accept": "text/html, application/json"})
    try:
        with urlopen(requisicao, timeout=10) as resposta:
            conteudo = resposta.read(1024)
            return resposta.status, len(conteudo)
    except (HTTPError, URLError, TimeoutError) as erro:
        raise RuntimeError(f"falha HTTP em {url}: {erro}") from erro


def criar_comando_compose(nome_projeto: str | None) -> list[str]:
    comando = ["docker", "compose"]
    if nome_projeto:
        comando.extend(["--project-name", nome_projeto])
    return comando


def verificar_stack(args: argparse.Namespace) -> int:
    compose = criar_comando_compose(args.project)
    falhas: list[str] = []

    def verificar(nome: str, funcao) -> None:
        try:
            funcao()
            print(f"{nome}=pass")
        except (OSError, RuntimeError) as erro:
            falhas.append(nome)
            print(f"{nome}=fail detalhe={erro}")

    verificar("compose_config", lambda: executar(compose + ["config", "--quiet"]))

    def servicos_ativos() -> None:
        servicos = set(executar(compose + ["ps", "--services", "--filter", "status=running"]).splitlines())
        ausentes = SERVICOS_OBRIGATORIOS - servicos
        if ausentes:
            raise RuntimeError(f"serviços não ativos: {', '.join(sorted(ausentes))}")

    verificar("compose_services", servicos_ativos)

    def mongo_ping() -> None:
        comando = compose + [
            "exec",
            "-T",
            "mongo",
            "sh",
            "-lc",
            'mongosh --quiet --host localhost --username "$MONGO_INITDB_ROOT_USERNAME" '
            '--password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin '
            "--eval 'db.adminCommand({ ping: 1 }).ok'",
        ]
        saida = executar(comando)
        if "1" not in saida:
            raise RuntimeError(f"ping inesperado: {saida}")

    verificar("mongo_ping", mongo_ping)

    def verificar_url(url: str) -> None:
        status, _ = consultar_http(url)
        if status != 200:
            raise RuntimeError(f"status HTTP {status}")

    for nome, url in (
        ("api_health", f"{args.api_url}/health"),
        ("api_docs", f"{args.api_url}/docs"),
        ("api_openapi", f"{args.api_url}/openapi.json"),
        ("api_usuarios", f"{args.api_url}/api/usuarios"),
        ("frontend_home", f"{args.frontend_url}/"),
        ("frontend_index", f"{args.frontend_url}/index.html"),
    ):
        verificar(
            nome,
            lambda url=url: verificar_url(url),
        )

    if falhas:
        print(f"stack_validation=fail count={len(falhas)}")
        return 1
    print("stack_validation=pass")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica uma stack Recicla/Reusa já iniciada pelo Docker Compose."
    )
    parser.add_argument("--project", help="nome opcional do projeto Compose")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:8080")
    return verificar_stack(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
