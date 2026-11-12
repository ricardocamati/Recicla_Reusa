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
let proximoCardId = 0;

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

function valorDatetimeLocal(iso) {
  if (!iso) return "";
  const data = new Date(iso);
  const pad = (numero) => String(numero).padStart(2, "0");
  return `${data.getFullYear()}-${pad(data.getMonth() + 1)}-${pad(data.getDate())}T${pad(data.getHours())}:${pad(data.getMinutes())}`;
}

function exibirPrevisao(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

async function atualizarCombinacao(interesse, recebido, requisicao, confere, mensagem, relerConflito = false) {
  if (acaoEmCurso) return;
  acaoEmCurso = true;
  const chave = recebido ? "recebidos" : "meus";
  const { message, listaId } = contexto(chave);
  // Restaura só os controles que esta operação bloqueou; não habilita ações proibidas.
  const controles = [...document.querySelectorAll(".interest-card button, .interest-card input")]
    .map((elemento) => [elemento, elemento.disabled]);
  const tinhaFoco = document.getElementById(listaId).contains(document.activeElement);
  controles.forEach(([elemento]) => { elemento.disabled = true; });
  setMessage(message, "Confirmando combinação...");
  try {
    const resposta = await requisicao();
    const relidas = await carregarTudo();
    if (!relidas[chave]) {
      setMessage(message, "Não foi possível atualizar para confirmar a combinação. Os campos foram mantidos; tente Atualizar.", "error");
      return;
    }
    const atual = registros[chave].find((i) => i.id === interesse.id);
    if (confere(resposta, atual)) {
      setMessage(message, mensagem, "success");
    } else {
      setMessage(message, "A combinação mudou novamente. Confira o resumo atualizado antes de continuar.", "error");
    }
  } catch (error) {
    if (relerConflito && error?.status === 409) await carregarTudo();
    // Erro de gravação/rede conserva a edição e não reenvia a mutação.
    handleError(error, message);
  } finally {
    acaoEmCurso = false;
    controles.forEach(([elemento, desabilitado]) => {
      if (elemento.isConnected) elemento.disabled = desabilitado;
    });
    if (tinhaFoco && !document.getElementById(listaId).contains(document.activeElement)) {
      const novo = [...document.getElementById(listaId).querySelectorAll("article")]
        .find((cartao) => cartao.dataset.interesseId === interesse.id);
      (novo?.querySelector(".combination-toggle") || novo?.querySelector(".interest-details-toggle") || message).focus();
    }
  }
}

function cartaoInteresse(interesse, { recebido }) {
  const article = createElement("article", "item-card interest-card");
  article.dataset.interesseId = interesse.id;
  const cardId = `interesse-card-${++proximoCardId}`;
  const detalhes = createElement("div", "interest-details");
  detalhes.id = `${cardId}-detalhes`;
  detalhes.hidden = true;
  const verDetalhes = createElement("button", "button button-ghost", "Ver detalhes");
  verDetalhes.type = "button";
  verDetalhes.classList.add("interest-details-toggle");
  verDetalhes.setAttribute("aria-controls", detalhes.id);
  verDetalhes.setAttribute("aria-expanded", "false");
  verDetalhes.addEventListener("click", () => {
    detalhes.hidden = !detalhes.hidden;
    verDetalhes.setAttribute("aria-expanded", String(!detalhes.hidden));
    verDetalhes.textContent = detalhes.hidden ? "Ver detalhes" : "Recolher";
    if (detalhes.hidden) {
      const editor = article.querySelector("form.combination-form");
      if (editor) {
        editor.hidden = true;
        editor.reset();
        article.querySelector(".combination-toggle").setAttribute("aria-expanded", "false");
      }
      verDetalhes.focus();
    }
  });
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
    detalhes.append(createElement("p", "item-card-description", `Motivo: ${interesse.motivo}`));
  }

  const editavel = interesse.status === "selecionado" && item?.status === "reservado";
  if (interesse.status === "selecionado" || interesse.combinacao) {
    const combinacao = interesse.combinacao;
    const situacao = combinacao
      ? `Combinação r${combinacao.revisao}: ${combinacao.local_texto} — ${
          combinacao.aceito_por ? "aceita" : combinacao.proposto_por === usuario.id
            ? "aguardando aceite da outra pessoa" : "aguardando seu aceite"
        }`
      : "Ainda sem combinação de entrega.";
    article.append(createElement("p", "item-card-description", situacao));
    if (combinacao?.previsao) article.append(createElement("p", "field-hint", `Previsão: ${exibirPrevisao(combinacao.previsao)}`));
    if (combinacao?.observacao) article.append(createElement("p", "field-hint", `Observação: ${combinacao.observacao}`));

    if (editavel) {
      const form = createElement("form", "form-stack combination-form");
      const local = createElement("input", "", "");
      local.name = "local_texto";
      local.placeholder = "Local da entrega";
      local.maxLength = 200;
      local.minLength = 3;
      local.required = true;
      const previsao = createElement("input", "", "");
      previsao.name = "previsao";
      previsao.type = "datetime-local";
      previsao.step = "60";
      let preenchido = "";
      const instanteOriginal = combinacao?.previsao || null;
      const observacao = createElement("input", "", "");
      observacao.name = "observacao";
      observacao.placeholder = "Observação (opcional)";
      observacao.maxLength = 300;
      for (const [campo, texto] of [[local, "Local da entrega"], [previsao, "Previsão da entrega (opcional)"], [observacao, "Observação (opcional)"]]) {
        campo.id = `${cardId}-${campo.name}`;
        const label = createElement("label", "", texto);
        label.htmlFor = campo.id;
        form.append(label, campo);
      }
      const propor = createElement("button", "button button-secondary", combinacao ? "Salvar alteração" : "Enviar proposta");
      propor.type = "submit";
      const cancelar = createElement("button", "button button-ghost", "Cancelar edição");
      cancelar.type = "button";
      form.append(propor, cancelar);
      form.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const previsaoMantida = preenchido && previsao.value === preenchido;
        const dados = {
          local_texto: local.value.trim(),
          previsao: previsaoMantida
            ? instanteOriginal
            : previsao.value ? new Date(previsao.value).toISOString() : null,
          observacao: observacao.value.trim() || null,
        };
        await atualizarCombinacao(interesse, recebido,
          () => requestApi(`/api/interesses/${encodeURIComponent(interesse.id)}/combinacao`, {
            method: "PUT", body: JSON.stringify(dados),
          }),
          (resposta, atual) => Boolean(resposta?.combinacao)
            && atual?.combinacao?.revisao === resposta.combinacao.revisao,
          "Combinação atualizada.");
      });
      form.id = `${cardId}-combinacao`;
      form.hidden = true;
      const abrirEdicao = createElement("button", "button button-secondary combination-toggle", combinacao ? "Alterar combinação" : "Propor combinação");
      abrirEdicao.type = "button";
      abrirEdicao.setAttribute("aria-controls", form.id);
      abrirEdicao.setAttribute("aria-expanded", "false");
      abrirEdicao.addEventListener("click", () => {
        if (form.hidden) {
          local.value = combinacao?.local_texto || "";
          previsao.value = valorDatetimeLocal(combinacao?.previsao);
          preenchido = previsao.value;
          observacao.value = combinacao?.observacao || "";
        }
        form.hidden = false;
        abrirEdicao.setAttribute("aria-expanded", "true");
        local.focus();
      });
      cancelar.addEventListener("click", () => {
        form.hidden = true;
        form.reset();
        preenchido = "";
        abrirEdicao.setAttribute("aria-expanded", "false");
        abrirEdicao.focus();
      });
      article.append(abrirEdicao, form);
    }

    if (editavel && combinacao && !combinacao.aceito_por && combinacao.proposto_por !== usuario.id) {
      const aceitarCombinacao = createElement("button", "button button-primary", "Aceitar combinação");
      aceitarCombinacao.type = "button";
      aceitarCombinacao.addEventListener("click", () => atualizarCombinacao(interesse, recebido,
        () => requestApi(`/api/interesses/${encodeURIComponent(interesse.id)}/combinacao/aceite`, {
          method: "POST", body: JSON.stringify({ revisao: combinacao.revisao }),
        }),
        (_resposta, atual) => atual?.combinacao?.revisao === combinacao.revisao
          && atual.combinacao.aceito_por === usuario.id,
        "Combinação aceita.", true));
      article.append(aceitarCombinacao);
    }
    if (interesse.status === "selecionado" && combinacao?.aceito_por && !recebido && item?.status === "aguardando_confirmacao") {
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
        new ApiError(400, { detail: "O motivo é obrigatório." }),
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
  if (recebido && editavel) {
    const liberar = createElement("button", "button button-ghost", "Liberar reserva");
    liberar.type = "button";
    liberar.addEventListener("click", () => pedirMotivo("liberar"));
    const adicionais = createElement("div", "item-actions");
    adicionais.append(liberar);
    detalhes.append(adicionais);
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
  article.append(verDetalhes, detalhes);
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
