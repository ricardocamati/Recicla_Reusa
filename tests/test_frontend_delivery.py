"""Entrega do frontend: invalidar assets antigos sem depender de limpar o navegador."""
from contextlib import contextmanager
from pathlib import Path
import re
import threading

import httpx


@contextmanager
def servir(pasta):
    from frontend.servidor import criar_servidor

    servidor = criar_servidor("127.0.0.1", 0, pasta)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_address[1]}"
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=2)


def preparar(pasta):
    (pasta / "js").mkdir()
    (pasta / "index.html").write_text('<a href="./perfil.html">Perfil</a><script type="module" src="./js/main.js"></script><link rel="stylesheet" href="./styles.css">', encoding="utf-8")
    (pasta / "js/main.js").write_text('import { texto } from "./comum.js"; document.body.dataset.texto = texto;', encoding="utf-8")
    (pasta / "js/comum.js").write_text('export const texto = "atual";', encoding="utf-8")
    (pasta / "styles.css").write_text('body { color: green; }', encoding="utf-8")


def test_frontend_nao_devolve_304_nem_permite_cache_local(tmp_path):
    preparar(tmp_path)
    with servir(tmp_path) as url:
        for caminho in ("/index.html", "/js/main.js", "/styles.css"):
            resposta = httpx.get(url + caminho, headers={"If-Modified-Since": "Wed, 01 Jan 2031 00:00:00 GMT"})
            assert resposta.status_code == 200
            assert "no-store" in resposta.headers["Cache-Control"]


def test_frontend_versiona_html_estilos_e_imports_sem_editar_fontes(tmp_path):
    preparar(tmp_path)
    original = (tmp_path / "index.html").read_bytes()
    with servir(tmp_path) as url:
        html = httpx.get(url + "/index.html").text
        versao = re.search(r'main.js\?v=([0-9a-f]{12})', html).group(1)
        assert f'./styles.css?v={versao}' in html
        assert f'./perfil.html?v={versao}' in html
        js = httpx.get(url + f"/js/main.js?v={versao}").text
        assert f'./comum.js?v={versao}' in js
    assert (tmp_path / "index.html").read_bytes() == original


def test_alterar_modulo_compartilhado_invalida_versao_da_entrega(tmp_path):
    preparar(tmp_path)
    with servir(tmp_path) as url:
        antes = httpx.get(url + "/index.html").text
    (tmp_path / "js/comum.js").write_text('export const texto = "corrigido";', encoding="utf-8")
    with servir(tmp_path) as url:
        depois = httpx.get(url + "/index.html").text
    assert antes != depois
