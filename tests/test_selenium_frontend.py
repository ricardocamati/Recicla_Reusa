from functools import partial
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler
import json
from pathlib import Path
import re
import socketserver
import threading
from urllib.parse import parse_qs, urlsplit

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
    "interesses.html": "#meus-interesses-list",
    "notificacoes.html": "#notificacoes-list",
    "pontos.html": "#pontos-list",
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
        "tipo": "pessoa",
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
        if caminho in {"/api/interesses", "/api/notificacoes", "/api/pontos-coleta"}:
            self._responder(200, [])
            return
        if caminho == "/api/indicadores":
            self._responder(200, {"doados": 0, "coletados": 0, "vendidos": 0, "total": 0})
            return
        self._responder(404, {"detail": "Não encontrado"})


@pytest.mark.parametrize("tipo", ["pessoa", "ponto_coleta"])
def test_selenium_perfil_preenche_resumo_e_atualiza_cidade(
    navegador, servidor_frontend, servidor_api, monkeypatch, tipo,
):
    usuario = {**ServidorApi.usuario, "tipo": tipo, "endereco": dict(ServidorApi.usuario["endereco"])}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)

    def atualizar(handler):
        dados = json.loads(handler.rfile.read(int(handler.headers["Content-Length"])))
        atualizado = {**usuario, **dados}
        handler._responder(200, atualizado)

    monkeypatch.setattr(ServidorApi, "do_PUT", atualizar, raising=False)
    navegador.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};"},
    )
    navegador.get(f"{servidor_frontend}/perfil.html")
    espera = WebDriverWait(navegador, 5)
    espera.until(lambda driver: driver.find_element(By.NAME, "nome").get_attribute("value") == usuario["nome"])
    papel = "Pessoa" if tipo == "pessoa" else "Ponto de coleta"
    assert navegador.find_element(By.ID, "account-role").text == papel
    assert navegador.find_element(By.ID, "account-city").text == "Maringá"
    for elemento in ("role-description", "account-tip"):
        texto = navegador.find_element(By.ID, elemento).text
        assert texto and "Carregando" not in texto and texto != "..."
    cidade = navegador.find_element(By.NAME, "cidade")
    cidade.clear()
    cidade.send_keys("Sarandi")
    salvar = navegador.find_element(By.CSS_SELECTOR, "#profile-form button[type='submit']")
    navegador.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", salvar)
    salvar.click()
    espera.until(lambda driver: "sucesso" in driver.find_element(By.ID, "profile-message").text)
    assert navegador.find_element(By.ID, "account-city").text == "Sarandi"


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

@pytest.mark.parametrize("pagina", ["catalogo.html", "itens.html", "perfil.html"])
def test_selenium_menu_oferece_acesso_a_interesses(navegador, servidor_frontend, servidor_api, pagina):
    navegador.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};",
    })
    navegador.get(f"{servidor_frontend}/{pagina}")
    WebDriverWait(navegador, 5).until(lambda d: d.find_element(By.ID, "session-chip").get_attribute("textContent") == "Pessoa")
    links = navegador.find_elements(By.CSS_SELECTOR, ".header-actions a[href='./interesses.html']")
    assert len(links) == 1 and links[0].is_displayed()


@pytest.fixture()
def api_catalogo_com_relacoes(monkeypatch):
    item = {"id": "item-catalogo", "titulo": "Monitor para acompanhar", "descricao": "Oferta de teste",
            "destino": "doacao", "status": "disponivel", "proprietario_id": "outra-pessoa", "categoria": "monitor",
            "condicao": "funcional", "valor": None, "cidade_proprietario": "Maringá"}
    estado = {"item": item, "interesses": [], "posts": 0, "offsets": [], "post_status": 201}
    original = ServidorApi.do_GET

    def consultar(handler):
        url = urlsplit(handler.path)
        query = parse_qs(url.query)
        if url.path in ("/api/itens", "/api/itens/item-catalogo"):
            handler._responder(200, [item] if url.path == "/api/itens" else item)
        elif url.path == "/api/interesses":
            if query.get("escopo") == ["recebidos"]:
                handler._responder(200, [])
                return
            offset = int(query.get("offset", [0])[0]); limite = int(query.get("limite", [20])[0])
            estado["offsets"].append(offset)
            handler._responder(200, estado["interesses"][offset:offset + limite])
        else:
            original(handler)

    def criar(handler):
        assert urlsplit(handler.path).path == "/api/interesses"
        assert json.loads(handler.rfile.read(int(handler.headers["Content-Length"]))) == {"item_id": item["id"]}
        estado["posts"] += 1
        interesse = {"id": "interesse-1", "item_id": item["id"], "usuario_id": "selenium-user", "status": "pendente", "tentativa": 1}
        estado["interesses"].append(interesse)
        handler._responder(estado["post_status"], interesse if estado["post_status"] == 201 else {"detail": "Relação já existente"})

    monkeypatch.setattr(ServidorApi, "do_GET", consultar)
    monkeypatch.setattr(ServidorApi, "do_POST", criar, raising=False)
    return estado


def abrir_catalogo_teste(navegador, servidor_frontend, servidor_api):
    navegador.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};",
    })
    navegador.get(f"{servidor_frontend}/catalogo.html")
    WebDriverWait(navegador, 5).until(lambda d: d.find_elements(By.CSS_SELECTOR, "#catalog-list article"))


@pytest.mark.parametrize("resposta_post", [201, 409])
def test_selenium_interesse_registrado_vira_acompanhamento_e_persiste(
    navegador, servidor_frontend, servidor_api, api_catalogo_com_relacoes, resposta_post,
):
    estado = api_catalogo_com_relacoes
    estado["post_status"] = resposta_post
    abrir_catalogo_teste(navegador, servidor_frontend, servidor_api)
    botao = navegador.find_element(By.CSS_SELECTOR, "button[data-acao='interesse']")
    navegador.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", botao)
    botao.click()
    espera = WebDriverWait(navegador, 5)
    mensagem = "Interesse registrado" if resposta_post == 201 else "Seu interesse já está registrado"
    espera.until(lambda d: mensagem in d.find_element(By.ID, "catalog-message").text)
    assert not navegador.find_elements(By.CSS_SELECTOR, "button[data-acao='interesse']")
    assert navegador.find_element(By.CSS_SELECTOR, "#catalog-list a[data-acao='acompanhar-interesse']").is_displayed()
    navegador.refresh()
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#catalog-list a[data-acao='acompanhar-interesse']"))
    assert not navegador.find_elements(By.CSS_SELECTOR, "button[data-acao='interesse']")
    link = navegador.find_element(By.CSS_SELECTOR, "#catalog-list a[data-acao='acompanhar-interesse']")
    navegador.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", link)
    link.click()
    espera.until(lambda d: "Monitor para acompanhar" in d.find_element(By.ID, "meus-interesses-list").text)
    assert estado["posts"] == 1
    assert urlsplit(navegador.current_url).path.endswith("/interesses.html")


@pytest.mark.parametrize("status", ["pendente", "cancelado", "recusado"])
def test_selenium_relacao_existente_na_segunda_pagina_nao_oferece_novo_interesse(
    navegador, servidor_frontend, servidor_api, api_catalogo_com_relacoes, status,
):
    estado = api_catalogo_com_relacoes
    estado["interesses"] = [{"id": f"outro-{i}", "item_id": f"outro-item-{i}", "status": "pendente"} for i in range(100)]
    estado["interesses"].append({"id": "existente", "item_id": estado["item"]["id"], "status": status})
    abrir_catalogo_teste(navegador, servidor_frontend, servidor_api)
    assert not navegador.find_elements(By.CSS_SELECTOR, "button[data-acao='interesse']")
    assert navegador.find_elements(By.CSS_SELECTOR, "#catalog-list a[data-acao='acompanhar-interesse']")
    assert 100 in estado["offsets"]
    assert estado["posts"] == 0
    if status == "pendente":
        link = navegador.find_element(By.CSS_SELECTOR, "#catalog-list a[data-acao='acompanhar-interesse']")
        navegador.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", link)
        link.click()
        WebDriverWait(navegador, 10).until(
            lambda d: "Monitor para acompanhar" in d.find_element(By.ID, "meus-interesses-list").text
        )
