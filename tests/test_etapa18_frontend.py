"""Testes frontend da Etapa 18 (gestão de locais do operador)."""
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select

from tests.test_selenium_frontend import (
    ServidorApi,
    navegador,
    servidor_api,
    servidor_frontend,
)


def _primeiro_texto(navegador, seletor):
    """Lê o primeiro resultado sem falhar quando a lista é re-renderizada."""
    try:
        elementos = navegador.find_elements(By.CSS_SELECTOR, seletor)
        return elementos[0].text if elementos else None
    except StaleElementReferenceException:
        return None


def _abrir(navegador, servidor_frontend, servidor_api, pagina):
    navegador.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": f"window.RECICLA_API_BASE = {json.dumps(servidor_api)};"},
    )
    navegador.get(f"{servidor_frontend}/{pagina}")


def test_etapa18_pessoa_recebe_acesso_negado_sem_get_de_locais(
    navegador, servidor_frontend, servidor_api, monkeypatch,
):
    pedidos = []
    usuario = {**ServidorApi.usuario, "tipo": "pessoa"}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)

    original = ServidorApi.do_GET

    def obter(handler):
        pedidos.append(urlsplit(handler.path).path)
        if urlsplit(handler.path).path == "/api/usuarios/me":
            handler._responder(200, usuario)
            return
        original(handler)

    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    _abrir(navegador, servidor_frontend, servidor_api, "pontos.html")
    espera = WebDriverWait(navegador, 5)
    espera.until(lambda d: d.find_element(By.ID, "pontos-acesso-negado").is_displayed())
    link = navegador.find_element(By.LINK_TEXT, "Onde descartar")
    assert link.is_displayed()
    assert "onde-descartar.html" in link.get_attribute("href")
    assert not any(caminho.startswith("/api/pontos-coleta") for caminho in pedidos)


def test_etapa18_operador_lista_paginada_e_inativos(navegador, servidor_frontend, servidor_api, monkeypatch):
    usuario = {**ServidorApi.usuario, "id": "op-1", "tipo": "ponto_coleta", "nome": "Operador"}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)

    locais = []
    for i in range(25):
        locais.append({
            "id": f"{i:024x}",
            "nome": f"Local {i:03}",
            "endereco": {"logradouro": "Rua X", "numero": str(i), "complemento": "Bloco", "cep": "87000000", "cidade": "Maringá"},
            "categorias_aceitas": ["notebook"],
            "horario_atendimento": "8h",
            "responsavel_id": "op-1",
            "ativo": i % 2 == 0,
        })

    pedidos = []

    def obter(handler):
        url = urlsplit(handler.path)
        if url.path == "/api/usuarios/me":
            handler._responder(200, usuario)
            return
        if url.path == "/api/pontos-coleta":
            query = parse_qs(url.query)
            pedidos.append((url.path, query))
            inicio = int(query.get("offset", ["0"])[0])
            limite = int(query.get("limite", ["20"])[0])
            ativo = query.get("ativo", [None])[0]
            filtrados = locais
            if ativo is not None:
                valor = ativo == "true"
                filtrados = [p for p in filtrados if p["ativo"] is valor]
            handler._responder(200, filtrados[inicio:inicio + limite])
            return
        handler._responder(404, {"detail": "Não encontrado"})

    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    _abrir(navegador, servidor_frontend, servidor_api, "pontos.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#pontos-list article")) == 20)
    assert len(navegador.find_elements(By.CSS_SELECTOR, "#pontos-list article")) == 20
    # lookahead: 21 solicitados? API recebe limite 21
    assert any(q.get("limite") == ["21"] for _, q in pedidos)
    # next
    navegador.find_element(By.ID, "ponto-next").send_keys(Keys.ENTER)
    espera.until(lambda d: _primeiro_texto(d, "#pontos-list h3") == "Local 020")
    # filtro inativos
    Select(navegador.find_element(By.ID, "filtro-ponto-ativo")).select_by_visible_text("Inativos")
    # submit via button
    navegador.find_element(By.CSS_SELECTOR, "#pontos-filtros button[type='submit']").send_keys(Keys.ENTER)
    espera.until(lambda d: _primeiro_texto(d, "#pontos-list h3") == "Local 001")
    # verifica query ativo=false no último pedido
    assert any(q.get("ativo") == ["false"] for _, q in pedidos)


def test_etapa18_criar_editar_ativar_e_falha_preserva_formulario(
    navegador, servidor_frontend, servidor_api, monkeypatch,
):
    usuario = {**ServidorApi.usuario, "id": "op-2", "tipo": "ponto_coleta", "nome": "Operador2"}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)

    estado = {"posts": 0, "puts": 0, "situacoes": 0, "ultimo_post": None, "ultimo_put": None, "pontos": []}

    def obter(handler):
        url = urlsplit(handler.path)
        if url.path == "/api/usuarios/me":
            handler._responder(200, usuario)
            return
        if url.path == "/api/pontos-coleta":
            handler._responder(200, estado["pontos"])
            return
        handler._responder(404, {"detail": "Não encontrado"})

    def criar(handler):
        body = json.loads(handler.rfile.read(int(handler.headers["Content-Length"])))
        estado["posts"] += 1
        estado["ultimo_post"] = body
        ponto = {
            "id": "ponto-1", "nome": body["nome"], "endereco": body["endereco"],
            "categorias_aceitas": body["categorias_aceitas"],
            "horario_atendimento": body["horario_atendimento"],
            "responsavel_id": "op-2", "ativo": True,
        }
        estado["pontos"] = [ponto]
        handler._responder(201, ponto)

    def atualizar(handler):
        body = json.loads(handler.rfile.read(int(handler.headers["Content-Length"])))
        estado["puts"] += 1
        estado["ultimo_put"] = body
        ponto = {
            "id": "ponto-1", "nome": body["nome"], "endereco": body["endereco"],
            "categorias_aceitas": body["categorias_aceitas"],
            "horario_atendimento": body["horario_atendimento"],
            "responsavel_id": "op-2", "ativo": True,
        }
        estado["pontos"] = [ponto]
        handler._responder(200, ponto)

    def situacao(handler):
        body = json.loads(handler.rfile.read(int(handler.headers["Content-Length"])))
        estado["situacoes"] += 1
        resposta = {
            "id": "ponto-1", "nome": "Local Editado", "endereco": {"logradouro": "Rua Y", "numero": "2", "complemento": None, "cep": "87000000", "cidade": "Maringá"},
            "categorias_aceitas": ["monitor"], "horario_atendimento": "9h",
            "responsavel_id": "op-2", "ativo": False,
        }
        estado["pontos"] = [resposta]
        handler._responder(200, resposta)

    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    monkeypatch.setattr(ServidorApi, "do_POST", criar, raising=False)
    monkeypatch.setattr(ServidorApi, "do_PUT", atualizar, raising=False)
    # situacao é POST em subpath; do_POST precisa distinguir. Wrap:
    original_post = ServidorApi.do_POST

    def post_roteador(handler):
        if "/situacao" in handler.path:
            situacao(handler)
        else:
            criar(handler)

    monkeypatch.setattr(ServidorApi, "do_POST", post_roteador, raising=False)

    _abrir(navegador, servidor_frontend, servidor_api, "pontos.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_element(By.ID, "ponto-admin").is_displayed())

    # criar
    form = navegador.find_element(By.ID, "ponto-form")
    form.find_element(By.NAME, "nome").send_keys("Local Novo")
    form.find_element(By.NAME, "logradouro").send_keys("Rua X")
    form.find_element(By.NAME, "numero").send_keys("10")
    form.find_element(By.NAME, "complemento").send_keys("Sala 2")
    form.find_element(By.NAME, "cep").send_keys("87000000")
    form.find_element(By.NAME, "cidade").send_keys("Maringá")
    select = form.find_element(By.NAME, "categorias_aceitas")
    for opt in select.find_elements(By.TAG_NAME, "option"):
        if opt.get_attribute("value") == "notebook":
            opt.click()
    form.find_element(By.NAME, "horario_atendimento").send_keys("8h às 17h")
    form.find_element(By.CSS_SELECTOR, "button[type='submit']").send_keys(Keys.ENTER)
    espera.until(lambda d: "cadastrado" in d.find_element(By.ID, "ponto-form-message").text.lower() or "Local" in d.find_element(By.ID, "pontos-list").text)
    assert estado["posts"] == 1
    assert estado["ultimo_post"].get("complemento") == "Sala 2" or estado["ultimo_post"]["endereco"]["complemento"] == "Sala 2"
    assert "responsavel_id" not in estado["ultimo_post"]
    assert "responsavel_id" not in estado["ultimo_post"].get("endereco", {})

    # editar
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "button[data-acao='editar']"))
    navegador.find_element(By.CSS_SELECTOR, "button[data-acao='editar']").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_element(By.NAME, "nome").get_attribute("value") == "Local Novo")
    nome = navegador.find_element(By.NAME, "nome")
    nome.clear()
    nome.send_keys("Local Editado")
    navegador.find_element(By.CSS_SELECTOR, "#ponto-form button[type='submit']").send_keys(Keys.ENTER)
    espera.until(lambda d: "atualizado" in d.find_element(By.ID, "ponto-form-message").text.lower())
    assert estado["puts"] == 1

    # ativar/inativar
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "button[data-acao='situacao']"))
    navegador.find_element(By.CSS_SELECTOR, "button[data-acao='situacao']").send_keys(Keys.ENTER)
    espera.until(lambda d: "desativado" in d.find_element(By.ID, "pontos-message").text.lower() or "ativado" in d.find_element(By.ID, "pontos-message").text.lower())
    assert estado["situacoes"] == 1

    # falha preserva formulário: simular 400 no próximo POST
    def falha(handler):
        handler._responder(400, {"detail": "Dados inválidos"})

    monkeypatch.setattr(ServidorApi, "do_POST", falha, raising=False)
    # limpar form e preencher
    if navegador.find_element(By.ID, "ponto-cancel-edit").is_displayed():
        navegador.find_element(By.ID, "ponto-cancel-edit").send_keys(Keys.ENTER)
    form2 = navegador.find_element(By.ID, "ponto-form")
    form2.find_element(By.NAME, "nome").send_keys("Falha")
    form2.find_element(By.NAME, "logradouro").send_keys("Rua Z")
    form2.find_element(By.NAME, "numero").send_keys("9")
    form2.find_element(By.NAME, "cep").send_keys("87000000")
    form2.find_element(By.NAME, "cidade").send_keys("Maringá")
    sel2 = form2.find_element(By.NAME, "categorias_aceitas")
    for opt in sel2.find_elements(By.TAG_NAME, "option"):
        if opt.get_attribute("value") == "monitor":
            opt.click()
    form2.find_element(By.NAME, "horario_atendimento").send_keys("9h às 18h")
    form2.find_element(By.CSS_SELECTOR, "button[type='submit']").send_keys(Keys.ENTER)
    espera.until(lambda d: "inválidos" in d.find_element(By.ID, "ponto-form-message").text or "Dados" in d.find_element(By.ID, "ponto-form-message").text)
    assert form2.find_element(By.NAME, "nome").get_attribute("value") == "Falha"


def test_etapa18_sem_aba_historico_descarte(navegador, servidor_frontend, servidor_api, monkeypatch):
    usuario = {**ServidorApi.usuario, "id": "pessoa-sem-hist", "tipo": "pessoa", "nome": "Pessoa Sem Hist"}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)

    def obter(handler):
        url = urlsplit(handler.path)
        if url.path == "/api/usuarios/me":
            handler._responder(200, usuario)
            return
        handler._responder(200, [])

    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    _abrir(navegador, servidor_frontend, servidor_api, "itens.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_element(By.ID, "my-items-list") is not None)
    assert not navegador.find_elements(By.CSS_SELECTOR, "[data-grupo='historico_descarte']")
    assert "Histórico de descarte" not in navegador.page_source


def test_etapa18_excluir_ultimo_item_ultima_pagina_volta_pagina_valida(
    navegador, servidor_frontend, servidor_api, monkeypatch,
):
    usuario = {**ServidorApi.usuario, "id": "op-pag", "tipo": "ponto_coleta", "nome": "Operador Pag"}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)

    locais = []
    for i in range(21):
        locais.append({
            "id": f"{i:024x}",
            "nome": f"Local {i:03}",
            "endereco": {"logradouro": "Rua X", "numero": str(i), "complemento": None, "cep": "87000000", "cidade": "Maringá"},
            "categorias_aceitas": ["notebook"],
            "horario_atendimento": "8h",
            "responsavel_id": "op-pag",
            "ativo": True,
        })

    def obter(handler):
        url = urlsplit(handler.path)
        if url.path == "/api/usuarios/me":
            handler._responder(200, usuario)
            return
        if url.path == "/api/pontos-coleta":
            query = parse_qs(url.query)
            inicio = int(query.get("offset", ["0"])[0])
            limite = int(query.get("limite", ["20"])[0])
            ativo = query.get("ativo", [None])[0]
            filtrados = locais
            if ativo is not None:
                valor = ativo == "true"
                filtrados = [p for p in filtrados if p["ativo"] is valor]
            handler._responder(200, filtrados[inicio:inicio + limite])
            return
        handler._responder(404, {"detail": "Não encontrado"})

    def excluir(handler):
        caminho = urlsplit(handler.path).path
        ponto_id = caminho.rsplit("/", 1)[-1]
        for indice, ponto in enumerate(locais):
            if ponto["id"] == ponto_id:
                del locais[indice]
                break
        handler.send_response(204)
        handler.send_header("Access-Control-Allow-Origin", handler.headers.get("Origin"))
        handler.send_header("Access-Control-Allow-Credentials", "true")
        handler.end_headers()

    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    monkeypatch.setattr(ServidorApi, "do_DELETE", excluir, raising=False)
    _abrir(navegador, servidor_frontend, servidor_api, "pontos.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#pontos-list article")) == 20)
    navegador.find_element(By.ID, "ponto-next").send_keys(Keys.ENTER)
    espera.until(lambda d: _primeiro_texto(d, "#pontos-list h3") == "Local 020")
    navegador.find_element(By.CSS_SELECTOR, "button[data-acao='excluir']").send_keys(Keys.ENTER)
    espera.until(lambda d: d.find_element(By.ID, "ponto-page").text == "Página 1")
    assert navegador.find_element(By.CSS_SELECTOR, "#pontos-list h3").text == "Local 000"
    assert len(navegador.find_elements(By.CSS_SELECTOR, "#pontos-list article")) == 20


def test_etapa18_novo_item_sem_modalidade_descarte():
    html = (Path(__file__).parents[1]/"frontend/itens.html").read_text(encoding="utf-8")
    assert '<option value="descarte">' not in html
    js = (Path(__file__).parents[1]/"frontend/js/itens.js").read_text(encoding="utf-8")
    assert "/api/encaminhamentos" not in js


@pytest.mark.parametrize("acao", ["situacao", "excluir"])
def test_mutacao_de_local_bloqueia_repeticao_enquanto_pendente(navegador, servidor_frontend, servidor_api, monkeypatch, acao):
    from threading import Event
    iniciou, liberar = Event(), Event()
    usuario = {**ServidorApi.usuario, "id": "operador-bloqueio", "tipo": "ponto_coleta"}
    ponto = {"id": "000000000000000000000001", "nome": "Local de teste", "ativo": True,
             "endereco": {"logradouro": "Rua pública", "numero": "1", "cidade": "Maringá", "cep": "87000000"},
             "categorias_aceitas": ["notebook"], "horario_atendimento": "9h às 17h", "responsavel_id": usuario["id"]}
    estado = {"pontos": [ponto], "mutacoes": 0}
    def obter(h):
        h._responder(200, usuario if urlsplit(h.path).path == "/api/usuarios/me" else estado["pontos"])
    def mutar(h):
        estado["mutacoes"] += 1
        iniciou.set()
        liberar.wait(timeout=10)
        if acao == "situacao":
            ponto["ativo"] = False;h._responder(200, ponto)
        else:
            estado["pontos"] = []
            h.send_response(204)
            h.send_header("Access-Control-Allow-Origin", h.headers.get("Origin"))
            h.send_header("Access-Control-Allow-Credentials", "true")
            h.end_headers()
    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    monkeypatch.setattr(ServidorApi, "do_POST", mutar, raising=False)
    monkeypatch.setattr(ServidorApi, "do_DELETE", mutar, raising=False)
    _abrir(navegador, servidor_frontend, servidor_api, "pontos.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, f"button[data-acao='{acao}']"))
    botao = navegador.find_element(By.CSS_SELECTOR, f"button[data-acao='{acao}']")
    try:
        botao.send_keys(Keys.ENTER)
        assert iniciou.wait(timeout=3)
        assert not botao.is_enabled()
    finally:
        liberar.set()
    espera.until(lambda d: "Carregando" not in d.find_element(By.ID, "pontos-message").text)
    assert estado["mutacoes"] == 1


def test_catalogo_do_operador_nao_promete_fila_de_descarte(navegador, servidor_frontend, servidor_api, monkeypatch):
    usuario = {**ServidorApi.usuario, "tipo": "ponto_coleta"}
    monkeypatch.setattr(ServidorApi, "usuario", usuario)
    _abrir(navegador, servidor_frontend, servidor_api, "catalogo.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_element(By.ID, "point-note").is_displayed())
    assert "doação e venda" in navegador.find_element(By.ID, "point-note").text
    assert "entregas previstas" not in navegador.find_element(By.ID, "role-description").text


def test_editar_local_preserva_todas_categorias_aceitas_pelo_contrato(navegador, servidor_frontend, servidor_api, monkeypatch):
    from app.schemas.item import CategoriaItem
    from typing import get_args
    categorias = set(get_args(get_args(CategoriaItem)[0]))
    usuario = {**ServidorApi.usuario, "id": "operador-categorias", "tipo": "ponto_coleta"}
    ponto = {"id": "000000000000000000000002", "nome": "Local varias categorias", "ativo": True,
             "endereco": {"logradouro": "Rua pública", "numero": "1", "complemento": None, "cidade": "Maringá", "cep": "87000000"},
             "categorias_aceitas": ["audio", "telefonia", "perifericos", "eletrodomestico"],
             "horario_atendimento": "9h às 17h", "responsavel_id": usuario["id"]}
    enviados = []
    def obter(h):
        h._responder(200, usuario if urlsplit(h.path).path == "/api/usuarios/me" else [ponto])
    def editar(h):
        dados = json.loads(h.rfile.read(int(h.headers["Content-Length"])));enviados.append(dados)
        ponto.update(dados);h._responder(200, ponto)
    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    monkeypatch.setattr(ServidorApi, "do_PUT", editar, raising=False)
    _abrir(navegador, servidor_frontend, servidor_api, "pontos.html")
    espera = WebDriverWait(navegador, 8)
    espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "button[data-acao='editar']"))
    navegador.find_element(By.CSS_SELECTOR, "button[data-acao='editar']").send_keys(Keys.ENTER)
    select = Select(navegador.find_element(By.CSS_SELECTOR, "#ponto-form select[name='categorias_aceitas']"))
    assert {o.get_attribute("value") for o in select.options} == categorias
    assert {o.get_attribute("value") for o in select.all_selected_options} == set(ponto["categorias_aceitas"])
    navegador.find_element(By.CSS_SELECTOR, "#ponto-form button[type='submit']").send_keys(Keys.ENTER)
    espera.until(lambda _: enviados)
    assert set(enviados[0]["categorias_aceitas"]) == set(ponto["categorias_aceitas"])


def test_indicadores_da_interface_usam_somente_ofertas(navegador, servidor_frontend, servidor_api, monkeypatch):
    valores = {"doados": 1, "vendidos": 2, "ofertas_ativas": 3, "pendencias": 4, "total": 1 + 2, "locais_ativos": 5}
    def obter(h):
        caminho = urlsplit(h.path).path
        if caminho == "/api/usuarios/me":
            h._responder(200, ServidorApi.usuario)
        elif caminho == "/api/indicadores":
            h._responder(200, valores)
        else:
            h._responder(200, [])
    monkeypatch.setattr(ServidorApi, "do_GET", obter)
    _abrir(navegador, servidor_frontend, servidor_api, "itens.html")
    WebDriverWait(navegador, 8).until(lambda d: d.find_element(By.ID, "indicador-doados").text == "1")
    assert not navegador.find_elements(By.ID, "indicador-coletados")
    assert not navegador.find_elements(By.ID, "indicador-indicados")
    assert navegador.find_element(By.ID, "indicador-vendidos").text == "2"
    assert navegador.find_element(By.ID, "indicador-total").text == str(valores["total"])
    assert navegador.find_element(By.ID, "indicador-locais").text == "5"
    assert "informação cadastral" in navegador.find_element(By.CSS_SELECTOR, "[aria-labelledby='indicadores-title']").text
