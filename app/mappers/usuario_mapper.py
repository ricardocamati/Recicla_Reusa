from app.models.usuario import Usuario
from app.schemas.usuario import (
    CamposEndereco,
    PontoColetaProvisionRequest,
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)
from app.security.passwords import hash_password


_NOMES_CAMPOS_ENDERECO = ("logradouro", "numero", "complemento", "cep", "cidade")


def campos_endereco(objeto: Usuario | CamposEndereco) -> dict[str, str | None]:
    """Extrai os campos de endereço sem criar uma estrutura aninhada."""

    return {nome: getattr(objeto, nome) for nome in _NOMES_CAMPOS_ENDERECO}


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
            **campos_endereco(request),
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
            **campos_endereco(usuario),
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
            cidade=usuario.cidade,
        )

    @staticmethod
    def atualizar_modelo(request: UsuarioUpdateRequest, usuario: Usuario, *, instante) -> None:
        usuario.nome = request.nome
        usuario.email = request.email
        for nome_campo, valor in campos_endereco(request).items():
            setattr(usuario, nome_campo, valor)
        usuario.data_modificacao = instante
