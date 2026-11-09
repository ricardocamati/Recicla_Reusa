import {
  comBotaoOcupado,
  createElement,
  createItemCard,
  handleError,
  itemPayloadFromForm,
  labelFor,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;
let itens = [];
let grupoAtual = "ativos";
let passoAtual = 1;

const DICAS_INTENCAO = {
  doacao: "A oferta entra no catálogo depois de publicada e pode receber interesses.",
  revenda: "A venda aparece no catálogo com preço; condição física não obriga reparo.",
};

function updateValueField() {
  const destination = document.getElementById("item-destination");
  const valueField = document.getElementById("item-value-field");
  const valueInput = document.getElementById("item-value");
  const hint = document.getElementById("item-intention-hint");
  const isResale = destination.value === "revenda";
  valueField.hidden = !isResale;
  valueInput.required = isResale;
  if (!isResale) valueInput.value = "";
  if (hint) hint.textContent = DICAS_INTENCAO[destination.value] || DICAS_INTENCAO.doacao;
}

function validarPassoAtual() {
  const etapa = document.querySelector(
    `#item-form .wizard-step[data-passo="${passoAtual}"]`,
  );
  const campos = [
    ...etapa.querySelectorAll("input[name], select[name], textarea[name]"),
  ].filter((campo) => campo.type !== "hidden");
  const invalido = campos.find((campo) => !campo.checkValidity());
  if (invalido) {
    invalido.reportValidity();
    return false;
  }
  return true;
}

function validarTudo() {
  const form = document.getElementById("item-form");
  const campos = [
    ...form.querySelectorAll(".wizard-step input[name], .wizard-step select[name], .wizard-step textarea[name]"),
  ].filter((campo) => campo.type !== "hidden");
  const invalido = campos.find((campo) => !campo.checkValidity());
  if (!invalido) return true;
  const etapa = invalido.closest(".wizard-step");
  if (etapa) irParaPasso(Number(etapa.dataset.passo));
  invalido.reportValidity();
  return false;
}

function irParaPasso(passo) {
  passoAtual = Math.min(3, Math.max(1, passo));
  document.querySelectorAll("#item-form .wizard-step").forEach((etapa) => {
    etapa.hidden = Number(etapa.dataset.passo) !== passoAtual;
  });
  document.querySelectorAll("#item-form .wizard-steps li").forEach((indicador) => {
    indicador.classList.toggle(
      "is-active",
      Number(indicador.dataset.indicador) === passoAtual,
    );
  });
  if (passoAtual === 3) renderRevisao();
}

function renderRevisao() {
  const form = document.getElementById("item-form");
  const lista = document.getElementById("item-review");
  lista.replaceChildren();
  const destino = form.elements.destino.value;
  const linhas = [
    ["Intenção", labelFor("destino", destino)],
    ["Título", form.elements.titulo.value || "-"],
    ["Categoria", labelFor("categoria", form.elements.categoria.value)],
    ["Condição", labelFor("condicao", form.elements.condicao.value)],
    ["Marca/Modelo", [form.elements.marca.value, form.elements.modelo.value].filter(Boolean).join(" ") || "-"],
  ];
  if (destino === "revenda") {
    linhas.push(["Preço", Number(form.elements.valor.value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })]);
  }
  linhas.forEach(([termo, valor]) => {
    const dt = createElement("dt", "", termo);
    const dd = createElement("dd", "", String(valor));
    lista.append(dt, dd);
  });
}

function resetItemForm() {
  const form = document.getElementById("item-form");
  form.reset();
  form.elements.item_id.value = "";
  document.getElementById("item-form-title").textContent = "Cadastrar oferta";
  document.getElementById("cancel-item-edit").hidden = true;
  document.getElementById("save-draft").hidden = false;
  setMessage(document.getElementById("item-message"));
  updateValueField();
  irParaPasso(1);
}

const PROXIMA_ACAO = {
  "doacao:reservado": { rotulo: "Declarar entrega" },
  "revenda:reservado": { rotulo: "Declarar entrega" },
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
  const botao = createElement("button", "button button-secondary", acao.rotulo);
  botao.type = "button";
  botao.dataset.acao = "entrega";
  botao.dataset.itemId = item.id;
  botao.addEventListener("click", () => {
    executarComandoItem(item.id, "entrega", "Entrega declarada. Aguardando confirmação.");
  });
  painel.append(botao);
  return painel;
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
    const acoes = createElement("div", "item-actions");
    if (item.status === "rascunho") {
      const publicar = createElement("button", "button button-primary", "Publicar");
      publicar.type = "button";
      publicar.dataset.acao = "publicar";
      publicar.dataset.itemId = item.id;
      publicar.addEventListener("click", () =>
        executarComandoItem(item.id, "publicar", "Oferta publicada."),
      );
      acoes.append(publicar);
    }
    if (item.status !== "arquivado") {
      const arquivar = createElement("button", "button button-ghost", "Arquivar");
      arquivar.type = "button";
      arquivar.dataset.acao = "arquivar";
      arquivar.dataset.itemId = item.id;
      arquivar.addEventListener("click", () =>
        executarComandoItem(item.id, "arquivar", "Oferta arquivada."),
      );
      acoes.append(arquivar);
    }
    if (acoes.childElementCount > 0) card.append(acoes);
    const fluxo = painelFluxo(item);
    if (fluxo) card.append(fluxo);
    list.append(card);
  });
}

async function loadOwnedItems() {
  const message = document.getElementById("my-items-message");
  setMessage(message, "Carregando suas ofertas...");
  try {
    const params = new URLSearchParams({ grupo: grupoAtual, offset: "0", limite: "20" });
    itens = await requestApi(`/api/itens/meus?${params.toString()}`);
    setMessage(message, `${itens.length} oferta(s) neste grupo.`, "success");
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
  document.getElementById("item-form-title").textContent = "Editar oferta";
  document.getElementById("cancel-item-edit").hidden = false;
  // Edição não publica nem cria rascunho novo.
  document.getElementById("save-draft").hidden = true;
  updateValueField();
  irParaPasso(2);
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function saveItem(event, publicar = true) {
  event.preventDefault();
  if (!validarTudo()) return;
  const form = document.getElementById("item-form");
  const message = document.getElementById("item-message");
  const itemId = String(form.elements.item_id.value || "");
  setMessage(message);
  const payload = itemPayloadFromForm(form);
  if (!itemId) payload.publicar = Boolean(publicar);
  try {
    await requestApi(itemId ? `/api/itens/${itemId}` : "/api/itens", {
      method: itemId ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    const aviso = itemId
      ? "Item atualizado."
      : publicar
        ? "Oferta publicada."
        : "Rascunho salvo. Publique quando estiver pronto.";
    resetItemForm();
    setMessage(message, aviso, "success");
    await Promise.all([loadOwnedItems(), loadIndicadores()]);
  } catch (error) {
    handleError(error, message);
  }
}

async function executarComandoItem(itemId, caminho, aviso) {
  const message = document.getElementById("my-items-message");
  setMessage(message);
  try {
    await requestApi(`/api/itens/${encodeURIComponent(itemId)}/${caminho}`, { method: "POST" });
    await Promise.all([loadOwnedItems(), loadIndicadores()]);
    setMessage(message, aviso, "success");
  } catch (error) {
    handleError(error, message);
  }
}

async function deleteItem(itemId) {
  const message = document.getElementById("my-items-message");
  setMessage(message);
  try {
    await requestApi(`/api/itens/${encodeURIComponent(itemId)}`, { method: "DELETE" });
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
    document.getElementById("indicador-ofertas").textContent = indicadores.ofertas_ativas ?? 0;
    document.getElementById("indicador-pendencias").textContent = indicadores.pendencias ?? 0;
    document.getElementById("indicador-vendidos").textContent = indicadores.vendidos;
    document.getElementById("indicador-total").textContent = indicadores.total;
    setMessage(message);
  } catch (error) {
    handleError(error, message);
  }
}

async function initItems() {
  const grupoDaUrl = new URLSearchParams(window.location.search).get("grupo");
  if (["ativos", "em_andamento", "encerrados"].includes(grupoDaUrl)) {
    grupoAtual = grupoDaUrl;
  }
  document.querySelectorAll("[data-grupo]").forEach((aba) => {
    const ativa = aba.dataset.grupo === grupoAtual;
    aba.classList.toggle("is-active", ativa);
    aba.setAttribute("aria-selected", String(ativa));
  });
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  if (usuario.tipo !== "pessoa") {
    document.getElementById("item-management").hidden = true;
    document.getElementById("not-donor").hidden = false;
    return;
  }
  const formularioItem = document.getElementById("item-form");
  formularioItem.addEventListener("submit", (evento) =>
    comBotaoOcupado(
      formularioItem.querySelector("button[type='submit']"),
      (e) => saveItem(e, true),
    )(evento),
  );
  document.getElementById("item-destination").addEventListener("change", updateValueField);
  document.getElementById("cancel-item-edit").addEventListener("click", resetItemForm);
  document.getElementById("save-draft").addEventListener("click", (evento) => {
    if (!validarTudo()) return;
    saveItem(evento, false);
  });
  document.querySelectorAll("#item-form [data-passo-acao]").forEach((botao) => {
    botao.addEventListener("click", () => {
      if (botao.dataset.passoAcao === "proximo") {
        if (!validarPassoAtual()) return;
        irParaPasso(passoAtual + 1);
      } else {
        irParaPasso(passoAtual - 1);
      }
    });
  });
  document.querySelectorAll("[data-grupo]").forEach((aba) => {
    aba.addEventListener("click", () => {
      grupoAtual = aba.dataset.grupo;
      document.querySelectorAll("[data-grupo]").forEach((outra) => {
        const ativa = outra === aba;
        outra.classList.toggle("is-active", ativa);
        outra.setAttribute("aria-selected", String(ativa));
      });
      loadOwnedItems();
    });
  });
  updateValueField();
  irParaPasso(1);
  await carregarReferencias();
  await Promise.all([loadOwnedItems(), loadIndicadores()]);
}

document.addEventListener("DOMContentLoaded", initItems);
