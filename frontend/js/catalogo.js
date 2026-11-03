import {
  createElement,
  createItemCard,
  handleError,
  labelFor,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;
let itens = [];

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

function cartaoComInteresse(item) {
  const card = createItemCard(item);
  if (!podeManifestarInteresse(item)) return card;
  const actions = createElement("div", "item-actions");
  const botao = createElement("button", "button button-primary", "Tenho interesse");
  botao.type = "button";
  botao.dataset.acao = "interesse";
  botao.dataset.itemId = item.id;
  botao.addEventListener("click", async () => {
    const message = document.getElementById("catalog-message");
    botao.disabled = true;
    try {
      await requestApi("/api/interesses", {
        method: "POST",
        body: JSON.stringify({ item_id: item.id }),
      });
      // loadCatalog reescreve a mensagem; o aviso do interesse vem depois.
      await loadCatalog();
      setMessage(message, "Interesse registrado. Acompanhe em Interesses.", "success");
    } catch (error) {
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
    itens = await requestApi(`/api/itens${query ? `?${query}` : ""}`);
    setMessage(message, `${itens.length} item(ns) encontrado(s).`, "success");
    renderCatalog();
  } catch (error) {
    handleError(error, message);
    document.getElementById("catalog-list").replaceChildren();
  }
}

function configureRoleView() {
  const pointNote = document.getElementById("point-note");
  const isCollectionPoint = usuario.tipo === "ponto_coleta";
  if (pointNote) pointNote.hidden = !isCollectionPoint;
}

function clearFilters() {
  const form = document.getElementById("catalog-form");
  form.reset();
  loadCatalog();
}

async function initCatalog() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  configureRoleView();
  document.getElementById("catalog-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadCatalog();
  });
  document.getElementById("clear-filters").addEventListener("click", clearFilters);
  await loadCatalog();
}

document.addEventListener("DOMContentLoaded", initCatalog);
