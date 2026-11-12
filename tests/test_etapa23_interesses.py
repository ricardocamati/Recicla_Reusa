"""Etapa 23: cards compactos e combinação aberta somente por ação explícita."""
import json
import time
import socket

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.test_etapa22_interesses import (  # noqa: F401 - fixtures reutilizadas
    ServidorInteresses,
    _interesse,
    abrir_interesses,
    clicar,
    interesses_api,
    navegador,
    servidor_frontend,
)


@pytest.fixture()
def combinacao_api(interesses_api, monkeypatch):
    estado, api = interesses_api
    estado.meus = [_interesse("selecionado-meu", "item-ativo", "selecionado")]
    estado.recebidos = [_interesse("selecionado-recebido", "item-recebido", "selecionado", "recebidos")]
    for interesse in estado.meus + estado.recebidos:
        estado.itens[interesse["item_id"]]["status"] = "reservado"
        interesse["combinacao"] = {
            "local_texto": "Portaria principal",
            "previsao": "2026-11-13T15:30:12.345Z",
            "observacao": "Levar embalagem",
            "revisao": 2,
            "proposto_por": "selenium-user",
            "proposto_em": "2026-11-11T12:00:00Z",
            "aceito_por": None,
            "aceito_em": None,
        }
    estado.salvamentos = []
    estado.erro_put = None
    estado.atraso_put = 0
    estado.perder_put = False
    estado.falhar_releitura_put = False

    def salvar(handler):
        dados = json.loads(handler.rfile.read(int(handler.headers["Content-Length"])))
        if estado.atraso_put:
            time.sleep(estado.atraso_put)
        if estado.erro_put:
            handler._responder(estado.erro_put, {"detail": "Não foi possível alterar a combinação"})
            return
        identificador = handler.path.split("/")[-2]
        interesse = next(i for i in estado.meus + estado.recebidos if i["id"] == identificador)
        atual = interesse["combinacao"] or {}
        interesse["combinacao"] = {**dados, "revisao": atual.get("revisao", 0) + 1,
                                  "proposto_por": "selenium-user", "aceito_por": None}
        estado.salvamentos.append(dados)
        if estado.falhar_releitura_put:
            estado.erro_listagem = True
        if estado.perder_put:
            handler.close_connection = True
            handler.connection.shutdown(socket.SHUT_RDWR)
            handler.connection.close()
            return
        handler._responder(200, interesse)

    estado.aceites = []
    original_post = ServidorInteresses.do_POST
    def aceitar(handler):
        if not handler.path.endswith("/combinacao/aceite"):
            return original_post(handler)
        dados = json.loads(handler.rfile.read(int(handler.headers["Content-Length"])))
        identificador = handler.path.split("/")[-3]
        interesse = next(i for i in estado.meus + estado.recebidos if i["id"] == identificador)
        combinacao = interesse["combinacao"]
        estado.aceites.append(dados)
        if dados["revisao"] != combinacao["revisao"]:
            handler._responder(409, {"detail": "Combinação alterada; revise a proposta atual"})
            return
        if combinacao["proposto_por"] == "selenium-user":
            handler._responder(403, {"detail": "Quem propôs não aceita a própria revisão"})
            return
        combinacao["aceito_por"] = "selenium-user"
        handler._responder(200, interesse)
    monkeypatch.setattr(ServidorInteresses, "do_PUT", salvar, raising=False)
    monkeypatch.setattr(ServidorInteresses, "do_POST", aceitar)
    return estado, api


def card(driver, recebido=False):
    lista = "recebidos-interesses-list" if recebido else "meus-interesses-list"
    return driver.find_element(By.CSS_SELECTOR, f"#{lista} article")


def texto_card(driver, recebido=False):
    lista = "recebidos-interesses-list" if recebido else "meus-interesses-list"
    return driver.execute_script("return document.querySelector('#' + arguments[0] + ' article')?.innerText || ''", lista)


def botao_card(driver, texto, recebido=False):
    return next(b for b in card(driver, recebido).find_elements(By.TAG_NAME, "button")
                if b.is_displayed() and b.text == texto)


@pytest.mark.parametrize("recebido", [False, True])
def test_card_inicia_compacto_com_resumo_e_sem_edicao(
    navegador, servidor_frontend, combinacao_api, recebido,
):
    _, api = combinacao_api
    abrir_interesses(navegador, servidor_frontend, api)
    WebDriverWait(navegador, 8).until(lambda d: d.find_element(By.ID, "recebidos-section").is_displayed())
    atual = card(navegador, recebido)
    assert not any(e.is_displayed() for e in atual.find_elements(By.CSS_SELECTOR, "form.combination-form"))
    assert "Portaria principal" in atual.text
    assert "Levar embalagem" in atual.text
    assert "aguardando aceite da outra pessoa" in atual.text
    assert "Liberar reserva" not in atual.text
    assert botao_card(navegador, "Ver detalhes", recebido)
    assert botao_card(navegador, "Alterar combinação", recebido)


def test_edicao_preenche_valores_e_cancelar_nao_grava(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    navegador.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/Sao_Paulo"})
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    formulario = card(navegador).find_element(By.CSS_SELECTOR, "form.combination-form")
    assert formulario.is_displayed()
    assert formulario.find_element(By.NAME, "local_texto").get_attribute("value") == "Portaria principal"
    assert formulario.find_element(By.NAME, "previsao").get_attribute("value") == "2026-11-13T12:30"
    assert formulario.find_element(By.NAME, "observacao").get_attribute("value") == "Levar embalagem"
    local = formulario.find_element(By.NAME, "local_texto")
    local.clear()
    local.send_keys("Não deve ser salvo")
    clicar(navegador, botao_card(navegador, "Cancelar edição"))
    assert not formulario.is_displayed()
    assert navegador.execute_script("return document.activeElement.textContent") == "Alterar combinação"
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    assert formulario.find_element(By.NAME, "local_texto").get_attribute("value") == "Portaria principal"
    assert estado.meus[0]["combinacao"]["revisao"] == 2
    assert estado.acoes == []


def test_detalhes_recolhem_e_liberar_reserva_fica_na_area_expandida(navegador, servidor_frontend, combinacao_api):
    _, api = combinacao_api
    abrir_interesses(navegador, servidor_frontend, api)
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_element(By.ID, "recebidos-section").is_displayed())
    toggle = botao_card(navegador, "Ver detalhes", True)
    alvo = toggle.get_attribute("aria-controls")
    assert not navegador.find_element(By.ID, alvo).is_displayed()
    clicar(navegador, toggle)
    assert toggle.get_attribute("aria-expanded") == "true"
    assert botao_card(navegador, "Liberar reserva", True)
    clicar(navegador, botao_card(navegador, "Recolher", True))
    assert not navegador.find_element(By.ID, alvo).is_displayed()
    assert navegador.execute_script("return document.activeElement.id") != alvo


def test_salvar_recolhe_confirma_revisao_e_preserva_instante_utc(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    navegador.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/Sao_Paulo"})
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    local = card(navegador).find_element(By.NAME, "local_texto")
    local.clear()
    local.send_keys("Portaria lateral")
    clicar(navegador, botao_card(navegador, "Salvar alteração"))
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: "Combinação r3" in texto_card(d))
    assert "Portaria lateral" in card(navegador).text
    assert not card(navegador).find_element(By.CSS_SELECTOR, "form.combination-form").is_displayed()
    assert estado.salvamentos[0]["previsao"] == "2026-11-13T15:30:12.345Z"
    assert navegador.execute_script("return document.activeElement.textContent") == "Alterar combinação"


def test_duplo_envio_da_edicao_nao_duplica_revisao(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    estado.atraso_put = .7
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    navegador.execute_script("const f=document.querySelector('#meus-interesses-list form'); f.requestSubmit(); f.requestSubmit();")
    WebDriverWait(navegador, 8).until(lambda d: "Combinação r3" in texto_card(d))
    assert len(estado.salvamentos) == 1


@pytest.mark.parametrize("falha", ["validacao", "rede", "releitura"])
def test_falha_de_edicao_mantem_campos_sem_anunciar_sucesso(navegador, servidor_frontend, combinacao_api, falha):
    estado, api = combinacao_api
    estado.erro_put = 422 if falha == "validacao" else None
    estado.perder_put = falha == "rede"
    estado.falhar_releitura_put = falha == "releitura"
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    campo = card(navegador).find_element(By.NAME, "local_texto")
    campo.clear()
    campo.send_keys("Entrada preenchida")
    clicar(navegador, botao_card(navegador, "Salvar alteração"))
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: "error" in d.find_element(By.ID, "meus-message").get_attribute("class"))
    form = card(navegador).find_element(By.CSS_SELECTOR, "form.combination-form")
    assert form.is_displayed()
    assert form.find_element(By.NAME, "local_texto").get_attribute("value") == "Entrada preenchida"
    assert form.find_element(By.CSS_SELECTOR, "button[type=submit]").is_enabled()
    assert "success" not in navegador.find_element(By.ID, "meus-message").get_attribute("class")


def test_aceite_e_visivel_so_a_contraparte_sem_abrir_formulario(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    estado.meus[0]["combinacao"]["proposto_por"] = "outra-pessoa"
    abrir_interesses(navegador, servidor_frontend, api)
    assert "aguardando seu aceite" in card(navegador).text
    assert botao_card(navegador, "Aceitar combinação")
    assert not any(b.is_displayed() and b.text == "Aceitar combinação" for b in card(navegador, True).find_elements(By.TAG_NAME, "button"))
    clicar(navegador, botao_card(navegador, "Aceitar combinação"))
    WebDriverWait(navegador, 8).until(lambda d: "aceita" in texto_card(d) and "aguardando" not in texto_card(d))
    assert estado.aceites == [{"revisao": 2}]
    assert not card(navegador).find_element(By.CSS_SELECTOR, "form.combination-form").is_displayed()


def test_revisao_vencida_e_relida_sem_aceitar_automaticamente(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    estado.meus[0]["combinacao"]["proposto_por"] = "outra-pessoa"
    abrir_interesses(navegador, servidor_frontend, api)
    estado.meus[0]["combinacao"].update(revisao=3, local_texto="Nova revisão concorrente")
    clicar(navegador, botao_card(navegador, "Aceitar combinação"))
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: "Combinação r3" in texto_card(d))
    assert "Nova revisão concorrente" in card(navegador).text
    assert estado.meus[0]["combinacao"]["aceito_por"] is None
    assert estado.aceites == [{"revisao": 2}]
    assert "revise" in navegador.find_element(By.ID, "meus-message").text


@pytest.mark.parametrize("status_interesse,status_item", [
    ("cancelado", "disponivel"), ("recusado", "disponivel"), ("encerrado", "concluido"),
    ("selecionado", "aguardando_confirmacao"), ("selecionado", "concluido"), ("selecionado", "arquivado"),
])
def test_estado_nao_editavel_nao_expoe_formulario_nem_liberacao(
    navegador, servidor_frontend, combinacao_api, status_interesse, status_item,
):
    estado, api = combinacao_api
    for i in estado.meus + estado.recebidos:
        i["status"] = status_interesse
        estado.itens[i["item_id"]]["status"] = status_item
    abrir_interesses(navegador, servidor_frontend, api)
    if status_interesse in ("cancelado", "recusado", "encerrado"):
        clicar(navegador, navegador.find_element(By.ID, "meus-filtro-historico"))
        clicar(navegador, navegador.find_element(By.ID, "recebidos-filtro-historico"))
    for recebido in [False, True]:
        atual = card(navegador, recebido)
        assert not atual.find_elements(By.CSS_SELECTOR, "form.combination-form, .combination-toggle")
        clicar(navegador, botao_card(navegador, "Ver detalhes", recebido))
        assert "Liberar reserva" not in card(navegador, recebido).text


def test_primeira_proposta_cancela_sem_registro(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    estado.meus[0]["combinacao"] = None
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Propor combinação"))
    assert card(navegador).find_element(By.NAME, "local_texto").get_attribute("value") == ""
    clicar(navegador, botao_card(navegador, "Cancelar edição"))
    assert estado.salvamentos == [] and estado.meus[0]["combinacao"] is None
    assert not card(navegador).find_element(By.CSS_SELECTOR, "form.combination-form").is_displayed()


def test_liberacao_recolhida_continua_exigindo_motivo(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Ver detalhes", True))
    clicar(navegador, botao_card(navegador, "Liberar reserva", True))
    navegador.switch_to.alert.dismiss()
    assert estado.acoes == []
    clicar(navegador, botao_card(navegador, "Liberar reserva", True))
    navegador.switch_to.alert.send_keys(" ")
    navegador.switch_to.alert.accept()
    WebDriverWait(navegador, 5).until(lambda d: "motivo" in d.find_element(By.ID, "recebidos-message").text.lower())
    assert estado.acoes == []


def test_controles_ocultos_nao_recebem_tab_e_layout_cabe_em_360(navegador, servidor_frontend, combinacao_api):
    from selenium.webdriver.common.keys import Keys
    estado, api = combinacao_api
    estado.itens["item-ativo"]["titulo"] = "Equipamento de informática com nome completo para identificar a oferta " * 3
    abrir_interesses(navegador, servidor_frontend, api)
    navegador.set_window_size(360, 900)
    toggle = botao_card(navegador, "Alterar combinação")
    controle = toggle.get_attribute("aria-controls")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert not navegador.find_element(By.ID, controle).is_displayed()
    toggle.send_keys(Keys.ENTER)
    assert toggle.get_attribute("aria-expanded") == "true"
    assert navegador.execute_script("return document.activeElement.name") == "local_texto"
    clicar(navegador, botao_card(navegador, "Cancelar edição"))
    assert toggle.get_attribute("aria-expanded") == "false"
    toggle.send_keys(Keys.TAB)
    assert navegador.execute_script("return !document.activeElement.closest('form.combination-form')")
    assert navegador.execute_script("return document.documentElement.scrollWidth <= innerWidth")
    assert card(navegador).find_element(By.TAG_NAME, "h3").value_of_css_property("white-space") != "nowrap"


def test_recolher_detalhes_fecha_tambem_edicao_sem_gravar(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    abrir_interesses(navegador, servidor_frontend, api)
    clicar(navegador, botao_card(navegador, "Ver detalhes"))
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    clicar(navegador, botao_card(navegador, "Recolher"))
    assert not card(navegador).find_element(By.CSS_SELECTOR, "form.combination-form").is_displayed()
    assert botao_card(navegador, "Alterar combinação").get_attribute("aria-expanded") == "false"
    assert estado.salvamentos == []


def test_verificador_de_jornadas_abre_edicao_antes_de_preencher(
    navegador, servidor_frontend, combinacao_api, monkeypatch,
):
    import importlib.util
    from pathlib import Path
    estado, api = combinacao_api
    abrir_interesses(navegador, servidor_frontend, api)
    monkeypatch.setenv("JORNADAS_MONGO_URI", "mongodb://127.0.0.1:1/?directConnection=true")
    caminho = Path(__file__).parents[1] / "scripts/validar_jornadas_v2.py"
    spec = importlib.util.spec_from_file_location("verificador_etapa23", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    try:
        modulo.FRONTEND = servidor_frontend
        verificador = modulo.Navegador.__new__(modulo.Navegador)
        verificador.driver = navegador
        verificador.espera = WebDriverWait(navegador, 8)
        verificador.propor_combinacao("meus-interesses-list", "Notebook para doação", "Portaria pelo verificador")
        assert estado.salvamentos[0]["local_texto"] == "Portaria pelo verificador"
    finally:
        modulo.cliente.close()
