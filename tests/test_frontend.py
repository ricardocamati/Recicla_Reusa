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
        "itens.html": ("item-form", "my-items-list", "logout-button"),
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
    ):
        assert rota in javascript
    assert 'credentials: "include"' in javascript
    assert '"endereco":' not in javascript
    assert "usuario.endereco" not in javascript


def test_javascript_nao_persiste_segredos_nem_renderiza_html_da_api() -> None:
    javascript = ler_javascript()

    assert "localStorage" not in javascript
    assert "sessionStorage" not in javascript
    assert "document.cookie" not in javascript
    assert "innerHTML" not in javascript
    assert "textContent" in javascript


def test_javascript_aplica_permissoes_e_erros_http() -> None:
    javascript = ler_javascript()

    for perfil in ("doador", "beneficiario", "ponto_coleta"):
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
        "itens.js": ("/api/itens", "itemPayloadFromForm"),
    }

    for modulo, marcadores in modulos.items():
        conteudo = ler(f"js/{modulo}")
        for marcador in marcadores:
            assert marcador in conteudo


def test_frontend_nao_mantem_monolito_js() -> None:
    assert not (FRONTEND / "app.js").exists()


def test_catalogo_forca_descarte_para_ponto_de_coleta() -> None:
    javascript = ler("js/catalogo.js")

    assert 'params.set("destino", "descarte")' in javascript


def test_css_tem_layout_responsivo_e_foco_acessivel() -> None:
    css = ler("styles.css")

    assert "@media" in css
    assert ":focus-visible" in css
    assert "grid-template-columns" in css


def test_frontend_nao_exibe_referencias_institucionais() -> None:
    arquivos = sorted(
        caminho
        for caminho in FRONTEND.rglob("*")
        if caminho.is_file()
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
