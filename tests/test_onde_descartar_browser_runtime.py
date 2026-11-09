"""Selenium -> HTTP real -> FastAPI -> replica set, em banco UUID descartável."""
import json
import socket
import threading

from bson import ObjectId
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from app.config import Settings
from tests.test_diretorio_runtime import snapshot
from tests.test_interesses_runtime import ambiente
from tests.test_pontos_coleta_v2 import INSTANTE
from tests.test_selenium_frontend import navegador, servidor_frontend


def test_browser_anonimo_filtra_pagina_abre_detalhe_sem_mudar_mongo(
    ambiente, navegador, servidor_frontend,
):
    banco = ambiente.banco
    colecao = banco[Settings().mongo_collection_pontos_coleta]
    dono = ObjectId()

    def documento(i, compativel=True):
        return {
            "_id": ObjectId(), "nome": f"Local real {i:03}" if compativel else f"Anterior {i:03}",
            "responsavel_id": dono, "ativo": True,
            "endereco": {"logradouro": "Rua pública da coleta", "numero": str(i),
                         "complemento": "Bloco B", "cep": "87000000", "cidade": "Maringá"},
            "categorias_aceitas": ["notebook"] if compativel else ["monitor"],
            "horario_atendimento": "Segunda a sexta, 9h às 16h",
            "data_adicao": INSTANTE, "data_modificacao": INSTANTE,
        }

    colecao.insert_many([documento(i, False) for i in range(105)] + [documento(i) for i in range(24)])
    colecao.insert_one({**documento(99), "ativo": False})
    antes = snapshot(banco)
    assert len(antes) == 5
    pedidos = []
    cors = CORSMiddleware(ambiente.app, allow_origins=[servidor_frontend],
                          allow_credentials=True, allow_methods=["GET"], allow_headers=["*"])

    async def aplicacao(scope, receive, send):
        if scope["type"] == "http":pedidos.append((scope["method"], scope["path"]))
        await cors(scope, receive, send)

    sock = socket.socket();sock.bind(("127.0.0.1", 0))
    porta = sock.getsockname()[1]
    servidor = uvicorn.Server(uvicorn.Config(aplicacao, host="127.0.0.1", port=porta,
                                             lifespan="off", log_level="error"))
    thread = threading.Thread(target=servidor.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    espera = WebDriverWait(navegador, 10)
    try:
        espera.until(lambda _: servidor.started)
        navegador.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": f"window.RECICLA_API_BASE = {json.dumps('http://127.0.0.1:'+str(porta))};",
        })
        navegador.get(servidor_frontend+"/onde-descartar.html")
        espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
        navegador.find_element(By.ID, "directory-city").send_keys("mArInGá")
        Select(navegador.find_element(By.ID, "directory-category")).select_by_value("notebook")
        navegador.find_element(By.ID, "directory-city").send_keys(Keys.ENTER)
        espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local real 000")
        navegador.find_element(By.ID, "directory-next").send_keys(Keys.ENTER)
        espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local real 020")
        assert len(navegador.find_elements(By.CSS_SELECTOR, "#directory-list article")) == 4
        assert not navegador.find_element(By.ID, "directory-next").is_enabled()
        navegador.find_element(By.CSS_SELECTOR, ".directory-detail-link").send_keys(Keys.ENTER)
        espera.until(lambda d: d.find_element(By.ID, "directory-detail").is_displayed() and "Local real 020" in d.find_element(By.ID, "directory-detail").text)
        assert "Bloco B" in navegador.find_element(By.ID, "directory-detail").text
        navegador.find_element(By.ID, "directory-back").send_keys(Keys.ENTER)
        espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local real 020")
        navegador.refresh()
        espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list h3") and d.find_element(By.CSS_SELECTOR, "#directory-list h3").text == "Local real 020")
        assert not navegador.get_cookies()
        assert pedidos and all(metodo == "GET" for metodo, _ in pedidos)
        assert all(caminho == "/api/usuarios/me" or caminho.startswith("/api/pontos-coleta") for _, caminho in pedidos)
        assert snapshot(banco) == antes
    finally:
        servidor.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive(), "servidor isolado não encerrou"
