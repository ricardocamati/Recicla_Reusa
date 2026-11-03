from datetime import UTC, datetime

import mongomock
import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.exceptions import PontoIncompativelError, ReferenciaAtivaError
from app.main import criar_app
from app.models.ponto_coleta import PontoColeta
from app.models.usuario import Endereco, Usuario
from app.repositories.mongo_ponto_coleta_repository import MongoPontoColetaRepository
from app.repositories.mongo_usuario_repository import MongoUsuarioRepository
from app.security.passwords import hash_password
from app.services.ponto_coleta_service import PontoColetaService
from tests.test_api_usuario import RepositorioEmMemoria

INSTANTE = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


class RepositorioPontosEmMemoria:
    def __init__(self) -> None:
        self.pontos: dict[str, PontoColeta] = {}
        self.proximo_id = 1

    def criar(self, ponto: PontoColeta) -> PontoColeta:
        ponto.id = f"ponto-{self.proximo_id}"
        self.proximo_id += 1
        self.pontos[ponto.id] = ponto
        return ponto

    def listar(
        self,
        *,
        cidade=None,
        categoria=None,
        responsavel_id=None,
        offset=0,
        limite=20,
    ) -> list[PontoColeta]:
        pontos = [
            ponto
            for ponto in self.pontos.values()
            if (not cidade or ponto.endereco.cidade.lower() == cidade.lower())
            and (not categoria or categoria in ponto.categorias_aceitas)
            and (not responsavel_id or ponto.responsavel_id == responsavel_id)
        ]
        return pontos[offset : offset + limite]

    def buscar_por_id(self, ponto_id: str) -> PontoColeta | None:
        return self.pontos.get(ponto_id)

    def atualizar(self, ponto: PontoColeta, *, responsavel_id: str) -> bool:
        if ponto.responsavel_id != responsavel_id:
            return False
        self.pontos[ponto.id or ""] = ponto
        return True

    def excluir(self, ponto_id: str, *, responsavel_id: str) -> bool:
        ponto = self.pontos.get(ponto_id)
        if ponto is None or ponto.responsavel_id != responsavel_id:
            return False
        del self.pontos[ponto_id]
        return True

    def contar_por_responsavel(self, responsavel_id: str) -> int:
        return sum(1 for p in self.pontos.values() if p.responsavel_id == responsavel_id)


PONTO = {
    "nome": "Ponto Centro",
    "endereco": {
        "logradouro": "Rua dos Pontos",
        "numero": "100",
        "cep": "87000-000",
        "cidade": "Maringá",
    },
    "categorias_aceitas": ["notebook", "celular"],
    "horario_atendimento": "Segunda a sexta, 8h às 17h",
}


def usuario(email: str, tipo: str) -> Usuario:
    return Usuario(
        nome=f"Usuário {email}",
        email=email,
        tipo=tipo,
        endereco=Endereco(
            logradouro="Rua A", numero="1", cep="87000000", cidade="Maringá", complemento=None
        ),
        senha_hash=hash_password("Senha123"),
        data_adicao=INSTANTE,
        data_modificacao=INSTANTE,
    )


def cliente(repositorio_usuarios, repositorio_pontos):
    return AsyncClient(
        transport=ASGITransport(
            app=criar_app(
                repositorio_usuarios,
                repositorio_pontos=repositorio_pontos,
                relogio=lambda: INSTANTE,
            )
        ),
        base_url="http://testserver",
        headers={"Origin": "http://localhost:5500"},
    )


@pytest.fixture
def usuarios() -> RepositorioEmMemoria:
    repo = RepositorioEmMemoria()
    repo.criar(usuario("operador@example.com", "ponto_coleta"))
    repo.criar(usuario("outro.operador@example.com", "ponto_coleta"))
    repo.criar(usuario("doador@example.com", "pessoa"))
    return repo


@pytest.fixture
def pontos() -> RepositorioPontosEmMemoria:
    return RepositorioPontosEmMemoria()


async def autenticar(api: AsyncClient, email: str) -> None:
    await api.post("/api/auth/login", json={"email": email, "senha": "Senha123"})


@pytest.mark.anyio
async def test_operador_cadastra_ponto_com_endereco_aninhado(usuarios, pontos) -> None:
    async with cliente(usuarios, pontos) as api:
        await autenticar(api, "operador@example.com")
        resposta = await api.post("/api/pontos-coleta", json=PONTO)
        listagem = await api.get("/api/pontos-coleta")

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["endereco"]["cep"] == "87000000"
    assert corpo["categorias_aceitas"] == ["notebook", "celular"]
    assert corpo["responsavel_id"] == usuarios.buscar_por_email("operador@example.com").id
    assert corpo["data_adicao"] == corpo["data_modificacao"]
    assert listagem.status_code == 200
    assert [ponto["id"] for ponto in listagem.json()] == [corpo["id"]]


@pytest.mark.anyio
async def test_doador_nao_cadastra_ponto(usuarios, pontos) -> None:
    async with cliente(usuarios, pontos) as api:
        await autenticar(api, "doador@example.com")
        resposta = await api.post("/api/pontos-coleta", json=PONTO)

    assert resposta.status_code == 403
    assert pontos.pontos == {}


@pytest.mark.anyio
async def test_categorias_invalidas_e_vazias_sao_rejeitadas(usuarios, pontos) -> None:
    async with cliente(usuarios, pontos) as api:
        await autenticar(api, "operador@example.com")
        vazia = await api.post("/api/pontos-coleta", json=PONTO | {"categorias_aceitas": []})
        repetida = await api.post(
            "/api/pontos-coleta",
            json=PONTO | {"categorias_aceitas": ["notebook", "notebook"]},
        )
        desconhecida = await api.post(
            "/api/pontos-coleta", json=PONTO | {"categorias_aceitas": ["fogao"]}
        )

    assert [vazia.status_code, repetida.status_code, desconhecida.status_code] == [400, 400, 400]
    assert pontos.pontos == {}


@pytest.mark.anyio
async def test_escopo_meus_e_propriedade_do_ponto(usuarios, pontos) -> None:
    async with cliente(usuarios, pontos) as api:
        await autenticar(api, "operador@example.com")
        criado = (await api.post("/api/pontos-coleta", json=PONTO)).json()
        meus = await api.get("/api/pontos-coleta", params={"escopo": "meus"})
        await api.post("/api/auth/logout")

        await autenticar(api, "outro.operador@example.com")
        alheios = await api.get("/api/pontos-coleta", params={"escopo": "meus"})
        alterar = await api.put(f"/api/pontos-coleta/{criado['id']}", json=PONTO)
        excluir = await api.delete(f"/api/pontos-coleta/{criado['id']}")

    assert [ponto["id"] for ponto in meus.json()] == [criado["id"]]
    assert alheios.json() == []
    assert alterar.status_code == 404
    assert excluir.status_code == 404
    assert criado["id"] in pontos.pontos


@pytest.mark.anyio
async def test_filtros_por_cidade_e_categoria(usuarios, pontos) -> None:
    async with cliente(usuarios, pontos) as api:
        await autenticar(api, "operador@example.com")
        await api.post("/api/pontos-coleta", json=PONTO)
        await api.post(
            "/api/pontos-coleta",
            json=PONTO
            | {
                "nome": "Ponto Norte",
                "categorias_aceitas": ["monitor"],
                "endereco": PONTO["endereco"] | {"cidade": "Londrina"},
            },
        )
        maringa = await api.get("/api/pontos-coleta", params={"cidade": "maringá"})
        monitores = await api.get("/api/pontos-coleta", params={"categoria": "monitor"})
        sem_resultado = await api.get("/api/pontos-coleta", params={"categoria": "tablet"})

    assert [ponto["nome"] for ponto in maringa.json()] == ["Ponto Centro"]
    assert [ponto["nome"] for ponto in monitores.json()] == ["Ponto Norte"]
    assert sem_resultado.json() == []


@pytest.mark.anyio
async def test_dono_atualiza_e_exclui_ponto(usuarios, pontos) -> None:
    async with cliente(usuarios, pontos) as api:
        await autenticar(api, "operador@example.com")
        criado = (await api.post("/api/pontos-coleta", json=PONTO)).json()
        atualizado = await api.put(
            f"/api/pontos-coleta/{criado['id']}",
            json=PONTO | {"nome": "Ponto Renomeado", "categorias_aceitas": ["celular"]},
        )
        removido = await api.delete(f"/api/pontos-coleta/{criado['id']}")
        depois = await api.get(f"/api/pontos-coleta/{criado['id']}")

    assert atualizado.status_code == 200
    assert atualizado.json()["nome"] == "Ponto Renomeado"
    assert atualizado.json()["categorias_aceitas"] == ["celular"]
    assert removido.status_code == 204
    assert depois.status_code == 404


def test_servico_recusa_categoria_incompativel() -> None:
    usuarios = RepositorioEmMemoria()
    usuarios.criar(usuario("operador@example.com", "ponto_coleta"))
    pontos = RepositorioPontosEmMemoria()
    servico = PontoColetaService(pontos, usuarios, relogio=lambda: INSTANTE)
    from app.schemas.ponto_coleta import PontoColetaCreateRequest

    criado = servico.criar(
        PontoColetaCreateRequest(**PONTO),
        responsavel_id=usuarios.buscar_por_email("operador@example.com").id,
    )

    assert servico.garantir_compatibilidade(criado.id, "notebook").id == criado.id
    with pytest.raises(PontoIncompativelError):
        servico.garantir_compatibilidade(criado.id, "monitor")


def test_repositorio_persiste_indices_e_endereco_aninhado() -> None:
    banco = mongomock.MongoClient(tz_aware=True).recicla_reusa
    repositorio = MongoPontoColetaRepository(banco.pontos_coleta)
    ponto = PontoColeta(
        nome="Ponto Centro",
        endereco=Endereco(
            logradouro="Rua dos Pontos", numero="100", cep="87000000", cidade="Maringá"
        ),
        categorias_aceitas=["notebook"],
        horario_atendimento="8h às 17h",
        responsavel_id=str(ObjectId()),
        data_adicao=INSTANTE,
        data_modificacao=INSTANTE,
    )
    criado = repositorio.criar(ponto)
    documento = banco.pontos_coleta.find_one({"_id": ObjectId(criado.id or "")})

    assert documento["endereco"] == {
        "logradouro": "Rua dos Pontos",
        "numero": "100",
        "complemento": None,
        "cep": "87000000",
        "cidade": "Maringá",
    }
    indices = banco.pontos_coleta.index_information()
    assert indices["ponto_responsavel"]["key"] == [("responsavel_id", 1)]
    assert indices["ponto_categorias"]["key"] == [("categorias_aceitas", 1)]
    assert indices["ponto_responsavel_nome"]["unique"] is True
    assert repositorio.contar_por_responsavel(ponto.responsavel_id) == 1


def test_exclusao_de_usuario_com_ponto_vinculado_e_bloqueada() -> None:
    banco = mongomock.MongoClient(tz_aware=True).recicla_reusa
    repositorio_usuarios = MongoUsuarioRepository(
        banco.usuarios, colecao_pontos_coleta=banco.pontos_coleta
    )
    repositorio_pontos = MongoPontoColetaRepository(banco.pontos_coleta)

    operador = repositorio_usuarios.criar(usuario("operador@example.com", "ponto_coleta"))
    repositorio_pontos.criar(
        PontoColeta(
            nome="Ponto Centro",
            endereco=Endereco(
                logradouro="Rua A", numero="1", cep="87000000", cidade="Maringá"
            ),
            categorias_aceitas=["notebook"],
            horario_atendimento="8h às 17h",
            responsavel_id=operador.id or "",
            data_adicao=INSTANTE,
            data_modificacao=INSTANTE,
        )
    )

    with pytest.raises(ReferenciaAtivaError):
        repositorio_usuarios.excluir(operador.id or "")
    assert repositorio_usuarios.buscar_por_id(operador.id or "") is not None
