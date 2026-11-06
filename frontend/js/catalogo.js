import {
  createElement,
  createItemCard,
  handleError,
  labelFor,
  labelForInteresse,
  requestAllPages,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;
let itens = [];
let meusInteresses = new Map();

function queryFromCatalogForm() {
  const form = document.getElementById("catalog-form");
  const data = new FormData(form);
  const params = new URLSearchParams();
  ["texto", "categoria", "condicao", "destino", "preco_min", "preco_max"].forEach(
    (campo) => {
      const valor = String(data.get(campo) || "").trim();
      if (valor) params.set(campo, valor);
    },
  );
  if (form.elements.incluir_reservados.checked) {
    params.set("incluir_reservados", "true");
  }
  // A API pagina o catálogo; a tela ainda não tem navegação por páginas.
  params.set("limite", "100");
  return params.toString();
}

function podeManifestarInteresse(item) {
  return (
    usuario.tipo !== "ponto_coleta" &&
    item.proprietario_id !== usuario.id &&
    item.destino !== "descarte" &&
    item.status === "disponivel"
  );
}

function mensagemDeInteresse(message, texto) {
  setMessage(message, texto, "success");
  const link = createElement("a", "", "Abrir Interesses");
  link.href = "./interesses.html";
  message.append(document.createTextNode(" "), link);
}

function cartaoComInteresse(item) {
  const card = createItemCard(item);
  card.dataset.itemId = item.id;
  if (usuario.tipo === "ponto_coleta" || item.proprietario_id === usuario.id) return card;
  const interesse = meusInteresses.get(item.id);
  if (!interesse && !podeManifestarInteresse(item)) return card;
  const actions = createElement("div", "item-actions");
  if (interesse) {
    const acompanhar = createElement("a", "button button-secondary", "Acompanhar interesse");
    acompanhar.href = "./interesses.html";
    acompanhar.dataset.acao = "acompanhar-interesse";
    actions.append(acompanhar);
    card.append(createElement("p", "field-hint", `Seu interesse: ${labelForInteresse(interesse.status)}`), actions);
    return card;
  }
  const botao = createElement("button", "button button-primary", "Tenho interesse");
  botao.type = "button";
  botao.dataset.acao = "interesse";
  botao.dataset.itemId = item.id;
  botao.addEventListener("click", async () => {
    const message = document.getElementById("catalog-message");
    botao.disabled = true;
    try {
      const registrado = await requestApi("/api/interesses", {
        method: "POST",
        body: JSON.stringify({ item_id: item.id }),
      });
      meusInteresses.set(item.id, registrado);
      // A confirmação só aparece após reconciliar o estado retornado pela API.
      if (await loadCatalog()) mensagemDeInteresse(message, "Interesse registrado.");
    } catch (error) {
      if (error.status === 409 && await loadCatalog() && meusInteresses.has(item.id)) {
        mensagemDeInteresse(message, "Seu interesse já está registrado.");
        return;
      }
      botao.disabled = false;
      handleError(error, message);
    }
  });
  actions.append(botao);
  card.append(actions);
  return card;
}

function renderCatalog() {
  const list = document.getElementById("catalog-list");
  list.replaceChildren();
  if (itens.length === 0) {
    renderEmptyState(list, "Nenhum item encontrado", "Tente remover algum filtro ou volte mais tarde.");
    return;
  }
  itens.forEach((item) => list.append(cartaoComInteresse(item)));
}

async function loadCatalog() {
  const message = document.getElementById("catalog-message");
  setMessage(message, "Carregando catálogo...");
  try {
    const query = queryFromCatalogForm();
    const [ofertas, interesses] = await Promise.all([
      requestApi(`/api/itens${query ? `?${query}` : ""}`),
      usuario.tipo === "pessoa" ? requestAllPages("/api/interesses", { escopo: "meus" }) : [],
    ]);
    itens = ofertas;
    meusInteresses = new Map(interesses.map((interesse) => [interesse.item_id, interesse]));
    setMessage(message, `${itens.length} item(ns) encontrado(s).`, "success");
    renderCatalog();
    return true;
  } catch (error) {
    handleError(error, message);
    document.getElementById("catalog-list").replaceChildren();
    return false;
  }
}

function configureRoleView() {
  const pointNote = document.getElementById("point-note");
  const isCollectionPoint = usuario.tipo === "ponto_coleta";
  if (pointNote) pointNote.hidden = !isCollectionPoint;
}

function guardarFiltros() {
  // Filtros no endereço: voltar do detalhe restaura a mesma busca.
  const form = document.getElementById("catalog-form");
  const dados = new FormData(form);
  const params = new URLSearchParams();
  ["texto", "categoria", "condicao", "destino", "preco_min", "preco_max"].forEach(
    (campo) => {
      const valor = String(dados.get(campo) || "").trim();
      if (valor) params.set(campo, valor);
    },
  );
  if (form.elements.incluir_reservados.checked) {
    params.set("incluir_reservados", "true");
  }
  const consulta = params.toString();
  window.history.replaceState(
    null,
    "",
    consulta ? `?${consulta}` : window.location.pathname,
  );
}

function restaurarFiltros() {
  const params = new URLSearchParams(window.location.search);
  const form = document.getElementById("catalog-form");
  ["texto", "categoria", "condicao", "destino", "preco_min", "preco_max"].forEach(
    (campo) => {
      if (params.has(campo) && form.elements[campo]) {
        form.elements[campo].value = params.get(campo);
      }
    },
  );
  form.elements.incluir_reservados.checked =
    params.get("incluir_reservados") === "true";
}

function clearFilters() {
  const form = document.getElementById("catalog-form");
  form.reset();
  window.history.replaceState(null, "", window.location.pathname);
  loadCatalog();
}

async function initCatalog() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  configureRoleView();
  restaurarFiltros();
  document.getElementById("catalog-form").addEventListener("submit", (event) => {
    event.preventDefault();
    guardarFiltros();
    loadCatalog();
  });
  document.getElementById("clear-filters").addEventListener("click", clearFilters);
  await loadCatalog();
}

document.addEventListener("DOMContentLoaded", initCatalog);
