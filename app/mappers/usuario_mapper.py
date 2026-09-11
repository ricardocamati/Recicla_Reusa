from app.models.usuario import Usuario
from app.schemas.usuario import (
    EnderecoSchema,
    PontoColetaProvisionRequest,
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioSummaryResponse,
    UsuarioUpdateRequest,
)
from app.security.passwords import hash_password


def campos_endereco(endereco: EnderecoSchema) -> dict[str, str | None]:
    """Converte o agrupamento HTTP em campos planos do modelo persistido."""
    return {
        "logradouro": endereco.logradouro,
        "numero": endereco.numero,
        "complemento": endereco.complemento,
        "cep": endereco.cep,
        "cidade": endereco.cidade,
    }


def endereco_para_schema(usuario: Usuario) -> EnderecoSchema:
    """Reconstrói o agrupamento do contrato HTTP sem criar subdocumento."""
    return EnderecoSchema(
        logradouro=usuario.logradouro,
        numero=usuario.numero,
        complemento=usuario.complemento,
        cep=usuario.cep,
        cidade=usuario.cidade,
    )


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
            **campos_endereco(request.endereco),
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
            endereco=endereco_para_schema(usuario),
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
        dados_endereco = campos_endereco(request.endereco)
        usuario.logradouro = dados_endereco["logradouro"]
        usuario.numero = dados_endereco["numero"]
        usuario.complemento = dados_endereco["complemento"]
        usuario.cep = dados_endereco["cep"]
        usuario.cidade = dados_endereco["cidade"]
        usuario.data_modificacao = instante
