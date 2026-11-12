import {
  ApiError,
  createElement,
  handleError,
  labelFor,
  labelForInteresse,
  renderEmptyState,
  requestApi,
  requestAllPages,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;
const itens = new Map();
// Filtro de apresentação: Ativos reúne pendente/selecionado; Histórico reúne os encerrados.
const GRUPOS = {
  ativos: new Set(["pendente", "selecionado"]),
  historico: new Set(["cancelado", "recusado", "encerrado"]),
};
const filtros = { meus: "ativos", recebidos: "ativos" };
const registros = { meus: null, recebidos: null };
const versoes = { meus: 0, recebidos: 0 };
let acaoEmCurso = false;

async function carregarItem(itemId, atualizar = false) {
  if (atualizar || !itens.has(itemId)) {
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

  if (interesse.status === "selecionado") {
    const combinacao = interesse.combinacao;
    const situacao = combinacao
      ? `Combinação r${combinacao.revisao}: ${combinacao.local_texto} — ${
          combinacao.aceito_por ? "aceita" : "aguardando aceite da contraparte"
        }`
      : "Ainda sem combinação de entrega.";
    article.append(createElement("p", "item-card-description", situacao));

    const form = createElement("form", "form-stack combination-form");
    const local = createElement("input", "", "");
    local.name = "local_texto";
    local.placeholder = "Local da entrega";
    local.maxLength = 200;
    local.required = true;
    const previsao = createElement("input", "", "");
    previsao.name = "previsao";
    previsao.type = "datetime-local";
    const observacao = createElement("input", "", "");
    observacao.name = "observacao";
    observacao.placeholder = "Observação (opcional)";
    observacao.maxLength = 300;
    const propor = createElement("button", "button button-secondary", combinacao ? "Alterar combinação" : "Propor combinação");
    propor.type = "submit";
    form.append(local, previsao, observacao, propor);
    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      try {
        await requestApi(`/api/interesses/${encodeURIComponent(interesse.id)}/combinacao`, {
          method: "PUT",
          body: JSON.stringify({
            local_texto: local.value.trim(),
            previsao: previsao.value ? new Date(previsao.value).toISOString() : null,
            observacao: observacao.value.trim() || null,
          }),
        });
        await carregarTudo();
      } catch (error) {
        handleError(error, recebido ? byIdRecebidos() : byIdMeus());
      }
    });
    article.append(form);

    if (combinacao && !combinacao.aceito_por && combinacao.proposto_por !== usuario.id) {
      const aceitarCombinacao = createElement("button", "button button-primary", "Aceitar combinação");
      aceitarCombinacao.type = "button";
      aceitarCombinacao.addEventListener("click", async () => {
        try {
          await requestApi(
            `/api/interesses/${encodeURIComponent(interesse.id)}/combinacao/aceite`,
            { method: "POST", body: JSON.stringify({ revisao: combinacao.revisao }) },
          );
          await carregarTudo();
        } catch (error) {
          handleError(error, recebido ? byIdRecebidos() : byIdMeus());
        }
      });
      article.append(aceitarCombinacao);
    }
    if (combinacao && combinacao.aceito_por && !recebido) {
      const confirmar = createElement("button", "button button-primary", "Confirmar recebimento");
      confirmar.type = "button";
      confirmar.addEventListener("click", async () => {
        try {
          await requestApi(`/api/itens/${encodeURIComponent(interesse.item_id)}/recebimento`, {
            method: "POST",
          });
          await carregarTudo();
        } catch (error) {
          handleError(error, byIdMeus());
        }
      });
      article.append(confirmar);
    }
  }

  const actions = createElement("div", "item-actions");
  const executar = async (acao, motivo = null, sucesso = null) => {
    if (acaoEmCurso) return;
    acaoEmCurso = true;
    const chave = recebido ? "recebidos" : "meus";
    const alvo = recebido ? byIdRecebidos() : byIdMeus();
    const tinhaFoco = article.contains(document.activeElement);
    const bloquear = (valor) => document.querySelectorAll(".item-actions button").forEach((b) => { b.disabled = valor; });
    bloquear(true);
    let confirmada = false;
    let incerta = false;
    try {
      try {
        await requestApi(`/api/interesses/${encodeURIComponent(interesse.id)}/acoes`, {
          method: "POST",
          body: JSON.stringify({ acao, motivo }),
        });
        confirmada = true;
      } catch (error) {
        if (error instanceof ApiError && error.status < 500) throw error;
        // Resposta de rede perdida ou erro 5xx: reler sem repetir a mutação.
        incerta = true;
      }
      const relidas = await carregarTudo();
      if (!relidas[chave]) {
        setMessage(alvo, "Não foi possível atualizar para confirmar o estado. A última lista foi mantida; tente Atualizar.", "error");
        return;
      }
      const esperado = { desistir: "cancelado", retomar: "pendente", reabrir: "pendente",
        recusar: "recusado", selecionar: "selecionado", liberar: "cancelado" }[acao];
      const atual = registros[chave].find((i) => i.id === interesse.id);
      if (atual?.status === esperado) {
        setMessage(alvo, sucesso || "Estado do interesse atualizado.", "success");
      } else if (incerta) {
        setMessage(alvo, "Não foi possível confirmar a operação. A lista foi relida; confira o estado atual antes de tentar novamente.", "error");
      } else if (confirmada) {
        setMessage(alvo, "Operação confirmada; o estado mudou novamente. Confira a lista atualizada.");
      }
    } catch (error) {
      handleError(error, alvo);
    } finally {
      acaoEmCurso = false;
      bloquear(false);
      if (tinhaFoco && !article.isConnected) alvo.focus();
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
  if (recebido && interesse.status === "recusado" && item?.status === "disponivel") {
    const reabrir = createElement("button", "button button-secondary", "Reabrir");
    reabrir.type = "button";
    reabrir.addEventListener("click", () => executar("reabrir"));
    actions.append(reabrir);
  }
  if (!recebido && ["pendente", "selecionado"].includes(interesse.status)) {
    const desistir = createElement("button", "button button-ghost", "Desistir");
    desistir.type = "button";
    desistir.addEventListener("click", () => executar("desistir", null, "Você desistiu deste interesse."));
    actions.append(desistir);
  }
  if (!recebido && interesse.status === "cancelado" && item?.status === "disponivel") {
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

function visiveis(interesses, filtro) {
  return interesses.filter((interesse) => GRUPOS[filtro].has(interesse.status));
}

function contexto(chave) {
  return {
    recebido: chave === "recebidos",
    listaId: chave === "meus" ? "meus-interesses-list" : "recebidos-interesses-list",
    message: document.getElementById(`${chave}-message`),
  };
}

function renderEscopo(chave) {
  const todos = registros[chave];
  if (todos === null) return; // Falha inicial não é uma lista vazia.
  const { recebido, listaId } = contexto(chave);
  const filtro = filtros[chave];
  const lista = document.getElementById(listaId);
  const selecionados = visiveis(todos, filtro);
  const desconhecidos = todos.filter((i) => !GRUPOS.ativos.has(i.status) && !GRUPOS.historico.has(i.status));
  const historico = filtro === "historico";
  const rotulo = historico ? "no histórico" : "ativo(s)";
  const alerta = desconhecidos.length ? ` ${desconhecidos.length} não classificado(s).` : "";
  document.getElementById(`${chave}-count`).textContent = `${selecionados.length} interesse(s) ${rotulo}.${alerta}`;
  lista.replaceChildren();
  if (!selecionados.length && !desconhecidos.length) {
    const noOutro = visiveis(todos, historico ? "ativos" : "historico").length;
    const titulo = historico ? "Nada no histórico" : "Nenhum interesse ativo";
    const texto = noOutro
      ? (historico ? "Os interesses em andamento estão em Ativos." : "Seus interesses encerrados estão no Histórico.")
      : (historico ? "Interesses cancelados, recusados ou encerrados aparecem aqui."
        : recebido ? "Quando alguém se interessar pelos seus itens, a decisão aparece aqui."
          : "Abra o catálogo e manifeste interesse em um item de doação ou revenda.");
    renderEmptyState(lista, titulo, texto);
  }
  selecionados.forEach((interesse) => lista.append(cartaoInteresse(interesse, { recebido })));
  if (desconhecidos.length) {
    lista.append(createElement("p", "field-hint", "Há interesses com situação não reconhecida. Atualize a lista para conferir."));
    // Sem reclassificar nem inventar ações para um estado fora do contrato.
    desconhecidos.forEach((interesse) => lista.append(cartaoInteresse(interesse, { recebido })));
  }
}

async function carregarEscopo(chave) {
  const { message, listaId } = contexto(chave);
  const lista = document.getElementById(listaId);
  const versao = ++versoes[chave];
  lista.setAttribute("aria-busy", "true");
  setMessage(message, "Carregando interesses...");
  try {
    const interesses = await requestAllPages("/api/interesses", { escopo: chave });
    const ids = [...new Set(interesses.map((interesse) => interesse.item_id))];
    await Promise.all(ids.map((id) => carregarItem(id, true)));
    if (versao !== versoes[chave]) return false;
    registros[chave] = interesses;
    if (chave === "recebidos") document.getElementById("recebidos-section").hidden = false;
    renderEscopo(chave);
    setMessage(message, "Lista atualizada.", "success");
    return true;
  } catch (error) {
    if (versao !== versoes[chave]) return false;
    if (chave === "recebidos" && error?.status === 403) {
      registros[chave] = null;
      lista.replaceChildren();
      document.getElementById("recebidos-section").hidden = true;
      return false;
    }
    handleError(error, message);
    if (registros[chave] !== null) {
      // Mantém os últimos dados conhecidos, sem fingir que a releitura deu certo.
      message.textContent += " Não foi possível atualizar; a última lista foi mantida.";
    }
    return false;
  } finally {
    if (versao === versoes[chave]) lista.setAttribute("aria-busy", "false");
  }
}

async function carregarMeus() { return carregarEscopo("meus"); }
async function carregarRecebidos() { return carregarEscopo("recebidos"); }

async function carregarTudo() {
  const [meus, recebidos] = await Promise.all([carregarMeus(), carregarRecebidos()]);
  return { meus, recebidos };
}

function ligarFiltro(chave) {
  const container = document.getElementById(`${chave}-filtros`);
  const botoes = [...container.querySelectorAll("[data-filtro]")];
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      if (filtros[chave] === botao.dataset.filtro) return;
      filtros[chave] = botao.dataset.filtro;
      botoes.forEach((outro) => {
        const ativo = outro.dataset.filtro === filtros[chave];
        outro.classList.toggle("is-active", ativo);
        outro.setAttribute("aria-pressed", String(ativo));
      });
      // A lista completa já foi carregada: filtrar não depende de outra requisição.
      renderEscopo(chave);
    });
  });
}

async function initInteresses() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  ligarFiltro("meus");
  ligarFiltro("recebidos");
  document.getElementById("atualizar-meus").addEventListener("click", carregarMeus);
  document.getElementById("atualizar-recebidos").addEventListener("click", carregarRecebidos);
  await carregarTudo();
}

document.addEventListener("DOMContentLoaded", initInteresses);
