"""Servidor estático local com versão de assets e sem cache de páginas antigas."""
from argparse import ArgumentParser
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TIPOS_VERSIONADOS = {".html", ".js", ".css"}
REFERENCIA_LOCAL = re.compile(
    r'''(?P<aspas>["'])(?P<url>\.{1,2}/[^"'\s<>]+?\.(?:html|js|css)(?:\?[^"'\s<>#]*)?(?:\#[^"'\s<>]*)?)(?P=aspas)'''
)


def versao_dos_assets(pasta: Path) -> str:
    resumo = sha256()
    for arquivo in sorted(p for p in pasta.rglob("*") if p.is_file() and p.suffix in TIPOS_VERSIONADOS):
        resumo.update(arquivo.relative_to(pasta).as_posix().encode())
        resumo.update(b"\0")
        resumo.update(arquivo.read_bytes())
        resumo.update(b"\0")
    return resumo.hexdigest()[:12]


def versionar_referencias(texto: str, versao: str) -> str:
    def substituir(match):
        partes = urlsplit(match["url"])
        parametros = [(chave, valor) for chave, valor in parse_qsl(partes.query, keep_blank_values=True) if chave != "v"]
        parametros.append(("v", versao))
        url = urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(parametros), partes.fragment))
        return f'{match["aspas"]}{url}{match["aspas"]}'
    return REFERENCIA_LOCAL.sub(substituir, texto)


class ServidorFrontend(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, versao: str, **kwargs):
        self.versao = versao
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        # Não manter páginas/módulos de implantações diferentes no navegador.
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Frontend-Version", self.versao)
        super().end_headers()

    def send_head(self):
        caminho = Path(self.translate_path(self.path))
        if caminho.is_dir():
            caminho = caminho / "index.html"
        if not caminho.is_file() or caminho.suffix not in TIPOS_VERSIONADOS:
            return super().send_head()
        conteudo = caminho.read_text(encoding="utf-8")
        if caminho.suffix in {".html", ".js"}:
            conteudo = versionar_referencias(conteudo, self.versao)
        corpo = conteudo.encode("utf-8")
        # Não responder 304 com base na data do HTML, pois seus imports podem mudar.
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(caminho)) + "; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        return BytesIO(corpo)


def criar_servidor(host: str, porta: int, pasta: Path) -> ThreadingHTTPServer:
    pasta = Path(pasta).resolve()
    handler = partial(ServidorFrontend, directory=str(pasta), versao=versao_dos_assets(pasta))
    return ThreadingHTTPServer((host, porta), handler)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("porta", type=int, nargs="?", default=5500)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--directory", type=Path, default=Path(__file__).parent)
    argumentos = parser.parse_args()
    with criar_servidor(argumentos.bind, argumentos.porta, argumentos.directory) as servidor:
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
