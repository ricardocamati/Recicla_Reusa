import {
  createItemCard,
  handleError,
  itemPayloadFromForm,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;
let itens = [];

function updateValueField() {
  const destination = document.getElementById("item-destination");
  const valueField = document.getElementById("item-value-field");
  const valueInput = document.getElementById("item-value");
  const isResale = destination.value === "revenda";
  valueField.hidden = !isResale;
  valueInput.required = isResale;
  if (!isResale) valueInput.value = "";
}

function resetItemForm() {
  const form = document.getElementById("item-form");
  form.reset();
  form.elements.item_id.value = "";
  document.getElementById("item-form-title").textContent = "Cadastrar item";
  document.getElementById("cancel-item-edit").hidden = true;
  setMessage(document.getElementById("item-message"));
  updateValueField();
}

function renderOwnedItems() {
  const list = document.getElementById("my-items-list");
  list.replaceChildren();
  if (itens.length === 0) {
    renderEmptyState(list, "Você ainda não cadastrou itens", "Use o formulário ao lado para publicar um eletrônico.");
    return;
  }
  itens.forEach((item) => list.append(createItemCard(item, {
    owned: true,
    onEdit: startItemEdit,
    onDelete: deleteItem,
  })));
}

async function loadOwnedItems() {
  const message = document.getElementById("my-items-message");
  setMessage(message, "Carregando seus itens...");
  try {
    const catalogo = await requestApi("/api/itens");
    itens = catalogo.filter((item) => item.proprietario_id === usuario.id);
    setMessage(message, `${itens.length} item(ns) seu(s).`, "success");
    renderOwnedItems();
  } catch (error) {
    handleError(error, message);
    document.getElementById("my-items-list").replaceChildren();
  }
}

function startItemEdit(itemId) {
  const item = itens.find((candidate) => candidate.id === itemId);
  if (!item) {
    setMessage(document.getElementById("item-message"), "O item não foi encontrado na sua lista.", "error");
    return;
  }
  const form = document.getElementById("item-form");
  form.elements.item_id.value = item.id;
  form.elements.titulo.value = item.titulo || "";
  form.elements.descricao.value = item.descricao || "";
  form.elements.categoria.value = item.categoria || "outro";
  form.elements.condicao.value = item.condicao || "funcional";
  form.elements.marca.value = item.marca || "";
  form.elements.modelo.value = item.modelo || "";
  form.elements.destino.value = item.destino || "doacao";
  form.elements.valor.value = item.valor === null ? "" : item.valor;
  document.getElementById("item-form-title").textContent = "Editar item";
  document.getElementById("cancel-item-edit").hidden = false;
  updateValueField();
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function saveItem(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("item-message");
  const itemId = String(form.elements.item_id.value || "");
  setMessage(message);
  try {
    await requestApi(itemId ? `/api/itens/${itemId}` : "/api/itens", {
      method: itemId ? "PUT" : "POST",
      body: JSON.stringify(itemPayloadFromForm(form)),
    });
    resetItemForm();
    setMessage(message, itemId ? "Item atualizado." : "Item cadastrado.", "success");
    await loadOwnedItems();
  } catch (error) {
    handleError(error, message);
  }
}

async function deleteItem(itemId) {
  const message = document.getElementById("my-items-message");
  setMessage(message);
  try {
    await requestApi(`/api/itens/${itemId}`, { method: "DELETE" });
    setMessage(message, "Item excluído.", "success");
    await loadOwnedItems();
  } catch (error) {
    handleError(error, message);
  }
}

async function initItems() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  if (usuario.tipo !== "doador") {
    document.getElementById("item-management").hidden = true;
    document.getElementById("not-donor").hidden = false;
    return;
  }
  document.getElementById("item-form").addEventListener("submit", saveItem);
  document.getElementById("item-destination").addEventListener("change", updateValueField);
  document.getElementById("cancel-item-edit").addEventListener("click", resetItemForm);
  updateValueField();
  await loadOwnedItems();
}

document.addEventListener("DOMContentLoaded", initItems);
