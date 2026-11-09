from pathlib import Path


FRONTEND = Path(__file__).parents[1] / "frontend"


def ler(nome: str) -> str:
    return (FRONTEND / nome).read_text(encoding="utf-8")


def ler_javascript() -> str:
    return "\n".join(
        caminho.read_text(encoding="utf-8")
        for caminho in sorted((FRONTEND / "js").glob("*.js"))
    )


def test_frontend_possui_entrada_e_recursos_estaticos() -> None:
    assert (FRONTEND / "index.html").is_file()
    assert (FRONTEND / "styles.css").is_file()
    assert (FRONTEND / "js").is_dir()


def test_html_oferece_fluxos_da_v1() -> None:
    paginas = {
        "cadastro.html": ("register-form",),
        "login.html": ("login-form",),
        "perfil.html": ("profile-form", "logout-button"),
        "catalogo.html": ("catalog-form", "catalog-list"),
        "itens.html": ("item-form", "my-items-list", "logout-button", "indicador-doados"),
        "interesses.html": ("meus-interesses-list", "recebidos-interesses-list", "logout-button"),
        "notificacoes.html": ("notificacoes-list", "filtro-lida", "logout-button"),
        "pontos.html": ("pontos-list", "ponto-form", "logout-button"),
    }

    for pagina, identificadores in paginas.items():
        conteudo = ler(pagina)
        for identificador in identificadores:
            assert f'id="{identificador}"' in conteudo

    entrada = ler("index.html")
    for destino in ("cadastro.html", "login.html", "catalogo.html"):
        assert destino in entrada


def test_javascript_consumes_contratos_da_api() -> None:
    javascript = ler_javascript()

    for rota in (
        "/api/usuarios",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/usuarios/me",
        "/api/itens",
        "/api/interesses",
        "/api/notificacoes",
        "/api/pontos-coleta",
        "/api/indicadores",
    ):
        assert rota in javascript
    assert 'credentials: "include"' in javascript
    assert "endereco: addressFromForm(data)" in javascript
    assert "usuario.endereco" in javascript


def test_javascript_nao_persiste_segredos_nem_renderiza_html_da_api() -> None:
    javascript = ler_javascript()

    assert "localStorage" not in javascript
    assert "sessionStorage" not in javascript
    assert "document.cookie" not in javascript
    assert "innerHTML" not in javascript
    assert "textContent" in javascript


def test_javascript_aplica_permissoes_e_erros_http() -> None:
    javascript = ler_javascript()

    for perfil in ("pessoa", "pessoa", "ponto_coleta"):
        assert perfil in javascript
    for status in ("401", "403", "404"):
        assert f"error.status === {status}" in javascript


def test_frontend_organiza_telas_separadas() -> None:
    paginas = {
        "index.html": "home.js",
        "cadastro.html": "cadastro.js",
        "login.html": "login.js",
        "perfil.html": "perfil.js",
        "catalogo.html": "catalogo.js",
        "itens.html": "itens.js",
        "interesses.html": "interesses.js",
        "notificacoes.html": "notificacoes.js",
        "pontos.html": "pontos.js",
    }

    for pagina, modulo in paginas.items():
        conteudo = ler(pagina)
        assert f'src="./js/{modulo}"' in conteudo
        assert 'type="module"' in conteudo


def test_frontend_separa_javascript_por_responsabilidade() -> None:
    modulos = {
        "api.js": ("requestApi", 'credentials: "include"'),
        "comum.js": ("handleError", "loadSession"),
        "cadastro.js": ("/api/usuarios", "userPayloadFromForm"),
        "login.js": ("/api/auth/login", "window.location"),
        "perfil.js": ("/api/usuarios/", "profilePayloadFromForm"),
        "catalogo.js": ("/api/itens", "queryFromCatalogForm"),
        "itens.js": ("/api/itens", "itemPayloadFromForm", "/api/indicadores"),
        "interesses.js": ("/api/interesses", "requestAllPages", 'escopo: "recebidos"'),
        "notificacoes.js": ("/api/notificacoes", "Marcar como lida"),
        "pontos.js": ("/api/pontos-coleta", "categorias_aceitas"),
    }

    for modulo, marcadores in modulos.items():
        conteudo = ler(f"js/{modulo}")
        for marcador in marcadores:
            assert marcador in conteudo


def test_frontend_nao_mantem_monolito_js() -> None:
    assert not (FRONTEND / "app.js").exists()


def test_catalogo_nao_oferece_descarte_e_filtra_por_texto_e_preco() -> None:
    html = ler("catalogo.html")
    assert '<option value="descarte">' not in html
    assert 'name="texto"' in html
    assert 'name="preco_min"' in html and 'name="preco_max"' in html
    assert 'name="incluir_reservados"' in html
    js = ler("js/catalogo.js")
    assert '"texto", "categoria", "condicao", "destino", "preco_min", "preco_max"' in js
    assert "incluir_reservados" in js
    # Catálogo não pede status: a API só devolve publicado e, se solicitado, reservado.
    assert '"status"' not in js.split("function clearFilters")[0]


def test_itens_guia_cadastro_por_intencao_caracteristicas_e_revisao() -> None:
    html = ler("itens.html")
    for marca in (
        'data-passo="1"',
        'data-passo="2"',
        'data-passo="3"',
        'id="save-draft"',
        'id="item-review"',
        'data-grupo="ativos"',
        'data-grupo="em_andamento"',
        'data-grupo="encerrados"',
    ):
        assert marca in html, marca
    assert 'data-grupo="historico_descarte"' not in html
    js = ler("js/itens.js")
    assert "/api/itens/meus?" in js
    assert '"publicar"' in js
    assert '"arquivar"' in js
    assert "publicar" in js and "rascunho" in js



def test_css_tem_layout_responsivo_e_foco_acessivel() -> None:
    css = ler("styles.css")

    assert "@media" in css
    assert ":focus-visible" in css
    assert "grid-template-columns" in css


def test_frontend_nao_exibe_referencias_institucionais() -> None:
    arquivos = sorted(
        caminho
        for caminho in FRONTEND.rglob("*")
        if caminho.is_file() and caminho.suffix in {".html", ".css", ".js"}
    )
    frontend = "\n".join(
        caminho.read_text(encoding="utf-8")
        for caminho in arquivos
    ).casefold()

    for referencia in (
        "poc",
        "ods 12",
        "consumo responsável",
        "consumo responsavel",
        "responsável",
        "responsavel",
    ):
        assert referencia not in frontend


def test_css_aplica_modo_escuro() -> None:
    css = ler("styles.css")

    assert "color-scheme: dark" in css
    for variavel in (
        "--ink: #e8f2eb",
        "--muted: #9aaea2",
        "--paper: #0d1410",
        "--card: #17221b",
        "--line: #2c3d32",
        "--green: #57c987",
        "--green-dark: #9ae6b0",
        "--green-soft: #183a28",
    ):
        assert variavel in css

    for superficie in (
        "--surface-deep: #0a120e",
        "--surface-input: #101a14",
        "--hero: #142d22",
    ):
        assert superficie in css

def test_catalogo_permite_manifestar_interesse() -> None:
    catalogo = ler("js/catalogo.js")
    assert 'data-acao' in catalogo or "dataset.acao" in catalogo
    assert "interesse" in catalogo
    assert "/api/interesses" in catalogo
    # Descarte é coletado por ponto de coleta, não disputado por interessados.
    assert 'item.destino !== "descarte"' in catalogo
    assert "item.proprietario_id !== usuario.id" in catalogo


def test_itens_oferece_acoes_do_fluxo_ao_proprietario() -> None:
    itens = ler("js/itens.js")
    for chave in (
        '"doacao:reservado"',
        '"revenda:reservado"',
    ):
        assert chave in itens, chave
    # Descarte não é mais fluxo de item: não agenda entrega nem usa encaminhamentos.
    assert "/api/encaminhamentos" not in itens
    assert "Agendar entrega" not in itens
    assert "Cancelar entrega" not in itens
    # Doação e venda terminam em entrega bilateral, não em conclusão por PUT.
    assert "Declarar entrega" in itens
    assert "executarComandoItem" in itens
    assert "em_avaliacao" not in itens
    assert 'status: "vendido"' not in itens


def test_avisos_e_navegacao_oferecem_link_e_recuperacao() -> None:
    comum = ler("js/comum.js")
    assert "comBotaoOcupado" in comum
    assert "Recarregue a página" in comum
    notificacoes = ler("js/notificacoes.js")
    assert "aviso.link" in notificacoes
    catalogo = ler("js/catalogo.js")
    assert "restaurarFiltros" in catalogo
    assert "replaceState" in catalogo


def test_itens_nao_oferece_destinacao_informada() -> None:
    itens = ler("js/itens.js")
    for marca in (
        '"descarte:destinacao_informada"',
        "destination-form",
        "Indicar outro lugar",
        "Desfazer indicação",
        "/destinacao",
    ):
        assert marca not in itens, marca


def test_pontos_oferece_gestao_de_locais() -> None:
    pontos = ler("js/pontos.js")
    for marca in (
        "situacao",
        "/situacao",
        "Editar",
        "Ativar",
        "Desativar",
        "/api/pontos-coleta",
    ):
        assert marca in pontos, marca
    html = ler("pontos.html")
    assert 'id="pontos-gestao"' in html
    assert 'id="fila-operador"' not in html


def test_interesses_oferece_combinacao_e_recebimento() -> None:
    interesses = ler("js/interesses.js")
    for marca in (
        "combination-form",
        "Aceitar combinação",
        "Confirmar recebimento",
        "/combinacao",
        "/combinacao/aceite",
        "/recebimento",
    ):
        assert marca in interesses, marca
