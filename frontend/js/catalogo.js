import {
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
  const data = new FormData(document.getElementById("catalog-form"));
  const params = new URLSearchParams();
  ["categoria", "condicao", "destino", "status"].forEach((campo) => {
    const valor = String(data.get(campo) || "");
    if (valor) params.set(campo, valor);
  });
  if (usuario?.tipo === "ponto_coleta") {
    params.set("destino", "descarte");
  }
  return params.toString();
}

function renderCatalog() {
  const list = document.getElementById("catalog-list");
  list.replaceChildren();
  if (itens.length === 0) {
    renderEmptyState(list, "Nenhum item encontrado", "Tente remover algum filtro ou volte mais tarde.");
    return;
  }
  itens.forEach((item) => list.append(createItemCard(item)));
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
  const destination = document.getElementById("catalog-destination");
  const isCollectionPoint = usuario.tipo === "ponto_coleta";
  pointNote.hidden = !isCollectionPoint;
  destination.disabled = isCollectionPoint;
  if (isCollectionPoint) destination.value = "descarte";
}

function clearFilters() {
  const form = document.getElementById("catalog-form");
  form.reset();
  if (usuario.tipo === "ponto_coleta") {
    form.elements.destino.value = "descarte";
  }
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
