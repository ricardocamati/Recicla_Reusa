import {
  ApiError, ROTULOS, byId, createElement, labelFor, loadSession, requestApi,
  setMessage, setupAuthenticatedHeader,
} from "./comum.js";

const PAGE_SIZE = 20;
let consulta;
let carregando = false;

function lerConsulta() {
  const p = new URLSearchParams(window.location.search);
  const offset = Number(p.get("offset") || 0);
  return {
    cidade: (p.get("cidade") || "").trim().slice(0, 160),
    categoria: Object.hasOwn(ROTULOS.categoria, p.get("categoria")) ? p.get("categoria") : "",
    offset: Number.isSafeInteger(offset) && offset >= 0 && offset <= Number.MAX_SAFE_INTEGER - PAGE_SIZE ? offset : 0,
    local: p.get("local") || "",
  };
}

function urlConsulta(alteracoes = {}) {
  const dados = { ...consulta, ...alteracoes };
  const p = new URLSearchParams();
  for (const chave of ["cidade", "categoria", "offset", "local"]) {
    if (dados[chave]) p.set(chave, String(dados[chave]));
  }
  const versao = new URLSearchParams(window.location.search).get("v");
  if (versao) p.set("v", versao);
  return `${window.location.pathname}${p.size ? `?${p}` : ""}`;
}

function navegar(alteracoes) {
  window.location.assign(urlConsulta(alteracoes));
}

function enderecoPublico(ponto) {
  const e = ponto.endereco || {};
  return [e.logradouro, e.numero, e.complemento, e.cidade, e.cep ? `CEP ${e.cep}` : ""].filter(Boolean).join(", ");
}

function informacoes(ponto) {
  const card = createElement("article", "item-card");
  card.append(
    createElement("h3", "", ponto.nome),
    createElement("p", "directory-address", enderecoPublico(ponto)),
    createElement("p", "", `Categorias: ${(ponto.categorias_aceitas || []).map(c => labelFor("categoria", c)).join(", ")}`),
    createElement("p", "", ponto.horario_atendimento?.trim() || "Horário não informado pelo local."),
  );
  return card;
}

async function copiarEndereco(botao, endereco, feedback) {
  botao.disabled = true;
  try {
    if (!navigator.clipboard?.writeText) throw new Error("Cópia indisponível");
    await navigator.clipboard.writeText(endereco.textContent);
    setMessage(feedback, "Endereço copiado.", "success");
  } catch {
    setMessage(feedback, "Cópia indisponível. Selecione o endereço e copie manualmente.");
    endereco.focus();
    const selecao = window.getSelection();
    const intervalo = document.createRange();
    intervalo.selectNodeContents(endereco);
    selecao?.removeAllRanges();
    selecao?.addRange(intervalo);
  } finally {
    botao.disabled = false;
  }
}

function mostrarDetalhe(ponto) {
  const card = informacoes(ponto);
  const endereco = card.querySelector(".directory-address");
  endereco.tabIndex = 0;
  const copiar = createElement("button", "button button-secondary", "Copiar endereço");
  copiar.type = "button";
  copiar.id = "directory-copy";
  const feedback = createElement("p", "form-message");
  feedback.id = "directory-copy-message";
  feedback.setAttribute("role", "status");
  feedback.setAttribute("aria-live", "polite");
  copiar.addEventListener("click", () => copiarEndereco(copiar, endereco, feedback));
  card.append(copiar, feedback);
  byId("directory-detail").append(card);
  byId("directory-title").textContent = "Detalhes do local";
  byId("directory-title").focus();
}

async function carregar() {
  if (carregando) return;
  carregando = true;
  const lista = byId("directory-list");
  lista.replaceChildren();
  const detalhe = byId("directory-detail");
  detalhe.replaceChildren();
  detalhe.hidden = !consulta.local;
  lista.hidden = Boolean(consulta.local);
  if (consulta.local) {
    const voltar = createElement("a", "button button-ghost", "Voltar aos locais");
    voltar.id = "directory-back";
    voltar.href = urlConsulta({ local: "" });
    detalhe.append(voltar);
  }
  lista.setAttribute("aria-busy", "true");
  byId("directory-pagination").hidden = true;
  byId("directory-retry").hidden = true;
  setMessage(byId("directory-message"), "Carregando locais...");
  try {
    if (consulta.local) {
      mostrarDetalhe(await requestApi(`/api/pontos-coleta/${encodeURIComponent(consulta.local)}`));
      setMessage(byId("directory-message"));
      return;
    }
    const p = new URLSearchParams({ offset: String(consulta.offset), limite: String(PAGE_SIZE + 1) });
    if (consulta.cidade) p.set("cidade", consulta.cidade);
    if (consulta.categoria) p.set("categoria", consulta.categoria);
    const pontos = await requestApi(`/api/pontos-coleta?${p}`);
    byId("directory-pagination").hidden = false;
    byId("directory-previous").disabled = consulta.offset === 0;
    byId("directory-next").disabled = pontos.length <= PAGE_SIZE;
    byId("directory-page").textContent = `Página ${Math.floor(consulta.offset / PAGE_SIZE) + 1}`;
    for (const ponto of pontos.slice(0, PAGE_SIZE)) {
      const card = informacoes(ponto);
      const link = createElement("a", "button button-secondary directory-detail-link", "Ver detalhes");
      link.href = urlConsulta({ local: ponto.id });
      link.setAttribute("aria-label", `Ver detalhes de ${ponto.nome}`);
      card.append(link);
      lista.append(card);
    }
    setMessage(byId("directory-message"), pontos.length ? "Locais desta página." : "Nenhum local encontrado para estes filtros. Tente outra cidade ou categoria.");
  } catch (error) {
    const mensagem = consulta.local && error instanceof ApiError && error.status === 404
      ? "Este local não está disponível. Volte aos locais para escolher outro ou altere os filtros."
      : "Não foi possível consultar os locais. Tente novamente ou altere os filtros.";
    setMessage(byId("directory-message"), mensagem, "error");
    byId("directory-retry").hidden = false;
  } finally {
    lista.setAttribute("aria-busy", "false");
    carregando = false;
  }
}

async function cabecalhoOpcional() {
  try {
    const usuario = await loadSession();
    document.querySelectorAll(".directory-guest").forEach(e => e.remove());
    setupAuthenticatedHeader(usuario);
  } catch {
    // Não ter sessão (ou não conseguir verificá-la) nunca bloqueia a consulta.
  }
}

document.addEventListener("DOMContentLoaded", () => {
  consulta = lerConsulta();
  window.history.replaceState(null, "", urlConsulta());
  for (const [valor, rotulo] of Object.entries(ROTULOS.categoria)) {
    const option = createElement("option", "", rotulo);option.value = valor;
    byId("directory-category").append(option);
  }
  byId("directory-city").value = consulta.cidade;
  byId("directory-category").value = consulta.categoria;
  byId("directory-filters").addEventListener("submit", evento => {
    evento.preventDefault();
    navegar({ cidade: byId("directory-city").value.trim(), categoria: byId("directory-category").value, offset: 0, local: "" });
  });
  byId("directory-clear").addEventListener("click", () => navegar({ cidade: "", categoria: "", offset: 0, local: "" }));
  byId("directory-previous").addEventListener("click", () => navegar({ offset: Math.max(0, consulta.offset - PAGE_SIZE) }));
  byId("directory-next").addEventListener("click", () => navegar({ offset: consulta.offset + PAGE_SIZE }));
  byId("directory-retry").addEventListener("click", carregar);
  cabecalhoOpcional();
  carregar();
});
