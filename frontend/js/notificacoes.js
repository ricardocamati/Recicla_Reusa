import {
  createElement,
  handleError,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;

const FILTROS = {
  todas: "",
  "nao-lidas": "false",
  lidas: "true",
};

function formatarData(valor) {
  if (!valor) return "";
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return "";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(data);
}

function cartaoAviso(aviso) {
  const article = createElement("article", aviso.lida ? "item-card" : "item-card item-card-unread");
  const tags = createElement("div", "item-tags");
  tags.append(createElement("span", aviso.lida ? "tag tag-neutral" : "tag", aviso.lida ? "Lida" : "Não lida"));
  article.append(tags, createElement("h3", "", aviso.titulo));
  article.append(createElement("p", "item-card-description", aviso.mensagem));
  article.append(createElement("small", "", formatarData(aviso.data_adicao)));

  if (aviso.link) {
    const abrir = createElement("a", "button button-ghost", "Abrir");
    abrir.href = aviso.link;
    const acoesLink = createElement("div", "item-actions");
    acoesLink.append(abrir);
    article.append(acoesLink);
  }

  if (!aviso.lida) {
    const actions = createElement("div", "item-actions");
    const marcar = createElement("button", "button button-secondary", "Marcar como lida");
    marcar.type = "button";
    marcar.addEventListener("click", async () => {
      const message = document.getElementById("notificacoes-message");
      try {
        await requestApi(`/api/notificacoes/${encodeURIComponent(aviso.id)}`, {
          method: "PATCH",
          body: JSON.stringify({ lida: true }),
        });
        await carregarNotificacoes();
      } catch (error) {
        handleError(error, message);
      }
    });
    actions.append(marcar);
    article.append(actions);
  }
  return article;
}

async function carregarNotificacoes() {
  const message = document.getElementById("notificacoes-message");
  const lista = document.getElementById("notificacoes-list");
  const filtro = document.getElementById("filtro-lida").value;
  const parametro = FILTROS[filtro] ?? "";
  setMessage(message, "Carregando notificações...");
  try {
    const consulta = parametro ? `?lida=${parametro}` : "";
    const avisos = await requestApi(`/api/notificacoes${consulta}`);
    lista.replaceChildren();
    if (avisos.length === 0) {
      renderEmptyState(lista, "Caixa de entrada vazia", "Avisos sobre interesses e itens aparecem aqui.");
    } else {
      avisos.forEach((aviso) => lista.append(cartaoAviso(aviso)));
    }
    if (filtro === "todas") {
      const naoLidas = avisos.filter((aviso) => !aviso.lida).length;
      setMessage(message, `${avisos.length} aviso(s), ${naoLidas} não lido(s).`, "success");
    } else {
      setMessage(message, `${avisos.length} aviso(s) no filtro selecionado.`, "success");
    }
  } catch (error) {
    handleError(error, message);
    lista.replaceChildren();
  }
}

async function initNotificacoes() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  document.getElementById("filtro-lida").addEventListener("change", carregarNotificacoes);
  document.getElementById("atualizar-notificacoes").addEventListener("click", carregarNotificacoes);
  await carregarNotificacoes();
}

document.addEventListener("DOMContentLoaded", initNotificacoes);
