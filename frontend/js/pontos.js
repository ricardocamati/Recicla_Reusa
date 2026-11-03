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
  if (ponto.ativo === false) {
    tags.append(createElement("span", "tag", "Inativo"));
  }
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
    const alternar = createElement(
      "button",
      "button button-secondary",
      ponto.ativo === false ? "Ativar" : "Desativar",
    );
    alternar.type = "button";
    alternar.dataset.acao = "situacao";
    alternar.addEventListener("click", async () => {
      const message = document.getElementById("pontos-message");
      try {
        await requestApi(`/api/pontos-coleta/${encodeURIComponent(ponto.id)}/situacao`, {
          method: "POST",
          body: JSON.stringify({ ativo: ponto.ativo === false }),
        });
        await carregarPontos();
        setMessage(
          message,
          ponto.ativo === false ? "Ponto reativado." : "Ponto desativado.",
          "success",
        );
      } catch (error) {
        handleError(error, message);
      }
    });
    actions.append(alternar, remover);
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

const NOME_STATUS = {
  entrega_prevista: "Entrega prevista",
  recebido: "Recebido",
  cancelado: "Cancelado",
  nao_recebido: "Não recebido",
};

async function carregarFila() {
  const lista = document.getElementById("fila-list");
  const message = document.getElementById("fila-message");
  if (!lista) return;
  lista.replaceChildren();
  try {
    const previstas = await requestApi(
      "/api/encaminhamentos?escopo=operador&status=entrega_prevista&limite=50",
    );
    if (!previstas.length) {
      renderEmptyState(lista, "Nenhuma entrega prevista no momento.");
      return;
    }
    for (const entrega of previstas) {
      let titulo = entrega.item_id;
      try {
        const item = await requestApi(`/api/itens/${encodeURIComponent(entrega.item_id)}`);
        titulo = item.titulo;
      } catch {
        /* item pode ter sido removido do catálogo */
      }
      const ponto = pontos.find((local) => local.id === entrega.ponto_id);
      const article = createElement("article", "item-card");
      article.dataset.encaminhamentoId = entrega.id;
      article.append(
        createElement("h3", "", titulo),
        createElement(
          "p",
          "item-card-description",
          `Entrega prevista em ${ponto ? ponto.nome : "ponto"} — ${NOME_STATUS[entrega.status]}`,
        ),
      );
      const actions = createElement("div", "item-actions");
      const receber = createElement("button", "button button-primary", "Confirmar recebimento");
      receber.type = "button";
      receber.dataset.acao = "receber";
      receber.addEventListener("click", async () => {
        try {
          await requestApi(
            `/api/encaminhamentos/${encodeURIComponent(entrega.id)}/acoes`,
            { method: "POST", body: JSON.stringify({ acao: "receber" }) },
          );
          await carregarFila();
          setMessage(message, "Recebimento confirmado.", "success");
        } catch (error) {
          handleError(error, message);
        }
      });
      const falha = createElement("button", "button button-ghost", "Não recebido");
      falha.type = "button";
      falha.dataset.acao = "nao_recebido";
      falha.addEventListener("click", async () => {
        const motivo = window.prompt("Motivo do não recebimento:");
        if (!motivo) return;
        try {
          await requestApi(
            `/api/encaminhamentos/${encodeURIComponent(entrega.id)}/acoes`,
            { method: "POST", body: JSON.stringify({ acao: "nao_recebido", motivo }) },
          );
          await carregarFila();
          setMessage(message, "Falha registrada; o item voltou ao autor.", "success");
        } catch (error) {
          handleError(error, message);
        }
      });
      actions.append(receber, falha);
      article.append(actions);
      lista.append(article);
    }
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
  if (usuario.tipo === "ponto_coleta") {
    const fila = document.getElementById("fila-operador");
    if (fila) {
      fila.hidden = false;
      await carregarFila();
    }
  }
}

document.addEventListener("DOMContentLoaded", initPontos);
