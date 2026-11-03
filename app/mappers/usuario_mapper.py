from dataclasses import asdict

from app.models.usuario import Endereco, Usuario
from app.schemas.usuario import (
    EnderecoRequest,
    EnderecoResponse,
    PontoColetaProvisionRequest,
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)
from app.security.passwords import hash_password


def _endereco_de_modelo(endereco: Endereco) -> EnderecoResponse:
    return EnderecoResponse(**asdict(endereco))


def _endereco_de_request(endereco: EnderecoRequest) -> Endereco:
    return Endereco(**endereco.model_dump())


class UsuarioMapper:
    @staticmethod
    def para_modelo(request: UsuarioCreateRequest, *, instante) -> Usuario:
        return UsuarioMapper._para_modelo(request, tipo=request.tipo, instante=instante)

    @staticmethod
    def para_modelo_ponto_coleta(
        request: PontoColetaProvisionRequest,
        *,
        instante,
    ) -> Usuario:
        return UsuarioMapper._para_modelo(request, tipo="ponto_coleta", instante=instante)

    @staticmethod
    def _para_modelo(request, *, tipo, instante) -> Usuario:
        return Usuario(
            nome=request.nome,
            email=request.email,
            tipo=tipo,
            endereco=_endereco_de_request(request.endereco),
            senha_hash=hash_password(request.senha),
            data_adicao=instante,
            data_modificacao=instante,
        )

    @staticmethod
    def para_resposta(usuario: Usuario) -> UsuarioResponse:
        if usuario.id is None:
            raise ValueError("Usuário persistido deve possuir identificador")
        return UsuarioResponse(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            tipo=usuario.tipo,
            endereco=_endereco_de_modelo(usuario.endereco),
            data_adicao=usuario.data_adicao,
            data_modificacao=usuario.data_modificacao,
        )

    @staticmethod
    def para_resumo(usuario: Usuario) -> UsuarioSummaryResponse:
        if usuario.id is None:
            raise ValueError("Usuário persistido deve possuir identificador")
        return UsuarioSummaryResponse(
            id=usuario.id,
            nome=usuario.nome,
            tipo=usuario.tipo,
            cidade=usuario.endereco.cidade,
        )

    @staticmethod
    def atualizar_modelo(request: UsuarioUpdateRequest, usuario: Usuario, *, instante) -> None:
        usuario.nome = request.nome
        usuario.email = request.email
        usuario.endereco = _endereco_de_request(request.endereco)
        usuario.data_modificacao = instante
