"""Etapa 24: previsão em minutos e sem contagem de tentativas no card."""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.test_etapa22_interesses import (  # noqa: F401 - fixtures reutilizadas
    abrir_interesses,
    clicar,
    interesses_api,
    navegador,
    servidor_frontend,
)
from tests.test_etapa23_interesses import (  # noqa: F401 - fixture reutilizada
    botao_card,
    card,
    combinacao_api,
    texto_card,
)


@pytest.fixture()
def pagina(navegador, servidor_frontend, combinacao_api):
    estado, api = combinacao_api
    navegador.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/Sao_Paulo"})
    abrir_interesses(navegador, servidor_frontend, api)
    return estado


def test_formulario_mostra_previsao_em_minutos_sem_segundos(pagina, navegador):
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    campo = card(navegador).find_element(By.NAME, "previsao")
    assert campo.get_attribute("step") == "60"
    assert campo.get_attribute("value") == "2026-11-13T12:30"


def test_resumo_exibe_previsao_sem_segundos(pagina, navegador):
    resumo = card(navegador).text
    assert "12:30" in resumo
    assert "12:30:12" not in resumo


def test_salvar_sem_alterar_previsao_preserva_instante_original(pagina, navegador):
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    local = card(navegador).find_element(By.NAME, "local_texto")
    local.clear()
    local.send_keys("Portaria lateral")
    clicar(navegador, botao_card(navegador, "Salvar alteração"))
    WebDriverWait(navegador, 8).until(lambda d: "Combinação r3" in texto_card(d))
    assert pagina.salvamentos[0]["previsao"] == "2026-11-13T15:30:12.345Z"


def test_alterar_previsao_grava_minuto_escolhido(pagina, navegador):
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    navegador.execute_script(
        "document.querySelector('#meus-interesses-list form').previsao.value = '2026-11-14T14:05';"
    )
    clicar(navegador, botao_card(navegador, "Salvar alteração"))
    WebDriverWait(navegador, 8).until(lambda d: "Combinação r3" in texto_card(d))
    assert pagina.salvamentos[0]["previsao"] == "2026-11-14T17:05:00.000Z"


def test_limpar_previsao_envia_nulo(pagina, navegador):
    clicar(navegador, botao_card(navegador, "Alterar combinação"))
    navegador.execute_script(
        "document.querySelector('#meus-interesses-list form').previsao.value = '';"
    )
    clicar(navegador, botao_card(navegador, "Salvar alteração"))
    WebDriverWait(navegador, 8).until(lambda d: "Combinação r3" in texto_card(d))
    assert pagina.salvamentos[0]["previsao"] is None


@pytest.mark.parametrize("tentativa", [1, 3])
def test_detalhes_nao_exibem_tentativa(pagina, navegador, tentativa):
    pagina.meus[0]["tentativa"] = tentativa
    navegador.refresh()
    WebDriverWait(navegador, 8).until(lambda d: "Portaria principal" in texto_card(d))
    clicar(navegador, botao_card(navegador, "Ver detalhes"))
    assert "Tentativa" not in card(navegador).text
