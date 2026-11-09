"""Jornadas completas pela interface na stack Docker, com auditoria e limpeza.

Uso (com a stack isolada no ar):
    JORNADAS_MONGO_URI=... JORNADAS_DB=recicla_reusa \
    JORNADAS_FRONTEND_URL=http://127.0.0.1:8109 JORNADAS_API_URL=http://127.0.0.1:8029 \
    python scripts/validar_jornadas_v2.py
"""
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

sys.path.insert(0, str(Path(__file__).parents[1]))
from app.security.passwords import hash_password  # noqa: E402

FRONTEND = os.environ.get("JORNADAS_FRONTEND_URL", "http://127.0.0.1:8109")
API = os.environ.get("JORNADAS_API_URL", "http://127.0.0.1:8029")
MONGO_URI = os.environ["JORNADAS_MONGO_URI"]
DB = os.environ.get("JORNADAS_DB", "recicla_reusa")
MARCA = "jornada-" + uuid4().hex[:6]
SENHA = "Teste12345"

cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
banco = cliente[DB]
usuarios = banco[os.environ.get("MONGO_COLLECTION_USUARIOS", "usuarios")]
itens = banco[os.environ.get("MONGO_COLLECTION_ITENS", "itens")]
pontos = banco[os.environ.get("MONGO_COLLECTION_PONTOS_COLETA", "pontos_coleta")]
interesses = banco[os.environ.get("MONGO_COLLECTION_INTERESSES", "interesses")]
avisos = banco[os.environ.get("MONGO_COLLECTION_NOTIFICACOES", "notificacoes")]


def preparar_operador() -> str:
    email = f"{MARCA}-operador@example.test"
    agora = datetime.now(UTC).replace(microsecond=0)
    usuarios.insert_one(
        {
            "nome": "Operador Jornada",
            "email": email,
            "tipo": "ponto_coleta",
            "endereco": {
                "logradouro": "Rua do Ponto",
                "numero": "10",
                "complemento": None,
                "cep": "87000000",
                "cidade": "Maringá",
            },
            "senha_hash": hash_password(SENHA),
            "data_adicao": agora,
            "data_modificacao": agora,
        }
    )
    return email


class Navegador:
    def __init__(self) -> None:
        opcoes = webdriver.ChromeOptions()
        opcoes.add_argument("--headless=new")
        opcoes.add_argument("--disable-gpu")
        opcoes.add_argument("--no-sandbox")
        opcoes.add_argument("--window-size=1440,1200")
        for candidato in (
            Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        ):
            if candidato.is_file():
                opcoes.binary_location = str(candidato)
                break
        try:
            self.driver = webdriver.Chrome(options=opcoes)
        except WebDriverException as erro:
            raise SystemExit(f"Chrome/Selenium indisponível: {erro}") from erro
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": f"window.RECICLA_API_BASE = {json.dumps(API)};"},
        )
        self.espera = WebDriverWait(self.driver, 15)

    def fechar(self) -> None:
        self.driver.quit()

    def abrir(self, pagina: str, seletor: str) -> None:
        self.driver.get(f"{FRONTEND}/{pagina}")
        self.espera.until(lambda d: d.execute_script("return document.readyState") == "complete")
        self.espera.until(lambda d: d.find_element(By.CSS_SELECTOR, seletor))

    def clicar(self, elemento) -> None:
        """Clique via JS para não depender de sobreposição de layout."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", elemento)
        self.driver.execute_script("arguments[0].click()", elemento)

    def preencher(self, campo: str, valor: str, escopo: str = "") -> None:
        prefixo = f"{escopo} " if escopo else ""
        elemento = self.driver.find_element(By.CSS_SELECTOR, f"{prefixo}[name='{campo}']")
        elemento.clear()
        elemento.send_keys(valor)

    def selecionar(self, campo: str, texto: str, escopo: str = "") -> None:
        prefixo = f"{escopo} " if escopo else ""
        elemento = self.driver.find_element(By.CSS_SELECTOR, f"{prefixo}[name='{campo}']")
        Select(elemento).select_by_visible_text(texto)

    def _cartao(self, lista: str, titulo: str):
        for card in self.driver.find_elements(By.CSS_SELECTOR, f"#{lista} article.item-card"):
            if titulo in card.text:
                return card
        return None

    def cartao(self, lista: str, titulo: str):
        return self.espera.until(lambda d: self._cartao(lista, titulo))

    def aguardar_sem_botao(self, lista: str, titulo: str, seletor: str) -> None:
        def sem_botao(driver) -> bool:
            try:
                card = self._cartao(lista, titulo)
                # Após a transição o item pode sair do grupo exibido.
                return card is None or not card.find_elements(By.CSS_SELECTOR, seletor)
            except StaleElementReferenceException:
                return False

        self.espera.until(sem_botao)

    def aguardar_sem_texto(self, lista: str, titulo: str, texto: str) -> None:
        def sem_texto(driver) -> bool:
            try:
                card = self._cartao(lista, titulo)
                return card is None or texto not in [
                    botao.text for botao in card.find_elements(By.TAG_NAME, "button")
                ]
            except StaleElementReferenceException:
                return False

        self.espera.until(sem_texto)

    def cadastrar(self, nome: str, email: str, tipo: str | None = None) -> None:
        # Desde a conta única de pessoa o cadastro público não escolhe perfil.
        self.abrir("cadastro.html", "#register-form")
        for campo, valor in (
            ("nome", nome),
            ("email", email),
            ("senha", SENHA),
            ("logradouro", "Rua da Jornada"),
            ("numero", "100"),
            ("cidade", "Maringá"),
            ("cep", "87000000"),
        ):
            self.preencher(campo, valor)
        self.clicar(self.driver.find_element(By.CSS_SELECTOR, "#register-form button[type='submit']"))
        self.espera.until(
            lambda d: "Conta criada" in d.find_element(By.ID, "register-message").text
        )

    def entrar(self, email: str) -> None:
        self.abrir("login.html", "#login-form")
        self.preencher("email", email)
        self.preencher("senha", SENHA)
        self.clicar(self.driver.find_element(By.CSS_SELECTOR, "#login-form button[type='submit']"))
        self.espera.until(lambda d: "login.html" not in d.current_url)
        self.espera.until(
            lambda d: "perfil.html" in d.current_url or "index.html" in d.current_url
            or d.find_element(By.ID, "logout-button").is_displayed()
        )

    def sair(self) -> None:
        self.abrir("perfil.html", "#logout-button")
        self.clicar(self.driver.find_element(By.ID, "logout-button"))
        self.espera.until(lambda d: "index.html" in d.current_url)

    def criar_item(self, titulo: str, destino: str, categoria: str, valor: str | None = None) -> None:
        self.abrir("itens.html", "#item-form")
        # Passo 1: intenção.
        rotulo = {"Revenda": "Venda"}.get(destino, destino)
        self.selecionar("destino", rotulo, escopo="#item-form")
        self.clicar(
            self.driver.find_element(
                By.CSS_SELECTOR, "#item-form [data-passo-acao='proximo']"
            )
        )
        # Passo 2: características.
        for campo, texto in (
            ("titulo", titulo),
            ("descricao", "Item criado pela jornada automatizada"),
            ("marca", "Marca Jornada"),
            ("modelo", "Modelo Jornada"),
        ):
            self.preencher(campo, texto, escopo="#item-form")
        self.selecionar("categoria", categoria, escopo="#item-form")
        self.selecionar("condicao", "Funcional", escopo="#item-form")
        if valor is not None:
            self.preencher("valor", valor, escopo="#item-form")
        self.clicar(
            self.driver.find_element(
                By.CSS_SELECTOR, "#item-form [data-passo-acao='proximo']"
            )
        )
        # Passo 3: revisão e publicação.
        self.clicar(self.driver.find_element(By.CSS_SELECTOR, "#item-form button[type='submit']"))
        self.espera.until(
            lambda d: any(
                titulo in card.text
                for card in d.find_elements(By.CSS_SELECTOR, "#my-items-list article.item-card")
            )
        )

    def manifestar_interesse(self, titulo: str) -> None:
        self.abrir("catalogo.html", "#catalog-form")
        cartao = self.cartao("catalog-list", titulo)
        self.clicar(cartao.find_element(By.CSS_SELECTOR, "button[data-acao='interesse']"))
        self.espera.until(
            lambda d: "Interesse registrado" in d.find_element(By.ID, "catalog-message").text
        )

    def aceitar_interesse(self, titulo: str) -> None:
        self.abrir("interesses.html", "#recebidos-interesses-list")
        cartao = self.cartao("recebidos-interesses-list", titulo)
        aceitar = self.espera.until(
            lambda d: [
                botao
                for botao in cartao.find_elements(By.TAG_NAME, "button")
                if botao.text == "Selecionar"
            ]
        )[0]
        self.clicar(aceitar)
        self.aguardar_sem_texto("recebidos-interesses-list", titulo, "Selecionar")

    def avancar(self, titulo: str, status: str, referencia: tuple[str, str] | None = None) -> None:
        documento = itens.find_one({"titulo": titulo})
        situacao = documento.get("status") if documento else None
        if situacao in {"concluido", "arquivado"}:
            grupo = "encerrados"
        elif situacao in {"reservado", "aguardando_confirmacao"}:
            grupo = "em_andamento"
        else:
            grupo = "ativos"
        self.abrir(f"itens.html?grupo={grupo}", "#my-items-list")
        cartao = self.cartao("my-items-list", titulo)
        if referencia is not None:
            papel, texto = referencia
            select = cartao.find_element(By.CSS_SELECTOR, f"select[data-papel='{papel}']")
            Select(select).select_by_visible_text(texto)
        self.clicar(cartao.find_element(By.CSS_SELECTOR, f"button[data-acao='{status}']"))
        self.espera.until(
            lambda d: "Fluxo atualizado" in d.find_element(By.ID, "my-items-message").text
        )
        self.aguardar_sem_botao("my-items-list", titulo, f"button[data-acao='{status}']")

    def criar_ponto(self, nome: str, categoria: str) -> None:
        self.abrir("pontos.html", "#ponto-form")
        for campo, valor in (
            ("nome", nome),
            ("logradouro", "Rua do Ponto"),
            ("numero", "10"),
            ("cep", "87000000"),
            ("cidade", "Maringá"),
            ("horario_atendimento", "Segunda a sexta"),
        ):
            self.preencher(campo, valor, escopo="#ponto-form")
        self.selecionar("categorias_aceitas", categoria, escopo="#ponto-form")
        self.clicar(self.driver.find_element(By.CSS_SELECTOR, "#ponto-form button[type='submit']"))
        self.espera.until(lambda d: "Local cadastrado" in d.find_element(By.ID, "ponto-form-message").text)

    def propor_combinacao(self, lista: str, titulo: str, local: str = "Portaria da jornada") -> None:
        self.abrir("interesses.html", f"#{lista}")
        cartao = self.cartao(lista, titulo)
        formulario = cartao.find_element(By.CSS_SELECTOR, "form.combination-form")
        campo = formulario.find_element(By.NAME, "local_texto")
        campo.clear()
        campo.send_keys(local)
        self.clicar(formulario.find_element(By.CSS_SELECTOR, "button[type='submit']"))

        def aguardando_aceite(driver) -> bool:
            try:
                cartao = self._cartao(lista, titulo)
                return cartao is not None and "aguardando aceite" in cartao.text
            except StaleElementReferenceException:
                return False

        self.espera.until(aguardando_aceite)

    def aceitar_combinacao(self, lista: str, titulo: str) -> None:
        self.abrir("interesses.html", f"#{lista}")
        cartao = self.cartao(lista, titulo)
        botao = self.espera.until(
            lambda d: next(
                (
                    b
                    for b in cartao.find_elements(By.TAG_NAME, "button")
                    if b.text == "Aceitar combinação"
                ),
                False,
            )
        )
        self.clicar(botao)

        def combinacao_aceita(driver) -> bool:
            try:
                cartao = self._cartao(lista, titulo)
                return (
                    cartao is not None
                    and "aguardando" not in cartao.text
                    and "aceita" in cartao.text
                )
            except StaleElementReferenceException:
                return False

        self.espera.until(combinacao_aceita)

    def declarar_entrega(self, titulo: str) -> None:
        self.abrir("itens.html?grupo=em_andamento", "#my-items-list")
        cartao = self.cartao("my-items-list", titulo)
        self.clicar(cartao.find_element(By.CSS_SELECTOR, "button[data-acao='entrega']"))
        self.espera.until(
            lambda d: "Entrega declarada" in d.find_element(By.ID, "my-items-message").text
        )

    def confirmar_recebimento(self, titulo: str) -> None:
        self.abrir("interesses.html", "#meus-interesses-list")
        cartao = self.cartao("meus-interesses-list", titulo)
        botao = self.espera.until(
            lambda d: next(
                (
                    b
                    for b in cartao.find_elements(By.TAG_NAME, "button")
                    if b.text == "Confirmar recebimento"
                ),
                False,
            )
        )
        self.clicar(botao)
        def confirmado(driver) -> bool:
            lista = driver.find_element(By.ID, "meus-interesses-list")
            return "Confirmar recebimento" not in lista.text

        self.espera.until(confirmado)

    def ler_indicadores(self) -> dict[str, str]:
        """Lê os indicadores expostos na tela de ofertas da sessão atual."""
        self.abrir("itens.html", "#indicadores-title")
        self.espera.until(lambda d: d.find_element(By.ID, "indicador-total").text != "")
        return {
            chave: self.driver.find_element(By.ID, f"indicador-{chave}").text
            for chave in ("doados", "vendidos", "ofertas", "pendencias", "total", "locais")
        }

    def consultar_diretorio_anonimo(self, cidade: str, categoria: str) -> None:
        """Terceira jornada: consulta pública sem conta, cookie ou cadastro de item."""
        self.driver.delete_all_cookies()
        self.abrir("onde-descartar.html", "#directory-list")
        self.espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
        campo = self.driver.find_element(By.ID, "directory-city")
        campo.clear()
        campo.send_keys(cidade)
        Select(self.driver.find_element(By.ID, "directory-category")).select_by_value(categoria)
        self.clicar(self.driver.find_element(By.CSS_SELECTOR, "#directory-filters button[type='submit']"))
        cartao = self.espera.until(
            lambda d: next(
                (c for c in d.find_elements(By.CSS_SELECTOR, "#directory-list article")
                 if cidade in c.text),
                False,
            )
        )
        assert "Rua" in cartao.text, cartao.text
        self.clicar(cartao.find_element(By.CSS_SELECTOR, ".directory-detail-link"))
        detalhe = self.espera.until(
            lambda d: d.find_element(By.ID, "directory-detail").is_displayed()
            and "Rua" in d.find_element(By.ID, "directory-detail").text
        )
        assert detalhe
        self.clicar(self.driver.find_element(By.ID, "directory-copy"))
        self.espera.until(
            lambda d: "copi" in d.find_element(By.ID, "directory-copy-message").text.lower()
        )
        self.clicar(self.driver.find_element(By.ID, "directory-back"))
        self.espera.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#directory-list article"))
        assert not self.driver.get_cookies(), "consulta pública não deve criar sessão"

    def avisos(self, titulo: str | None = None) -> str:
        self.abrir("notificacoes.html", "#notificacoes-list")
        self.espera.until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "#notificacoes-list article.item-card")
        )
        cartoes = self.driver.find_elements(
            By.CSS_SELECTOR, "#notificacoes-list article.item-card"
        )
        return " ".join(cartao.text for cartao in cartoes)


def auditar_datas() -> dict[str, int]:
    """Confere UTC com milissegundos nas cinco coleções, lendo com tz_aware."""
    banco_utc = MongoClient(MONGO_URI, tz_aware=True, serverSelectionTimeoutMS=5000)[DB]
    verificados = {}
    for nome, colecao in (
        ("usuarios", banco_utc[usuarios.name]),
        ("itens", banco_utc[itens.name]),
        ("pontos_coleta", banco_utc[pontos.name]),
        ("interesses", banco_utc[interesses.name]),
        ("notificacoes", banco_utc[avisos.name]),
    ):
        documentos = list(colecao.find({}))
        assert documentos, f"{nome} sem documentos para auditar"
        for documento in documentos:
            for campo in ("data_adicao", "data_modificacao"):
                valor = documento.get(campo)
                assert isinstance(valor, datetime), f"{nome}.{campo} ausente"
                assert valor.tzinfo is not None, f"{nome}.{campo} sem fuso UTC"
                assert valor.utcoffset().total_seconds() == 0, f"{nome}.{campo} fora de UTC"
                assert valor.microsecond % 1000 == 0, f"{nome}.{campo} com microssegundos"
            assert documento["data_modificacao"] >= documento["data_adicao"], nome
        verificados[nome] = len(documentos)
    return verificados


def limpar(prefixo: str = MARCA) -> None:
    """Remove apenas documentos das jornadas; nunca toca em dados de demonstração."""
    filtro_usuarios = {"email": {"$regex": f"^{prefixo}"}}
    ids_usuarios = [documento["_id"] for documento in usuarios.find(filtro_usuarios, {"_id": 1})]
    filtro_itens = {"titulo": {"$regex": f"^{prefixo}"}}
    ids_itens = [documento["_id"] for documento in itens.find(filtro_itens, {"_id": 1})]
    ids_pontos = [
        documento["_id"]
        for documento in pontos.find({"nome": {"$regex": f"^{prefixo}"}}, {"_id": 1})
    ]
    if ids_itens or ids_usuarios:
        avisos.delete_many(
            {"$or": [{"item_id": {"$in": ids_itens}}, {"usuario_id": {"$in": ids_usuarios}}]}
        )
    if ids_itens or ids_usuarios:
        interesses.delete_many(
            {"$or": [{"item_id": {"$in": ids_itens}}, {"usuario_id": {"$in": ids_usuarios}}]}
        )
    removidos_itens = itens.delete_many({"_id": {"$in": ids_itens}}).deleted_count
    removidos_pontos = pontos.delete_many({"_id": {"$in": ids_pontos}}).deleted_count
    removidos_usuarios = usuarios.delete_many({"_id": {"$in": ids_usuarios}}).deleted_count
    assert removidos_itens == len(ids_itens), (removidos_itens, len(ids_itens))
    assert removidos_pontos == len(ids_pontos), (removidos_pontos, len(ids_pontos))
    assert removidos_usuarios == len(ids_usuarios), (removidos_usuarios, len(ids_usuarios))
    restantes = {
        "usuarios": usuarios.count_documents(filtro_usuarios),
        "itens": itens.count_documents(filtro_itens),
        "pontos": pontos.count_documents({"nome": {"$regex": f"^{prefixo}"}}),
        "interesses": interesses.count_documents({"item_id": {"$in": ids_itens + [ObjectId()]}}),
        "notificacoes": avisos.count_documents({"item_id": {"$in": ids_itens + [ObjectId()]}}),
    }
    assert restantes == {chave: 0 for chave in restantes}, restantes
    print(
        "limpeza=ok; removidos "
        f"usuarios={removidos_usuarios} itens={removidos_itens} "
        f"pontos={removidos_pontos}"
    )


def main() -> None:
    # Restos de execuções interrompidas são removidos pelo mesmo prefixo seletivo.
    limpar("jornada-")
    for colecao, nome in (
        (usuarios, "usuarios"), (itens, "itens"), (pontos, "pontos"),
        (interesses, "interesses"), (avisos, "notificacoes"),
    ):
        assert colecao.count_documents({}) == 0, f"base da jornada deveria estar vazia: {nome}"

    operador_email = preparar_operador()
    doador_email = f"{MARCA}-doador@example.test"
    beneficiario_email = f"{MARCA}-beneficiario@example.test"
    titulo_doacao = f"{MARCA} Notebook doacao"
    titulo_revenda = f"{MARCA} Tablet revenda"
    nome_ponto = f"{MARCA} Ponto Central"

    navegador = Navegador()
    try:
        # Preparação: operador cadastra o local consultado na terceira jornada.
        navegador.entrar(operador_email)
        navegador.criar_ponto(nome_ponto, "Notebook")
        navegador.sair()

        # Jornada 1 — doação com entrega bilateral.
        navegador.cadastrar("Doadora Jornada", doador_email, "Doador")
        navegador.entrar(doador_email)
        navegador.criar_item(titulo_doacao, "Doação", "Notebook")
        navegador.sair()

        navegador.cadastrar("Beneficiária Jornada", beneficiario_email, "Beneficiário")
        navegador.entrar(beneficiario_email)
        navegador.manifestar_interesse(titulo_doacao)
        navegador.sair()

        navegador.entrar(doador_email)
        navegador.aceitar_interesse(titulo_doacao)
        navegador.propor_combinacao("recebidos-interesses-list", titulo_doacao)
        navegador.sair()

        navegador.entrar(beneficiario_email)
        navegador.aceitar_combinacao("meus-interesses-list", titulo_doacao)
        navegador.sair()

        navegador.entrar(doador_email)
        navegador.declarar_entrega(titulo_doacao)
        navegador.sair()

        navegador.entrar(beneficiario_email)
        navegador.confirmar_recebimento(titulo_doacao)
        texto = navegador.avisos(titulo_doacao)
        assert "concluído" in texto.lower(), texto
        navegador.sair()
        print("jornada_doacao=ok")

        # Jornada 3 — consulta anônima do diretório, sem item, conta ou escrita.
        navegador.consultar_diretorio_anonimo("Maringá", "notebook")
        print("jornada_publica_onde_descartar=ok")

        # Jornada 2 — venda direta com entrega bilateral.
        navegador.entrar(doador_email)
        navegador.criar_item(titulo_revenda, "Revenda", "Tablet", valor="120")
        navegador.sair()

        navegador.entrar(beneficiario_email)
        navegador.manifestar_interesse(titulo_revenda)
        navegador.sair()

        navegador.entrar(doador_email)
        navegador.aceitar_interesse(titulo_revenda)
        navegador.propor_combinacao("recebidos-interesses-list", titulo_revenda, "Estação central")
        navegador.sair()

        navegador.entrar(beneficiario_email)
        navegador.aceitar_combinacao("meus-interesses-list", titulo_revenda)
        navegador.sair()

        navegador.entrar(doador_email)
        navegador.declarar_entrega(titulo_revenda)
        navegador.sair()

        navegador.entrar(beneficiario_email)
        navegador.confirmar_recebimento(titulo_revenda)
        navegador.sair()
        print("jornada_revenda=ok")
    finally:
        navegador.fechar()

    # Indicadores após as jornadas: somente ofertas confirmadas e locais cadastrais.
    navegador = Navegador()
    try:
        navegador.entrar(doador_email)
        indicadores = navegador.ler_indicadores()
    finally:
        navegador.fechar()
    assert indicadores["doados"] == "1" and indicadores["vendidos"] == "1", indicadores
    assert indicadores["total"] == "2", indicadores
    assert indicadores["locais"] == "1", indicadores
    print("indicadores=ok; " + " ".join(f"{k}={v}" for k, v in indicadores.items()))

    documento = itens.find_one({"titulo": titulo_doacao})
    assert documento["status"] == "concluido"
    selecionado = interesses.find_one({"item_id": documento["_id"]})
    assert selecionado["status"] == "encerrado" and selecionado["resultado"] == "concluido"
    assert selecionado["combinacao"]["aceito_por"] is not None
    revenda = itens.find_one({"titulo": titulo_revenda})
    assert revenda["status"] == "concluido" and revenda["valor"] == 120.0
    assert avisos.count_documents({"item_id": documento["_id"]}) >= 1
    print("referencias_persistidas=ok")

    verificados = auditar_datas()
    print("auditoria_datas=ok; " + " ".join(f"{k}={v}" for k, v in verificados.items()))

    limpar(MARCA)


if __name__ == "__main__":
    try:
        main()
    finally:
        cliente.close()
