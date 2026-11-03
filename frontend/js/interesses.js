import {
  createElement,
  handleError,
  labelFor,
  labelForInteresse,
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
    createElement("span", "tag", labelForInteresse(interesse.status)),
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

  if (interesse.motivo) {
    article.append(createElement("p", "item-card-description", `Motivo: ${interesse.motivo}`));
  }
  if (interesse.tentativa > 1) {
    article.append(createElement("p", "field-hint", `Tentativa ${interesse.tentativa}`));
  }

  const actions = createElement("div", "item-actions");
  const executar = async (acao, motivo = null) => {
    const alvo = recebido ? byIdRecebidos() : byIdMeus();
    try {
      await requestApi(`/api/interesses/${encodeURIComponent(interesse.id)}/acoes`, {
        method: "POST",
        body: JSON.stringify({ acao, motivo }),
      });
      await carregarTudo();
    } catch (error) {
      handleError(error, alvo);
    }
  };
  const pedirMotivo = (acao) => {
    const motivo = window.prompt("Informe o motivo:", "");
    if (motivo === null) return;
    if (!motivo.trim()) {
      handleError(
        { status: 400, message: "O motivo é obrigatório." },
        recebido ? byIdRecebidos() : byIdMeus(),
      );
      return;
    }
    executar(acao, motivo.trim());
  };

  if (recebido && interesse.status === "pendente") {
    const selecionar = createElement("button", "button button-primary", "Selecionar");
    selecionar.type = "button";
    selecionar.addEventListener("click", () => executar("selecionar"));
    const recusar = createElement("button", "button button-ghost", "Recusar");
    recusar.type = "button";
    recusar.addEventListener("click", () => pedirMotivo("recusar"));
    actions.append(selecionar, recusar);
  }
  if (recebido && interesse.status === "selecionado") {
    const liberar = createElement("button", "button button-ghost", "Liberar reserva");
    liberar.type = "button";
    liberar.addEventListener("click", () => pedirMotivo("liberar"));
    actions.append(liberar);
  }
  if (recebido && interesse.status === "recusado") {
    const reabrir = createElement("button", "button button-secondary", "Reabrir");
    reabrir.type = "button";
    reabrir.addEventListener("click", () => executar("reabrir"));
    actions.append(reabrir);
  }
  if (!recebido && ["pendente", "selecionado"].includes(interesse.status)) {
    const desistir = createElement("button", "button button-ghost", "Desistir");
    desistir.type = "button";
    desistir.addEventListener("click", () => executar("desistir"));
    actions.append(desistir);
  }
  if (!recebido && interesse.status === "cancelado") {
    const retomar = createElement("button", "button button-secondary", "Retomar");
    retomar.type = "button";
    retomar.addEventListener("click", () => executar("retomar"));
    actions.append(retomar);
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
