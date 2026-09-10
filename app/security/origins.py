from urllib.parse import urlsplit

from fastapi import Request

from app.security.sessions import SESSION_COOKIE_NAME

METODOS_MUTAVEIS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _origem_da_url(url: str) -> str | None:
    partes = urlsplit(url)
    if not partes.scheme or not partes.netloc:
        return None
    return f"{partes.scheme}://{partes.netloc}"


def _origem_da_requisicao(request: Request) -> str:
    return f"{request.url.scheme}://{request.url.netloc}"


def requisicao_com_sessao_mutavel(request: Request) -> bool:
    return request.method in METODOS_MUTAVEIS and SESSION_COOKIE_NAME in request.cookies


def origem_permitida(request: Request, origens_configuradas: list[str]) -> bool:
    origem_api = _origem_da_requisicao(request)
    origem = request.headers.get("origin")
    if origem is not None:
        return origem in origens_configuradas or origem == origem_api

    referer = request.headers.get("referer")
    if referer is None:
        return False
    origem_referer = _origem_da_url(referer)
    return origem_referer in origens_configuradas or origem_referer == origem_api
