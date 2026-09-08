from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)


class UsuarioMapper:
    @staticmethod
    def para_modelo(request: UsuarioCreateRequest, *, data_cadastro) -> Usuario:
        return Usuario(
            nome=request.nome,
            email=request.email,
            tipo=request.tipo,
            cidade=request.cidade,
            data_cadastro=data_cadastro,
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
            cidade=usuario.cidade,
            data_cadastro=usuario.data_cadastro,
        )

    @staticmethod
    def para_resumo(usuario: Usuario) -> UsuarioSummaryResponse:
        if usuario.id is None:
            raise ValueError("Usuário persistido deve possuir identificador")
        return UsuarioSummaryResponse(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            tipo=usuario.tipo,
        )

    @staticmethod
    def atualizar_modelo(request: UsuarioUpdateRequest, usuario: Usuario) -> None:
        usuario.nome = request.nome
        usuario.email = request.email
        usuario.tipo = request.tipo
        usuario.cidade = request.cidade
