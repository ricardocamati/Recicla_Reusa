from functools import partial
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler
import json
from pathlib import Path
import re
import socketserver
import threading
from urllib.parse import urlsplit

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


FRONTEND = Path(__file__).parents[1] / "frontend"
PAGINAS = {
    "index.html": ".hero",
    "cadastro.html": "#register-form",
    "login.html": "#login-form",
    "perfil.html": "#profile-form",
    "catalogo.html": "#catalog-form",
    "itens.html": "#item-form",
}


class ServidorThreading(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class ServidorFrontend(SimpleHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        return


class ServidorApi(BaseHTTPRequestHandler):
    usuario = {
        "id": "selenium-user",
        "nome": "Usuário Selenium",
        "email": "selenium@example.com",
        "tipo": "doador",
        "endereco": {
            "logradouro": "Rua de Teste",
            "numero": "100",
            "complemento": None,
            "cep": "87000000",
            "cidade": "Maringá",
        },
    }

    def log_message(self, *_args) -> None:
        return

    def _responder(self, status: int, payload: object) -> None:
        corpo = json.dumps(payload).encode("utf-8")
        origem = self.headers.get("Origin")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Access-Control-Allow-Origin", origem or "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(corpo)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", "*"))
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        caminho = urlsplit(self.path).path
        if caminho == "/api/usuarios/me":
            self._responder(200, self.usuario)
            return
        if caminho == "/api/itens":
            self._responder(200, [])
            return
        self._responder(404, {"detail": "Não encontrado"})


@pytest.fixture()
def servidor_frontend():
    handler = partial(ServidorFrontend, directory=str(FRONTEND))
    servidor = ServidorThreading(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_address[1]}"
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=2)


@pytest.fixture()
def servidor_api():
    servidor = ServidorThreading(("127.0.0.1", 0), ServidorApi)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_address[1]}"
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=2)


@pytest.fixture()
def navegador():
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument("--headless=new")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--window-size=1440,1000")

    candidatos = (
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
    )
    for candidato in candidatos:
        if candidato.is_file():
            opcoes.binary_location = str(candidato)
            break

    try:
        driver = webdriver.Chrome(options=opcoes)
    except WebDriverException as erro:
        pytest.skip(f"Chrome/Selenium indisponível: {erro}")

    try:
        yield driver
    finally:
        driver.quit()


def test_selenium_navega_nas_seis_telas_em_modo_escuro(
    navegador,
    servidor_frontend: str,
    servidor_api: str,
) -> None:
    navegador.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};"},
    )

    for pagina, seletor_principal in PAGINAS.items():
        navegador.get(f"{servidor_frontend}/{pagina}")
        WebDriverWait(navegador, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        WebDriverWait(navegador, 10).until(
            lambda driver: driver.find_element(By.CSS_SELECTOR, seletor_principal)
        )

        caminho_atual = urlsplit(navegador.current_url).path
        assert caminho_atual.endswith(f"/{pagina}")
        assert "Recicla/Reusa" in navegador.title
        assert navegador.find_element(By.CSS_SELECTOR, "link[rel='stylesheet']")
        assert navegador.execute_script(
            "return getComputedStyle(document.documentElement).colorScheme"
        ) == "dark"
        assert "13, 20, 16" in navegador.find_element(
            By.TAG_NAME, "body"
        ).value_of_css_property("background-color")

        texto = navegador.find_element(By.TAG_NAME, "body").text
        assert not re.search(r"poc|ods|consumo|acad[eê]mic|respons[aá]vel", texto, re.IGNORECASE)
