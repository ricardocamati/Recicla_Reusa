import {
  createElement,
  handleError,
  labelFor,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;
const itens = new Map();

async function carregarItem(itemId) {
  if (!itens.has(itemId)) {
    try {
      itens.set(itemId, await requestApi(`/api/itens/${encodeURIComponent(itemId)}`));
    } catch {
      itens.set(itemId, null);
    }
  }
  return itens.get(itemId);
}

function cartaoInteresse(interesse, { recebido }) {
  const article = createElement("article", "item-card");
  const tags = createElement("div", "item-tags");
  tags.append(
    createElement("span", "tag", labelFor("status", interesse.status)),
    createElement("span", "tag tag-neutral", recebido ? "Recebido" : "Enviado"),
  );

  const item = itens.get(interesse.item_id);
  const titulo = item?.titulo || `Item ${interesse.item_id}`;
  article.append(tags, createElement("h3", "", titulo));

  if (item) {
    const meta = createElement("div", "item-meta");
    meta.append(
      createElement("span", "", labelFor("destino", item.destino)),
      createElement("span", "", labelFor("categoria", item.categoria)),
      createElement("span", "", `Situação: ${labelFor("status", item.status)}`),
    );
    article.append(meta);
  }

  const actions = createElement("div", "item-actions");
  const decidir = async (status) => {
    const alvo = recebido ? byIdRecebidos() : byIdMeus();
    try {
      await requestApi(`/api/interesses/${encodeURIComponent(interesse.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      await carregarTudo();
    } catch (error) {
      handleError(error, alvo);
    }
  };

  if (recebido && interesse.status === "pendente") {
    const aceitar = createElement("button", "button button-primary", "Aceitar");
    aceitar.type = "button";
    aceitar.addEventListener("click", () => decidir("aceito"));
    const recusar = createElement("button", "button button-ghost", "Recusar");
    recusar.type = "button";
    recusar.addEventListener("click", () => decidir("recusado"));
    actions.append(aceitar, recusar);
  }
  if (!recebido && ["pendente", "aceito"].includes(interesse.status)) {
    const cancelar = createElement("button", "button button-ghost", "Cancelar");
    cancelar.type = "button";
    cancelar.addEventListener("click", () => decidir("cancelado"));
    actions.append(cancelar);
  }
  if (actions.childElementCount > 0) article.append(actions);
  return article;
}

function byIdMeus() {
  return document.getElementById("meus-message");
}

function byIdRecebidos() {
  return document.getElementById("recebidos-message");
}

function renderLista(listaId, interesses, opcoes) {
  const lista = document.getElementById(listaId);
  lista.replaceChildren();
  if (interesses.length === 0) {
    renderEmptyState(
      lista,
      opcoes.vazioTitulo,
      opcoes.vazioTexto,
    );
    return;
  }
  interesses.forEach((interesse) => lista.append(cartaoInteresse(interesse, opcoes)));
}

async function carregarMeus() {
  const message = byIdMeus();
  setMessage(message, "Carregando seus interesses...");
  try {
    const interesses = await requestApi("/api/interesses?escopo=meus");
    await Promise.all(interesses.map((interesse) => carregarItem(interesse.item_id)));
    renderLista("meus-interesses-list", interesses, {
      recebido: false,
      vazioTitulo: "Nenhum interesse registrado",
      vazioTexto: "Abra o catálogo e manifeste interesse em um item de doação ou revenda.",
    });
    setMessage(message, `${interesses.length} interesse(s).`, "success");
  } catch (error) {
    handleError(error, message);
    document.getElementById("meus-interesses-list").replaceChildren();
  }
}

async function carregarRecebidos() {
  const secao = document.getElementById("recebidos-section");
  const message = byIdRecebidos();
  try {
    const interesses = await requestApi("/api/interesses?escopo=recebidos");
    await Promise.all(interesses.map((interesse) => carregarItem(interesse.item_id)));
    secao.hidden = false;
    renderLista("recebidos-interesses-list", interesses, {
      recebido: true,
      vazioTitulo: "Nenhum interesse recebido",
      vazioTexto: "Quando alguém se interessar pelos seus itens, a decisão aparece aqui.",
    });
    setMessage(message, `${interesses.length} interesse(s) recebido(s).`, "success");
  } catch (error) {
    if (error?.status === 403) {
      secao.hidden = true;
      return;
    }
    handleError(error, message);
  }
}

async function carregarTudo() {
  await Promise.all([carregarMeus(), carregarRecebidos()]);
}

async function initInteresses() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  document.getElementById("atualizar-meus").addEventListener("click", carregarMeus);
  document.getElementById("atualizar-recebidos").addEventListener("click", carregarRecebidos);
  await carregarTudo();
}

document.addEventListener("DOMContentLoaded", initInteresses);
