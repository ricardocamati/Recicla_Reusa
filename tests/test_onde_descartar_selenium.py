"""Consulta pública no navegador: módulos reais e API isolada controlável."""
import json
import time
from urllib.parse import parse_qs, urlsplit

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select

from tests.test_selenium_frontend import (
    ServidorApi, navegador, servidor_api, servidor_frontend,
)


def local(indice):
    return {
        "id": f"{indice:024x}", "nome": f"Local {indice:03}",
        "endereco": {"logradouro": "Rua Pública & Reuso", "numero": str(indice),
                     "complemento": "Bloco A", "cep": "87000000", "cidade": "Maringá"},
        "categorias_aceitas": ["notebook"], "horario_atendimento": "8h às 17h",
    }


@pytest.fixture
def diretorio_api(monkeypatch, servidor_api):
    estado = {"locais": [local(i) for i in range(1, 46)], "usuario": None,
              "erro": False, "indisponivel": False, "atraso": 0, "pedidos": []}

    def obter(handler):
        url = urlsplit(handler.path);query = parse_qs(url.query)
        estado["pedidos"].append(("GET", url.path, query))
        if url.path == "/api/usuarios/me":
            handler._responder(200 if estado["usuario"] else 401,
                               estado["usuario"] or {"detail": "Não autenticado"})
            return
        if url.path.startswith("/api/pontos-coleta"):
            if estado["atraso"]:time.sleep(estado["atraso"])
            if estado["erro"]:
                handler._responder(503, {"detail": "Consulta indisponível"});return
            if url.path == "/api/pontos-coleta":
                locais = estado["locais"]
                if "cidade" in query:
                    locais = [p for p in locais if p["endereco"]["cidade"].casefold() == query["cidade"][0].strip().casefold()]
                if "categoria" in query:
                    locais = [p for p in locais if query["categoria"][0] in p["categorias_aceitas"]]
                inicio = int(query.get("offset", [0])[0]);limite = int(query.get("limite", [20])[0])
                handler._responder(200, locais[inicio:inicio+limite]);return
            ponto = next((p for p in estado["locais"] if p["id"] == url.path.rsplit("/", 1)[-1]), None)
            handler._responder(200 if ponto and not estado["indisponivel"] else 404,
                               ponto if ponto and not estado["indisponivel"] else {"detail": "Não encontrado"})
            return
        handler._responder(404, {"detail": "Não encontrado"})

    def mutar(handler):
        estado["pedidos"].append((handler.command, handler.path, {}))
        handler._responder(405, {"detail": "Consulta não deve escrever"})
    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    for metodo in ["POST", "PUT", "PATCH", "DELETE"]:
        monkeypatch.setattr(ServidorApi, "do_"+metodo, mutar, raising=False)
    return estado


def abrir(navegador, servidor_frontend, servidor_api, consulta=""):
    navegador.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};",
    })
    navegador.get(servidor_frontend+"/onde-descartar.html"+consulta)
    return WebDriverWait(navegador, 8)


def test_visitante_abre_diretorio_sem_login_item_cookie_ou_escrita(
    navegador, servidor_frontend, servidor_api, diretorio_api,
):
    espera = abrir(navegador, servidor_frontend, servidor_api)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    assert "onde-descartar.html" in navegador.current_url
    assert navegador.find_element(By.TAG_NAME, "h1").text == "Onde descartar"
    assert "Local 001" in navegador.find_element(By.ID, "directory-list").text
    assert "Rua Pública & Reuso" in navegador.find_element(By.ID, "directory-list").text
    assert not navegador.get_cookies()
    assert diretorio_api["pedidos"] and all(m == "GET" for m, _, _ in diretorio_api["pedidos"])
    assert all(p == "/api/usuarios/me" or p.startswith("/api/pontos-coleta") for _, p, _ in diretorio_api["pedidos"])
    assert not navegador.find_elements(By.CSS_SELECTOR, "#item-form, #register-form, #login-form")


def test_filtros_cumulativos_paginacao_url_recarrega_e_reinicia(
    navegador, servidor_frontend, servidor_api, diretorio_api,
):
    outros = [{**local(100+i), "categorias_aceitas": ["monitor"],
               "endereco": {**local(i)["endereco"], "cidade": "Londrina"}} for i in range(105)]
    diretorio_api["locais"] = outros + diretorio_api["locais"]
    espera = abrir(navegador, servidor_frontend, servidor_api,
                   "?cidade=Maring%C3%A1&categoria=notebook&offset=20&escopo=meus&item_id=privado")
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local 021")
    assert navegador.find_element(By.ID, "directory-city").get_attribute("value") == "Maringá"
    assert Select(navegador.find_element(By.ID, "directory-category")).first_selected_option.get_attribute("value") == "notebook"
    assert len(navegador.find_elements(By.CSS_SELECTOR, "#directory-list article")) == 20
    pedido = [q for _, p, q in diretorio_api["pedidos"] if p == "/api/pontos-coleta"][-1]
    assert pedido == {"cidade": ["Maringá"], "categoria": ["notebook"], "offset": ["20"], "limite": ["21"]}
    navegador.find_element(By.ID, "directory-next").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local 041")
    assert not navegador.find_element(By.ID, "directory-next").is_enabled()
    navegador.refresh()
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local 041")
    cidade = navegador.find_element(By.ID, "directory-city");cidade.clear();cidade.send_keys("Sem locais", Keys.ENTER)
    espera.until(lambda d: "Nenhum local" in d.find_element(By.ID, "directory-message").text)
    assert parse_qs(urlsplit(navegador.current_url).query).get("offset", ["0"]) == ["0"]
    assert not navegador.find_elements(By.CSS_SELECTOR, "#directory-list article")
    navegador.find_element(By.ID, "directory-clear").click()
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    assert not navegador.find_element(By.ID, "directory-city").get_attribute("value")
    assert Select(navegador.find_element(By.ID, "directory-category")).first_selected_option.get_attribute("value") == ""


@pytest.mark.parametrize("copia", ["ok", "negada", "ausente"])
def test_detalhe_copia_fallback_e_retorno_preservam_filtros_e_pagina(
    navegador, servidor_frontend, servidor_api, diretorio_api, copia,
):
    diretorio_api["locais"][20]["horario_atendimento"] = None
    diretorio_api["locais"][20]["responsavel_id"] = "NAO_EXIBIR_RESPONSAVEL"
    codigo = 'undefined' if copia == "ausente" else ('{writeText: async texto => {' + ('throw new Error("negada");' if copia == "negada" else 'window.enderecoCopiado = texto;') + '}}')
    navegador.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": 'Object.defineProperty(navigator, "clipboard", {configurable: true, value: '+codigo+'});',
    })
    espera = abrir(navegador, servidor_frontend, servidor_api, "?cidade=Maring%C3%A1&categoria=notebook&offset=20")
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    navegador.find_element(By.CSS_SELECTOR, ".directory-detail-link").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_elements(By.ID, "directory-copy"))
    assert "local=" in navegador.current_url
    texto = navegador.find_element(By.ID, "directory-detail").text
    assert "Local 021" in texto and "Bloco A" in texto and "Horário não informado" in texto
    assert "NAO_EXIBIR_RESPONSAVEL" not in navegador.find_element(By.TAG_NAME, "body").text
    navegador.find_element(By.ID, "directory-copy").send_keys(Keys.ENTER)
    if copia == "ok":
        espera.until(lambda d: "Endereço copiado" in d.find_element(By.ID, "directory-copy-message").text)
        assert "Rua Pública & Reuso" in navegador.execute_script("return window.enderecoCopiado")
    else:
        espera.until(lambda d: "Selecione" in d.find_element(By.ID, "directory-copy-message").text)
        assert "Rua Pública & Reuso" in navegador.execute_script("return window.getSelection().toString()")
        assert navegador.switch_to.active_element.get_attribute("class") == "directory-address"
    navegador.find_element(By.ID, "directory-back").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local 021")
    query = parse_qs(urlsplit(navegador.current_url).query)
    assert query["cidade"] == ["Maringá"] and query["categoria"] == ["notebook"] and query["offset"] == ["20"]
    assert "local" not in query
    assert all(m == "GET" for m, _, _ in diretorio_api["pedidos"])


def test_local_inativado_apos_lista_mantem_retorno_sem_fallback_de_item(
    navegador, servidor_frontend, servidor_api, diretorio_api,
):
    espera = abrir(navegador, servidor_frontend, servidor_api, "?categoria=notebook&offset=20")
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    diretorio_api["indisponivel"] = True
    navegador.find_element(By.CSS_SELECTOR, ".directory-detail-link").send_keys(Keys.ENTER)
    espera.until(lambda d: "não está disponível" in d.find_element(By.ID, "directory-message").text)
    assert navegador.find_element(By.ID, "directory-back").is_displayed()
    assert not navegador.find_elements(By.ID, "directory-copy")
    assert "Nenhum local" not in navegador.find_element(By.ID, "directory-message").text
    navegador.find_element(By.ID, "directory-back").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    assert parse_qs(urlsplit(navegador.current_url).query)["offset"] == ["20"]


def test_carregamento_erro_e_nova_tentativa_nao_simulam_vazio(
    navegador, servidor_frontend, servidor_api, diretorio_api,
):
    diretorio_api.update(erro=True, atraso=1)
    espera = abrir(navegador, servidor_frontend, servidor_api)
    assert "Carregando" in navegador.find_element(By.ID, "directory-message").text
    assert navegador.find_element(By.ID, "directory-list").get_attribute("aria-busy") == "true"
    espera.until(lambda d: d.find_element(By.ID, "directory-retry").is_displayed())
    assert "Nenhum local" not in navegador.find_element(By.ID, "directory-message").text
    assert not navegador.find_elements(By.CSS_SELECTOR, "#directory-list article")
    diretorio_api.update(erro=False, atraso=0)
    navegador.find_element(By.ID, "directory-retry").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    assert not navegador.find_element(By.ID, "directory-retry").is_displayed()


@pytest.mark.parametrize("pagina", ["index.html", "itens.html"])
def test_entrada_quero_descartar_abre_consulta_sem_formulario_de_item(
    navegador, servidor_frontend, servidor_api, diretorio_api, pagina,
):
    if pagina == "itens.html":diretorio_api["usuario"] = dict(ServidorApi.usuario)
    navegador.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};",
    })
    navegador.get(servidor_frontend+"/"+pagina)
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_elements(By.LINK_TEXT, "Quero descartar"))
    link = navegador.find_element(By.LINK_TEXT, "Quero descartar")
    assert urlsplit(link.get_attribute("href")).path.endswith("/onde-descartar.html")
    link.send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    assert "local" not in parse_qs(urlsplit(navegador.current_url).query)
    assert not navegador.find_elements(By.CSS_SELECTOR, "#item-form, #login-form")
    assert all(m == "GET" for m, _, _ in diretorio_api["pedidos"])


@pytest.mark.parametrize("largura", [320, 768, 1024, 1440])
def test_visitante_teclado_responsivo_texto_longo_sem_overflow(
    navegador, servidor_frontend, servidor_api, diretorio_api, largura,
):
    import struct
    from pathlib import Path
    diretorio_api["locais"][0]["nome"] = "Local de coleta de equipamentos eletrônicos "*3
    diretorio_api["locais"][0]["endereco"]["logradouro"] = "Rua de nome longo e público "*5
    navegador.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": largura, "height": 1000, "deviceScaleFactor": 1, "mobile": False,
    })
    espera = abrir(navegador, servidor_frontend, servidor_api)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
    assert navegador.execute_script("return window.innerWidth") == largura
    assert navegador.execute_script("return document.documentElement.scrollWidth <= window.innerWidth + 1")
    assert navegador.execute_script("return getComputedStyle(document.querySelector('#directory-list h3')).whiteSpace") == "normal"
    navegador.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)
    assert navegador.switch_to.active_element.text == "Ir para a consulta"
    navegador.switch_to.active_element.send_keys(Keys.ENTER, Keys.TAB)
    assert navegador.switch_to.active_element.get_attribute("id") == "directory-city"
    assert not [x for x in navegador.get_log("browser") if "Uncaught" in x["message"] or "SyntaxError" in x["message"]]
    imagem = navegador.get_screenshot_as_png();assert struct.unpack('!II', imagem[16:24]) == (largura, 1000)
    saida = Path(__file__).parents[1]/"artefatos/nao_versionados/etapa17-interface"
    saida.mkdir(parents=True, exist_ok=True);(saida/f"anonima-{largura}.png").write_bytes(imagem)
