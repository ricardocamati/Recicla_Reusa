import {
  ROTULOS,
  comBotaoOcupado,
  createElement,
  handleError,
  labelFor,
  renderEmptyState,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

const PAGE_SIZE = 20;
let usuario;
let pontos = [];
let meusPontos = new Set();
let offsetAtual = 0;

function normalizarAtivo(valor) {
  const texto = String(valor || "").trim().toLowerCase();
  if (["", "todos", "all"].includes(texto)) return null;
  if (["ativos", "ativo", "true", "1"].includes(texto)) return true;
  if (["inativos", "inativo", "false", "0"].includes(texto)) return false;
  return null;
}


function enderecoFormulario(ponto) {
  const e = ponto.endereco || {};
  return {
    logradouro: e.logradouro || "",
    numero: e.numero || "",
    complemento: e.complemento || "",
    cep: e.cep || "",
    cidade: e.cidade || "",
  };
}

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
      [endereco.logradouro, endereco.numero, endereco.complemento, endereco.cidade, endereco.cep]
        .filter(Boolean)
        .join(", "),
    ),
  );
  const meta = createElement("div", "item-meta");
  meta.append(
    createElement("span", "", (ponto.categorias_aceitas || []).map((c) => labelFor("categoria", c)).join(", ")),
    createElement("span", "", ponto.horario_atendimento),
  );
  article.append(meta);

  if (usuario.tipo === "ponto_coleta" && meusPontos.has(ponto.id)) {
    const actions = createElement("div", "item-actions");
    const editar = createElement("button", "button button-secondary", "Editar");
    editar.type = "button";
    editar.dataset.acao = "editar";
    editar.dataset.pontoId = ponto.id;
    editar.addEventListener("click", () => iniciarEdicaoPonto(ponto.id));

    const alternar = createElement(
      "button",
      "button button-secondary",
      ponto.ativo === false ? "Ativar" : "Desativar",
    );
    alternar.type = "button";
    alternar.dataset.acao = "situacao";
    alternar.dataset.pontoId = ponto.id;
    alternar.addEventListener("click", comBotaoOcupado(alternar, () => alternarSituacao(ponto.id)));

    const remover = createElement("button", "button button-ghost", "Excluir");
    remover.type = "button";
    remover.dataset.acao = "excluir";
    remover.dataset.pontoId = ponto.id;
    remover.addEventListener("click", comBotaoOcupado(remover, () => excluirPonto(ponto.id)));

    actions.append(editar, alternar, remover);
    article.append(actions);
  }
  return article;
}


async function carregarPontos() {
  const message = document.getElementById("pontos-message");
  const lista = document.getElementById("pontos-list");
  const cidade = document.getElementById("filtro-ponto-cidade").value.trim();
  const categoria = document.getElementById("filtro-ponto-categoria").value;
  const ativo = normalizarAtivo(document.getElementById("filtro-ponto-ativo").value);

  const parametros = new URLSearchParams();
  parametros.set("escopo", "meus");
  if (cidade) parametros.set("cidade", cidade);
  if (categoria) parametros.set("categoria", categoria);
  if (ativo !== null) parametros.set("ativo", String(ativo));
  parametros.set("offset", String(offsetAtual));
  parametros.set("limite", String(PAGE_SIZE + 1));

  setMessage(message, "Carregando locais...");
  try {
    const resposta = await requestApi(`/api/pontos-coleta?${parametros.toString()}`);
    pontos = resposta;
    meusPontos = new Set(resposta.map((ponto) => ponto.id));
    lista.replaceChildren();
    if (resposta.length === 0) {
      renderEmptyState(lista, "Nenhum local encontrado", "Ajuste os filtros ou cadastre um novo local.");
    } else {
      resposta.slice(0, PAGE_SIZE).forEach((ponto) => lista.append(cartaoPonto(ponto)));
    }
    const pagina = Math.floor(offsetAtual / PAGE_SIZE) + 1;
    document.getElementById("ponto-page").textContent = `Página ${pagina}`;
    document.getElementById("ponto-previous").disabled = offsetAtual === 0;
    document.getElementById("ponto-next").disabled = resposta.length <= PAGE_SIZE;
    setMessage(message, `${Math.min(resposta.length, PAGE_SIZE)} local(is) de coleta.`, "success");
    return { ok: true, vazio: resposta.length === 0 };
  } catch (error) {
    handleError(error, message);
    lista.replaceChildren();
    pontos = [];
    return { ok: false, vazio: false };
  }
}

function categoriasSelecionadas(form) {
  return Array.from(form.elements.categorias_aceitas.selectedOptions).map((opcao) => opcao.value);
}

function payloadPonto(form) {
  const dados = new FormData(form);
  return {
    nome: String(dados.get("nome") || "").trim(),
    endereco: {
      logradouro: String(dados.get("logradouro") || "").trim(),
      numero: String(dados.get("numero") || "").trim(),
      complemento: String(dados.get("complemento") || "").trim() || null,
      cep: String(dados.get("cep") || "").trim(),
      cidade: String(dados.get("cidade") || "").trim(),
    },
    categorias_aceitas: categoriasSelecionadas(form),
    horario_atendimento: String(dados.get("horario_atendimento") || "").trim(),
  };
}

function resetarFormularioPonto() {
  const form = document.getElementById("ponto-form");
  form.reset();
  form.elements.ponto_id.value = "";
  document.getElementById("ponto-admin-title").textContent = "Novo local";
  document.getElementById("ponto-cancel-edit").hidden = true;
  setMessage(document.getElementById("ponto-form-message"));
}

function iniciarEdicaoPonto(pontoId) {
  const ponto = pontos.find((item) => item.id === pontoId);
  if (!ponto) return;
  const form = document.getElementById("ponto-form");
  form.elements.ponto_id.value = ponto.id;
  form.elements.nome.value = ponto.nome || "";
  const endereco = enderecoFormulario(ponto);
  form.elements.logradouro.value = endereco.logradouro;
  form.elements.numero.value = endereco.numero;
  form.elements.complemento.value = endereco.complemento;
  form.elements.cep.value = endereco.cep;
  form.elements.cidade.value = endereco.cidade;
  Array.from(form.elements.categorias_aceitas.options).forEach((opcao) => {
    opcao.selected = (ponto.categorias_aceitas || []).includes(opcao.value);
  });
  form.elements.horario_atendimento.value = ponto.horario_atendimento || "";
  document.getElementById("ponto-admin-title").textContent = "Editar local";
  document.getElementById("ponto-cancel-edit").hidden = false;
}


async function salvarPonto(evento) {
  evento.preventDefault();
  const form = evento.currentTarget;
  const message = document.getElementById("ponto-form-message");
  setMessage(message);
  const pontoId = String(form.elements.ponto_id.value || "").trim();
  const payload = payloadPonto(form);
  try {
    const resposta = pontoId
      ? await requestApi(`/api/pontos-coleta/${encodeURIComponent(pontoId)}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
      : await requestApi("/api/pontos-coleta", {
          method: "POST",
          body: JSON.stringify(payload),
        });
    if (pontoId) {
      const indice = pontos.findIndex((item) => item.id === pontoId);
      if (indice >= 0) pontos[indice] = resposta;
      meusPontos.add(resposta.id);
    } else {
      meusPontos.add(resposta.id);
    }
    resetarFormularioPonto();
    setMessage(message, pontoId ? "Local atualizado." : "Local cadastrado.", "success");
    await carregarPontos();
  } catch (error) {
    handleError(error, message);
  }
}

async function alternarSituacao(pontoId) {
  const message = document.getElementById("pontos-message");
  const ponto = pontos.find((item) => item.id === pontoId);
  if (!ponto) return;
  try {
    const resposta = await requestApi(`/api/pontos-coleta/${encodeURIComponent(pontoId)}/situacao`, {
      method: "POST",
      body: JSON.stringify({ ativo: ponto.ativo === false }),
    });
    const indice = pontos.findIndex((item) => item.id === pontoId);
    if (indice >= 0) pontos[indice] = resposta;
    meusPontos.add(resposta.id);
    const carga = await carregarPontos();
    if (carga.ok) {
      setMessage(message, resposta.ativo === false ? "Local desativado." : "Local ativado.", "success");
    }
  } catch (error) {
    handleError(error, message);
  }
}

async function excluirPonto(pontoId) {
  const message = document.getElementById("pontos-message");
  setMessage(message);
  try {
    await requestApi(`/api/pontos-coleta/${encodeURIComponent(pontoId)}`, { method: "DELETE" });
    let carga = await carregarPontos();
    if (carga.vazio && offsetAtual >= PAGE_SIZE) {
      offsetAtual = Math.max(0, offsetAtual - PAGE_SIZE);
      carga = await carregarPontos();
    }
    // carregarPontos() substitui a mensagem; o sucesso só aparece se a última carga funcionou.
    if (carga.ok) setMessage(message, "Local excluído.", "success");
  } catch (error) {
    handleError(error, message);
  }
}

async function initPontos() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);

  const denied = document.getElementById("pontos-acesso-negado");
  const gestao = document.getElementById("pontos-gestao");
  const admin = document.getElementById("ponto-admin");

  if (usuario.tipo !== "ponto_coleta") {
    if (denied) denied.hidden = false;
    setMessage(document.getElementById("pontos-message"), "Seu perfil não pode executar esta ação.", "error");
    return;
  }

  // A edição deve preservar todas as categorias aceitas pelo contrato.
  const filtroCategoria = document.getElementById("filtro-ponto-categoria");
  const categoriasForm = document.querySelector("#ponto-form select[name='categorias_aceitas']");
  filtroCategoria.replaceChildren(new Option("Todas", ""));
  categoriasForm.replaceChildren();
  for (const [valor, rotulo] of Object.entries(ROTULOS.categoria)) {
    filtroCategoria.append(new Option(rotulo, valor));
    categoriasForm.append(new Option(rotulo, valor));
  }
  if (gestao) gestao.hidden = false;
  if (admin) admin.hidden = false;

  document.getElementById("pontos-filtros").addEventListener("submit", (evento) => {
    evento.preventDefault();
    offsetAtual = 0;
    carregarPontos();
  });

  const form = document.getElementById("ponto-form");
  form.addEventListener("submit", comBotaoOcupado(
    form.querySelector("button[type='submit']"),
    salvarPonto,
  ));
  document.getElementById("ponto-cancel-edit").addEventListener("click", resetarFormularioPonto);

  document.getElementById("ponto-previous").addEventListener("click", () => {
    offsetAtual = Math.max(0, offsetAtual - PAGE_SIZE);
    carregarPontos();
  });
  document.getElementById("ponto-next").addEventListener("click", () => {
    offsetAtual += PAGE_SIZE;
    carregarPontos();
  });

  await carregarPontos();
}

document.addEventListener("DOMContentLoaded", initPontos);
