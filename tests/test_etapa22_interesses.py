"""Etapa 22: interesses ativos separados do histórico.

Os testes usam um servidor HTTP falso e o Chrome headless já usados nos demais
testes de interface. Eles exercitam a tela real servida por ``frontend/``.
"""
import json
import threading
import socket
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.test_selenium_frontend import (  # noqa: F401 - fixtures do módulo
    ServidorThreading,
    navegador,
    servidor_frontend,
)


ITENS = {
    "item-ativo": {"id": "item-ativo", "titulo": "Notebook para doação", "destino": "doacao",
                   "categoria": "notebook", "status": "disponivel"},
    "item-cancelado": {"id": "item-cancelado", "titulo": "Monitor cancelado", "destino": "revenda",
                       "categoria": "monitor", "status": "disponivel"},
    "item-recebido": {"id": "item-recebido", "titulo": "Impressora recebida", "destino": "doacao",
                      "categoria": "impressora", "status": "disponivel"},
}


def _interesse(identificador, item_id, status, escopo="meus"):
    return {
        "id": identificador,
        "item_id": item_id,
        "usuario_id": "outra-pessoa" if escopo == "recebidos" else "selenium-user",
        "status": status,
        "tentativa": 1,
        "motivo": None,
        "combinacao": None,
        "historico": [],
        "data_adicao": "2026-11-01T10:00:00+00:00",
        "data_modificacao": "2026-11-01T10:00:00+00:00",
    }


class EstadoInteresses:
    def __init__(self):
        self.meus = [
            _interesse("i-pendente", "item-ativo", "pendente"),
            _interesse("i-cancelado", "item-cancelado", "cancelado"),
        ]
        self.recebidos = [
            _interesse("i-recebido-pendente", "item-recebido", "pendente", "recebidos"),
        ]
        self.itens = {k: dict(v) for k, v in ITENS.items()}
        self.acoes = []
        self.erro_acao = None
        self.perder_resposta = False
        self.erro_listagem = False
        self.falhar_releitura = False
        self.atraso_acao = 0
        self.pedidos = []

    def aplicar(self, interesse_id, acao):
        alvo = next((i for i in self.meus + self.recebidos if i["id"] == interesse_id), None)
        if alvo is None:
            return None
        transicoes = {"desistir": "cancelado", "retomar": "pendente", "selecionar": "selecionado",
                      "recusar": "recusado", "reabrir": "pendente", "liberar": "cancelado"}
        alvo["status"] = transicoes[acao]
        self.acoes.append((interesse_id, acao))
        return alvo


class ServidorInteresses(BaseHTTPRequestHandler):
    estado = EstadoInteresses()

    def log_message(self, *_args) -> None:
        return

    def _responder(self, status, payload):
        corpo = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(corpo)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", "*"))
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self):
        url = urlsplit(self.path)
        caminho = url.path
        if caminho == "/api/usuarios/me":
            self._responder(200, {"id": "selenium-user", "nome": "Usuário Selenium",
                                  "email": "selenium@example.com", "tipo": "pessoa",
                                  "endereco": {"logradouro": "Rua de Teste", "numero": "100",
                                               "complemento": None, "cep": "87000000",
                                               "cidade": "Maringá"}})
            return
        if caminho.startswith("/api/itens/"):
            item = self.estado.itens.get(caminho.rsplit("/", 1)[-1])
            self._responder(200, item) if item else self._responder(404, {"detail": "não encontrado"})
            return
        if caminho == "/api/itens":
            self._responder(200, [])
            return
        if caminho == "/api/interesses":
            escopo = parse_qs(url.query).get("escopo", ["meus"])[0]
            offset = int(parse_qs(url.query).get("offset", ["0"])[0])
            self.estado.pedidos.append((escopo, offset))
            if self.estado.erro_listagem:
                self._responder(503, {"detail": "Falha temporária de leitura"})
                return
            lista = self.estado.recebidos if escopo == "recebidos" else self.estado.meus
            self._responder(200, lista[offset:offset + 100])
            return
        if caminho in ("/api/notificacoes", "/api/pontos-coleta"):
            self._responder(200, [])
            return
        self._responder(404, {"detail": "não encontrado"})

    def do_POST(self):
        caminho = urlsplit(self.path).path
        partes = caminho.strip("/").split("/")
        if len(partes) == 4 and partes[:2] == ["api", "interesses"] and partes[3] == "acoes":
            corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.estado.atraso_acao:
                time.sleep(self.estado.atraso_acao)
            if self.estado.erro_acao:
                self._responder(self.estado.erro_acao, {"detail": "Ação recusada"})
                return
            alvo = self.estado.aplicar(partes[2], corpo["acao"])
            if self.estado.falhar_releitura:
                self.estado.erro_listagem = True
            if self.estado.perder_resposta:
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            self._responder(200, alvo) if alvo else self._responder(404, {"detail": "não encontrado"})
            return
        self._responder(404, {"detail": "não encontrado"})


@pytest.fixture()
def interesses_api(monkeypatch):
    estado = EstadoInteresses()
    monkeypatch.setattr(ServidorInteresses, "estado", estado)
    servidor = ServidorThreading(("127.0.0.1", 0), ServidorInteresses)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield estado, f"http://127.0.0.1:{servidor.server_address[1]}"
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=2)


def abrir_interesses(navegador, servidor_frontend, api):
    navegador.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": f"window.RECICLA_API_BASE = {json.dumps(api)};"},
    )
    navegador.get(f"{servidor_frontend}/interesses.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_element(By.ID, "logout-button").is_displayed())
    espera.until(lambda d: d.find_element(By.ID, "meus-message").text
                 and "Carregando" not in d.find_element(By.ID, "meus-message").text)
    return espera


def clicar(navegador, elemento):
    navegador.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", elemento)
    elemento.click()


def botao(navegador, texto, lista_id="meus-interesses-list"):
    return [b for b in navegador.find_elements(By.CSS_SELECTOR, f"#{lista_id} article button")
            if b.text == texto][0]


def titulos(navegador, lista_id="meus-interesses-list"):
    return navegador.execute_script(
        "return [...document.querySelectorAll('#' + arguments[0] + ' article h3')].map(e => e.textContent)",
        lista_id,
    )


def test_ativos_e_padrao_e_historico_mostra_cancelado(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    abrir_interesses(navegador, servidor_frontend, api)

    assert titulos(navegador) == ["Notebook para doação"]
    assert navegador.find_element(By.ID, "meus-filtro-ativos").get_attribute("aria-pressed") == "true"

    navegador.find_element(By.ID, "meus-filtro-historico").click()
    WebDriverWait(navegador, 5).until(lambda d: titulos(d) == ["Monitor cancelado"])
    assert navegador.find_element(By.ID, "meus-filtro-historico").get_attribute("aria-pressed") == "true"
    card = navegador.find_element(By.CSS_SELECTOR, "#meus-interesses-list article")
    assert "Cancelado" in card.text
    assert "Retomar" in card.text


def test_desistir_retira_da_lista_ativa_e_mantem_no_historico(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    abrir_interesses(navegador, servidor_frontend, api)

    clicar(navegador, botao(navegador, "Desistir"))

    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: "desistiu" in d.find_element(By.ID, "meus-message").text)
    assert titulos(navegador) == []
    assert estado.acoes == [("i-pendente", "desistir")]

    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: len(titulos(d)) == 2)
    assert set(titulos(navegador)) == {"Notebook para doação", "Monitor cancelado"}


def test_retomar_no_historico_devolve_o_card_aos_ativos(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    abrir_interesses(navegador, servidor_frontend, api)

    navegador.find_element(By.ID, "meus-filtro-historico").click()
    espera = WebDriverWait(navegador, 5)
    espera.until(lambda d: titulos(d) == ["Monitor cancelado"])

    clicar(navegador, botao(navegador, "Retomar"))
    espera.until(lambda d: ("i-cancelado", "retomar") in estado.acoes)
    espera.until(lambda d: titulos(d) == [])

    navegador.find_element(By.ID, "meus-filtro-ativos").click()
    espera.until(lambda d: set(titulos(d)) == {"Notebook para doação", "Monitor cancelado"})


def test_recebidos_tambem_tem_filtro_e_mantem_decisoes(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.recebidos.append(_interesse("i-recebido-recusado", "item-ativo", "recusado", "recebidos"))
    espera = abrir_interesses(navegador, servidor_frontend, api)

    espera.until(lambda d: d.find_element(By.ID, "recebidos-section").is_displayed())
    assert titulos(navegador, "recebidos-interesses-list") == ["Impressora recebida"]

    clicar(navegador, navegador.find_element(By.ID, "recebidos-filtro-historico"))
    espera.until(lambda d: titulos(d, "recebidos-interesses-list") == ["Notebook para doação"])
    card = navegador.find_element(By.CSS_SELECTOR, "#recebidos-interesses-list article")
    assert "Recusado" in card.text
    assert "Reabrir" in card.text


def test_contadores_paginacao_e_atualizar_preservam_filtro(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.meus = [_interesse(f"antigo-{n}", "item-cancelado", "encerrado") for n in range(100)]
    estado.meus += [_interesse("i-pendente", "item-ativo", "pendente")]
    espera = abrir_interesses(navegador, servidor_frontend, api)
    assert titulos(navegador) == ["Notebook para doação"]
    assert ("meus", 100) in estado.pedidos
    assert navegador.find_element(By.ID, "meus-count").text == "1 interesse(s) ativo(s)."
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: len(titulos(d)) == 100)
    assert navegador.find_element(By.ID, "meus-count").text == "100 interesse(s) no histórico."
    clicar(navegador, navegador.find_element(By.ID, "atualizar-meus"))
    espera.until(lambda d: d.find_element(By.ID, "meus-interesses-list").get_attribute("aria-busy") == "false")
    assert navegador.find_element(By.ID, "meus-filtro-historico").get_attribute("aria-pressed") == "true"
    assert len(titulos(navegador)) == 100


def test_reabrir_recebido_sai_do_historico(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.recebidos = [_interesse("r-recusado", "item-recebido", "recusado", "recebidos")]
    espera = abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, navegador.find_element(By.ID, "recebidos-filtro-historico"))
    espera.until(lambda d: titulos(d, "recebidos-interesses-list") == ["Impressora recebida"])
    clicar(navegador, botao(navegador, "Reabrir", "recebidos-interesses-list"))
    espera.until(lambda d: titulos(d, "recebidos-interesses-list") == [])
    assert estado.acoes == [("r-recusado", "reabrir")]
    clicar(navegador, navegador.find_element(By.ID, "recebidos-filtro-ativos"))
    espera.until(lambda d: titulos(d, "recebidos-interesses-list") == ["Impressora recebida"])
    assert navegador.find_element(By.ID, "recebidos-count").text == "1 interesse(s) ativo(s)."


def test_desistencia_negada_preserva_card(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.erro_acao = 409
    espera = abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao(navegador, "Desistir"))
    espera.until(lambda d: "Ação recusada" in d.find_element(By.ID, "meus-message").text)
    assert titulos(navegador) == ["Notebook para doação"]
    assert estado.acoes == []
    assert "desistiu" not in navegador.find_element(By.ID, "meus-message").text


def test_resposta_perdida_reconcilia_sem_repetir_mutacao(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.perder_resposta = True
    espera = abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao(navegador, "Desistir"))
    espera.until(lambda d: "desistiu" in d.find_element(By.ID, "meus-message").text)
    assert titulos(navegador) == []
    assert estado.acoes == [("i-pendente", "desistir")]
    assert navegador.find_element(By.ID, "meus-count").text == "0 interesse(s) ativo(s)."
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: len(titulos(d)) == 2)
    navegador.refresh()
    espera.until(lambda d: d.find_element(By.ID, "meus-interesses-list").get_attribute("aria-busy") == "false")
    assert titulos(navegador) == []
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: len(titulos(d)) == 2)


def test_post_confirmado_mas_releitura_falhou_nao_anuncia_sucesso(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.falhar_releitura = True
    espera = abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao(navegador, "Desistir"))
    espera.until(lambda d: "atualizar" in d.find_element(By.ID, "meus-message").text.lower())
    assert "desistiu" not in navegador.find_element(By.ID, "meus-message").text
    assert titulos(navegador) == ["Notebook para doação"]
    estado.erro_listagem = False
    clicar(navegador, navegador.find_element(By.ID, "atualizar-meus"))
    espera.until(lambda d: titulos(d) == [])


def test_falha_de_atualizacao_preserva_lista_e_filtro(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    espera = abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: titulos(d) == ["Monitor cancelado"])
    estado.erro_listagem = True
    clicar(navegador, navegador.find_element(By.ID, "atualizar-meus"))
    espera.until(lambda d: "Falha temporária" in d.find_element(By.ID, "meus-message").text)
    assert titulos(navegador) == ["Monitor cancelado"]
    assert navegador.find_element(By.ID, "meus-filtro-historico").get_attribute("aria-pressed") == "true"
    # Filtro local não depende de nova chamada de rede.
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-ativos"))
    espera.until(lambda d: titulos(d) == ["Notebook para doação"])


def test_vazios_indicam_historico_e_filtros_funcionam_por_teclado(navegador, servidor_frontend, interesses_api):
    from selenium.webdriver.common.keys import Keys
    estado, api = interesses_api
    estado.meus = [estado.meus[1]]
    espera = abrir_interesses(navegador, servidor_frontend, api)
    assert "Histórico" in navegador.find_element(By.ID, "meus-interesses-list").text
    assert navegador.find_element(By.ID, "meus-filtros").get_attribute("role") == "group"
    btn = navegador.find_element(By.ID, "meus-filtro-historico")
    btn.send_keys(Keys.ENTER)
    espera.until(lambda d: titulos(d) == ["Monitor cancelado"])
    assert btn.get_attribute("aria-pressed") == "true"
    assert navegador.execute_script("return document.activeElement.id") == "meus-filtro-historico"
    navegador.set_window_size(360, 900)
    assert navegador.execute_script("return document.documentElement.scrollWidth <= innerWidth")


def test_status_desconhecido_nao_desaparece(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.meus.append(_interesse("novo-status", "item-recebido", "futuro"))
    espera = abrir_interesses(navegador, servidor_frontend, api)
    assert "Impressora recebida" in titulos(navegador)
    assert "não reconhecida" in navegador.find_element(By.ID, "meus-interesses-list").text
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: "Monitor cancelado" in titulos(d))
    assert "Impressora recebida" in titulos(navegador)


def test_duplo_clique_nao_repete_desistencia_e_remove_foco_do_card(navegador, servidor_frontend, interesses_api):
    estado, api = interesses_api
    estado.atraso_acao = 1
    espera = abrir_interesses(navegador, servidor_frontend, api)
    btn = botao(navegador, "Desistir")
    navegador.execute_script("arguments[0].focus(); arguments[0].click(); arguments[0].click();", btn)
    espera.until(lambda d: "desistiu" in d.find_element(By.ID, "meus-message").text)
    assert estado.acoes == [("i-pendente", "desistir")]
    assert navegador.execute_script("return document.activeElement.id") == "meus-message"


@pytest.mark.parametrize("status_item", ["reservado", "concluido", "arquivado"])
def test_historico_nao_oferece_retomada_ou_reabertura_de_item_indisponivel(
    navegador, servidor_frontend, interesses_api, status_item,
):
    estado, api = interesses_api
    estado.recebidos = [_interesse("recusado", "item-cancelado", "recusado", "recebidos")]
    espera = abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
    espera.until(lambda d: "Monitor cancelado" in titulos(d))
    assert botao(navegador, "Retomar")
    # O refresh deve consultar novamente a situação do equipamento, não um cache antigo.
    estado.itens["item-cancelado"]["status"] = status_item
    clicar(navegador, navegador.find_element(By.ID, "atualizar-meus"))
    rotulo = {"reservado": "Reservado", "concluido": "Concluído", "arquivado": "Arquivado"}[status_item]
    espera.until(lambda d: f"Situação: {rotulo}" in d.find_element(By.ID, "meus-interesses-list").text)
    assert "Retomar" not in navegador.find_element(By.ID, "meus-interesses-list").text
    clicar(navegador, navegador.find_element(By.ID, "atualizar-recebidos"))
    espera.until(lambda d: d.find_element(By.ID, "recebidos-interesses-list").get_attribute("aria-busy") == "false")
    clicar(navegador, navegador.find_element(By.ID, "recebidos-filtro-historico"))
    espera.until(lambda d: "Monitor cancelado" in titulos(d, "recebidos-interesses-list"))
    assert "Reabrir" not in navegador.find_element(By.ID, "recebidos-interesses-list").text
