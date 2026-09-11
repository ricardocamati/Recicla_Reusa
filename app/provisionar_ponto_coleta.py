from argparse import ArgumentParser
from collections.abc import Sequence
from getpass import getpass

from pymongo import MongoClient
from pydantic import ValidationError

from app.config import Settings
from app.exceptions import EmailDuplicadoError
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.schemas.usuario import PontoColetaProvisionRequest
from app.services.usuario_service import UsuarioService


def criar_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Provisiona uma conta operacional de ponto de coleta.",
    )
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--logradouro", required=True)
    parser.add_argument("--numero", required=True)
    parser.add_argument("--cep", required=True)
    parser.add_argument("--cidade", required=True)
    parser.add_argument("--complemento")
    return parser


def main(argumentos: Sequence[str] | None = None) -> int:
    parser = criar_parser()
    args = parser.parse_args(argumentos)
    senha = getpass("Senha do ponto de coleta: ")

    try:
        request = PontoColetaProvisionRequest(
            nome=args.nome,
            email=args.email,
            senha=senha,
            logradouro=args.logradouro,
            numero=args.numero,
            complemento=args.complemento,
            cep=args.cep,
            cidade=args.cidade,
        )
    except ValidationError as erro:
        parser.error(f"dados inválidos: {erro.errors()[0]['msg']}")

    settings = Settings()
    cliente = MongoClient(settings.mongo_uri)
    try:
        repositorio = MongoUsuarioRepository(
            cliente[settings.mongo_database][settings.mongo_collection_usuarios],
        )
        servico = UsuarioService(repositorio)
        usuario = servico.provisionar_ponto_coleta(request)
    except EmailDuplicadoError:
        parser.error("e-mail já cadastrado")
    finally:
        cliente.close()

    print(f"Ponto de coleta provisionado: {usuario.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
