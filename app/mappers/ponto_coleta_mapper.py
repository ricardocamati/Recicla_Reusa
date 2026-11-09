from dataclasses import asdict

from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Endereco
from app.schemas.ponto_coleta import (
    PontoColetaCreateRequest,
    PontoColetaPublicResponse,
    PontoColetaResponse,
    PontoColetaUpdateRequest,
)
from app.schemas.usuario import EnderecoResponse


class PontoColetaMapper:
    @staticmethod
    def para_modelo(
        request: PontoColetaCreateRequest,
        *,
        responsavel_id: str,
        instante,
    ) -> PontoColeta:
        return PontoColeta(
            nome=request.nome,
            endereco=Endereco(**request.endereco.model_dump()),
            categorias_aceitas=list(request.categorias_aceitas),
            horario_atendimento=request.horario_atendimento,
            responsavel_id=responsavel_id,
            data_adicao=instante,
            data_modificacao=instante,
        )

    @staticmethod
    def para_resposta(ponto: PontoColeta) -> PontoColetaResponse:
        if ponto.id is None:
            raise ValueError("Ponto persistido deve possuir identificador")
        return PontoColetaResponse(
            id=ponto.id,
            nome=ponto.nome,
            endereco=EnderecoResponse(**asdict(ponto.endereco)),
            categorias_aceitas=list(ponto.categorias_aceitas),
            horario_atendimento=ponto.horario_atendimento,
            responsavel_id=ponto.responsavel_id,
            ativo=ponto.ativo,
            data_adicao=ponto.data_adicao,
            data_modificacao=ponto.data_modificacao,
        )

    @staticmethod
    def para_resposta_publica(ponto: PontoColeta) -> PontoColetaPublicResponse:
        if ponto.id is None:
            raise ValueError("Ponto persistido deve possuir identificador")
        return PontoColetaPublicResponse(
            id=ponto.id,
            nome=ponto.nome,
            endereco=EnderecoResponse(**asdict(ponto.endereco)),
            categorias_aceitas=list(ponto.categorias_aceitas),
            horario_atendimento=ponto.horario_atendimento,
        )

    @staticmethod
    def atualizar_modelo(
        request: PontoColetaUpdateRequest,
        ponto: PontoColeta,
        *,
        instante,
    ) -> None:
        ponto.nome = request.nome
        ponto.endereco = Endereco(**request.endereco.model_dump())
        ponto.categorias_aceitas = list(request.categorias_aceitas)
        ponto.horario_atendimento = request.horario_atendimento
        ponto.data_modificacao = instante
