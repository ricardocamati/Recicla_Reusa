import {
  createElement,
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

const PROXIMA_ACAO = {
  "doacao:reservado": { status: "doado", rotulo: "Marcar como doado" },
  "descarte:disponivel": {
    status: "encaminhado",
    rotulo: "Encaminhar ao ponto",
    referencia: "ponto",
  },
  "descarte:encaminhado": { status: "coletado", rotulo: "Marcar como coletado" },
  "revenda:disponivel": { status: "em_avaliacao", rotulo: "Iniciar avaliação" },
  "revenda:em_avaliacao": {
    status: "recondicionado",
    rotulo: "Marcar como recondicionado",
  },
  "revenda:recondicionado": {
    status: "vendido",
    rotulo: "Registrar venda",
    referencia: "comprador",
  },
};

let pontos = [];
let pessoas = [];

async function carregarReferencias() {
  try {
    pontos = await requestApi("/api/pontos-coleta?limite=100");
  } catch {
    pontos = [];
  }
  try {
    pessoas = await requestApi("/api/usuarios");
  } catch {
    pessoas = [];
  }
}

function opcoes(select, valores) {
  select.replaceChildren();
  const vazio = createElement("option", "", "Selecione");
  vazio.value = "";
  select.append(vazio);
  valores.forEach(({ valor, texto }) => {
    const opcao = createElement("option", "", texto);
    opcao.value = valor;
    select.append(opcao);
  });
}

function painelFluxo(item) {
  const acao = PROXIMA_ACAO[`${item.destino}:${item.status}`];
  if (!acao) return null;
  const painel = createElement("div", "item-actions");
  let select = null;

  if (acao.referencia === "ponto") {
    const compativeis = pontos.filter((ponto) =>
      (ponto.categorias_aceitas || []).includes(item.categoria),
    );
    select = createElement("select", "", "");
    select.dataset.papel = "ponto";
    select.setAttribute("aria-label", "Ponto de coleta");
    opcoes(select, compativeis.map((ponto) => ({ valor: ponto.id, texto: ponto.nome })));
    painel.append(select);
  }
  if (acao.referencia === "comprador") {
    const candidatos = pessoas.filter(
      (pessoa) => pessoa.id !== item.proprietario_id && pessoa.tipo !== "ponto_coleta",
    );
    select = createElement("select", "", "");
    select.dataset.papel = "comprador";
    select.setAttribute("aria-label", "Comprador");
    opcoes(select, candidatos.map((pessoa) => ({ valor: pessoa.id, texto: pessoa.nome })));
    painel.append(select);
  }

  const botao = createElement("button", "button button-secondary", acao.rotulo);
  botao.type = "button";
  botao.dataset.acao = acao.status;
  botao.dataset.itemId = item.id;
  botao.addEventListener("click", () => aplicarAcao(item, acao, select));
  painel.append(botao);
  return painel;
}

function corpoDoItem(item, status, extras = {}) {
  return {
    titulo: item.titulo,
    descricao: item.descricao,
    categoria: item.categoria,
    marca: item.marca,
    modelo: item.modelo,
    condicao: item.condicao,
    destino: item.destino,
    valor: item.valor,
    especificacoes: item.especificacoes || {},
    status,
    ...extras,
  };
}

async function aplicarAcao(item, acao, select) {
  const message = document.getElementById("my-items-message");
  const extras = {};
  if (acao.referencia === "ponto") {
    if (!select?.value) {
      setMessage(message, "Selecione um ponto de coleta compatível.", "error");
      return;
    }
    extras.ponto_coleta_id = select.value;
  }
  if (acao.referencia === "comprador") {
    if (!select?.value) {
      setMessage(message, "Selecione o comprador.", "error");
      return;
    }
    extras.comprador_id = select.value;
  }
  setMessage(message);
  try {
    await requestApi(`/api/itens/${encodeURIComponent(item.id)}`, {
      method: "PUT",
      body: JSON.stringify(corpoDoItem(item, acao.status, extras)),
    });
    await Promise.all([loadOwnedItems(), loadIndicadores()]);
    // A recarga das listas reescreve a mensagem; o aviso vem depois.
    setMessage(message, "Fluxo atualizado.", "success");
  } catch (error) {
    handleError(error, message);
  }
}

function renderOwnedItems() {
  const list = document.getElementById("my-items-list");
  list.replaceChildren();
  if (itens.length === 0) {
    renderEmptyState(list, "Você ainda não cadastrou itens", "Use o formulário ao lado para publicar um eletrônico.");
    return;
  }
  itens.forEach((item) => {
    const card = createItemCard(item, {
      owned: true,
      onEdit: startItemEdit,
      onDelete: deleteItem,
    });
    const fluxo = painelFluxo(item);
    if (fluxo) card.append(fluxo);
    list.append(card);
  });
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

async function loadIndicadores() {
  const message = document.getElementById("indicadores-message");
  try {
    const indicadores = await requestApi("/api/indicadores");
    document.getElementById("indicador-doados").textContent = indicadores.doados;
    document.getElementById("indicador-coletados").textContent = indicadores.coletados;
    document.getElementById("indicador-vendidos").textContent = indicadores.vendidos;
    document.getElementById("indicador-total").textContent = indicadores.total;
    setMessage(message);
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
  await carregarReferencias();
  await Promise.all([loadOwnedItems(), loadIndicadores()]);
}

document.addEventListener("DOMContentLoaded", initItems);
