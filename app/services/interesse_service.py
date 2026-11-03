from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from app.exceptions import InteresseError
from app.mappers.interesse_mapper import InteresseMapper
from app.models.interesse import Interesse
from app.schemas.interesse import InteresseResponse


class RepositorioDeInteresses(Protocol):
    def buscar_usuario(self, usuario_id: str) -> dict[str, Any] | None: ...
    def buscar_item(self, item_id: str) -> dict[str, Any] | None: ...
    def criar(self, interesse: Interesse) -> Interesse: ...
    def listar(self, usuario_id: str, *, escopo: str = "meus", item_id: str | None = None, status: str | None = None, offset: int = 0, limite: int = 20) -> list[Interesse]: ...
    def buscar_por_id(self, interesse_id: str) -> Interesse | None: ...
    def decidir(self, interesse_id: str, status: str, usuario_id: str, instante: datetime) -> Interesse: ...


class InteresseService:
    def __init__(self, repositorio: RepositorioDeInteresses, *, relogio: Callable[[], datetime] | None = None) -> None:
        self._repositorio = repositorio
        self._relogio = relogio or (lambda: datetime.now(UTC))

    def criar(self, dados, usuario_id: str) -> InteresseResponse:
        usuario = self._usuario_valido(usuario_id)
        if usuario.get("tipo") not in {"doador", "beneficiario"}:
            raise InteresseError(403, "Este perfil não pode registrar interesses")
        item_id = dados.item_id if hasattr(dados, "item_id") else dados["item_id"]
        item = self._repositorio.buscar_item(item_id)
        if item is None:
            raise InteresseError(404, "Item não encontrado")
        if str(item.get("proprietario_id")) == usuario_id:
            raise InteresseError(400, "Não é permitido demonstrar interesse no próprio item")
        if item.get("destino") == "descarte":
            raise InteresseError(400, "Itens destinados a descarte não aceitam interesses")
        if item.get("status") != "disponivel" or item.get("interesse_aceito_id") is not None:
            raise InteresseError(409, "Item não está disponível")
        agora = self._relogio()
        interesse = Interesse(item_id=item_id, usuario_id=usuario_id, status="pendente", data_adicao=agora, data_modificacao=agora)
        return InteresseMapper.para_resposta(self._repositorio.criar(interesse))

    def listar(self, usuario_id: str, *, escopo: str = "meus", item_id: str | None = None, status: str | None = None, offset: int = 0, limite: int = 20) -> list[InteresseResponse]:
        usuario = self._usuario_valido(usuario_id)
        if escopo not in {"meus", "recebidos"}:
            raise InteresseError(400, "Escopo inválido")
        if escopo == "recebidos" and usuario.get("tipo") != "doador":
            raise InteresseError(403, "Somente doadores podem consultar interesses recebidos")
        rows = self._repositorio.listar(usuario_id, escopo=escopo, item_id=item_id, status=status, offset=offset, limite=limite)
        return [InteresseMapper.para_resposta(i) for i in rows]

    def buscar_por_id(self, interesse_id: str, usuario_id: str) -> InteresseResponse:
        self._usuario_valido(usuario_id)
        interesse = self._repositorio.buscar_por_id(interesse_id)
        if interesse is None:
            raise InteresseError(404, "Interesse não encontrado")
        item = self._repositorio.buscar_item(interesse.item_id)
        if item is None or (interesse.usuario_id != usuario_id and str(item.get("proprietario_id")) != usuario_id):
            raise InteresseError(404, "Interesse não encontrado")
        return InteresseMapper.para_resposta(interesse)

    def atualizar(self, interesse_id: str, dados, usuario_id: str) -> InteresseResponse:
        usuario = self._usuario_valido(usuario_id)
        if usuario.get("tipo") not in {"doador", "beneficiario"}:
            raise InteresseError(403, "Este perfil não pode alterar interesses")
        novo_status = dados.status if hasattr(dados, "status") else dados["status"]
        interesse = self._repositorio.decidir(interesse_id, novo_status, usuario_id, self._relogio())
        return InteresseMapper.para_resposta(interesse)

    def _usuario_valido(self, usuario_id: str) -> dict[str, Any]:
        usuario = self._repositorio.buscar_usuario(usuario_id)
        if usuario is None:
            raise InteresseError(404, "Usuário não encontrado")
        return usuario
