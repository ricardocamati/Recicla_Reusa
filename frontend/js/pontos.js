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
let pontos = [];
const meusPontos = new Set();

function cartaoPonto(ponto) {
  const article = createElement("article", "item-card");
  const tags = createElement("div", "item-tags");
  tags.append(createElement("span", "tag", "Ponto de coleta"));
  article.append(tags, createElement("h3", "", ponto.nome));

  const endereco = ponto.endereco || {};
  article.append(
    createElement(
      "p",
      "item-card-description",
      [endereco.logradouro, endereco.numero, endereco.cidade, endereco.cep]
        .filter(Boolean)
        .join(", "),
    ),
  );
  const meta = createElement("div", "item-meta");
  meta.append(
    createElement("span", "", ponto.categorias_aceitas.map((c) => labelFor("categoria", c)).join(", ")),
    createElement("span", "", ponto.horario_atendimento),
  );
  article.append(meta);

  if (usuario.tipo === "ponto_coleta" && meusPontos.has(ponto.id)) {
    const actions = createElement("div", "item-actions");
    const remover = createElement("button", "button button-ghost", "Excluir");
    remover.type = "button";
    remover.addEventListener("click", async () => {
      const message = document.getElementById("pontos-message");
      try {
        await requestApi(`/api/pontos-coleta/${encodeURIComponent(ponto.id)}`, { method: "DELETE" });
        setMessage(message, "Ponto excluído.", "success");
        await carregarPontos();
      } catch (error) {
        handleError(error, message);
      }
    });
    actions.append(remover);
    article.append(actions);
  }
  return article;
}

async function carregarPontos() {
  const message = document.getElementById("pontos-message");
  const lista = document.getElementById("pontos-list");
  const cidade = document.getElementById("filtro-ponto-cidade").value.trim();
  const categoria = document.getElementById("filtro-ponto-categoria").value;
  const parametros = new URLSearchParams();
  if (cidade) parametros.set("cidade", cidade);
  if (categoria) parametros.set("categoria", categoria);
  const consulta = parametros.toString() ? `?${parametros}` : "";

  setMessage(message, "Carregando pontos...");
  try {
    if (usuario.tipo === "ponto_coleta") {
      // O servidor restringe o escopo à conta da sessão.
      const proprios = await requestApi("/api/pontos-coleta?escopo=meus");
      meusPontos.clear();
      proprios.forEach((ponto) => meusPontos.add(ponto.id));
    }
    pontos = await requestApi(`/api/pontos-coleta${consulta}`);
    lista.replaceChildren();
    if (pontos.length === 0) {
      renderEmptyState(lista, "Nenhum ponto encontrado", "Ajuste os filtros ou tente outra cidade.");
    } else {
      pontos.forEach((ponto) => lista.append(cartaoPonto(ponto)));
    }
    setMessage(message, `${pontos.length} ponto(s) de coleta.`, "success");
  } catch (error) {
    handleError(error, message);
    lista.replaceChildren();
  }
}

function categoriasSelecionadas(form) {
  return Array.from(form.elements.categorias_aceitas.selectedOptions).map(
    (opcao) => opcao.value,
  );
}

async function salvarPonto(evento) {
  evento.preventDefault();
  const form = evento.currentTarget;
  const message = document.getElementById("ponto-form-message");
  setMessage(message);
  const dados = new FormData(form);
  const payload = {
    nome: String(dados.get("nome") || "").trim(),
    endereco: {
      logradouro: String(dados.get("logradouro") || "").trim(),
      numero: String(dados.get("numero") || "").trim(),
      complemento: null,
      cep: String(dados.get("cep") || "").trim(),
      cidade: String(dados.get("cidade") || "").trim(),
    },
    categorias_aceitas: categoriasSelecionadas(form),
    horario_atendimento: String(dados.get("horario_atendimento") || "").trim(),
  };
  try {
    await requestApi("/api/pontos-coleta", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    setMessage(message, "Ponto cadastrado.", "success");
    await carregarPontos();
  } catch (error) {
    handleError(error, message);
  }
}

async function initPontos() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);

  document.getElementById("pontos-filtros").addEventListener("submit", (evento) => {
    evento.preventDefault();
    carregarPontos();
  });

  const admin = document.getElementById("ponto-admin");
  if (usuario.tipo === "ponto_coleta") {
    admin.hidden = false;
    document.getElementById("ponto-form").addEventListener("submit", salvarPonto);
  }

  await carregarPontos();
}

document.addEventListener("DOMContentLoaded", initPontos);
