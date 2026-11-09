import { ApiError, requestApi } from "./api.js";

export { ApiError, requestApi };

export const ROTULOS = {
  tipo: {
    pessoa: "Pessoa",
    ponto_coleta: "Ponto de coleta",
  },
  categoria: {
    informatica: "Informática",
    notebook: "Notebook",
    desktop: "Desktop",
    telefonia: "Telefonia",
    celular: "Celular",
    tablet: "Tablet",
    televisao: "Televisão",
    audio: "Áudio",
    eletrodomestico: "Eletrodoméstico",
    perifericos: "Periféricos",
    monitor: "Monitor",
    impressora: "Impressora",
    outro: "Outro",
  },
  condicao: {
    funcional: "Funcional",
    funcional_com_defeito: "Com defeito",
    reparavel: "Reparável",
    sem_conserto: "Sem conserto",
    recondicionado: "Recondicionado",
  },
  destino: {
    doacao: "Doação",
    descarte: "Descarte",
    revenda: "Revenda",
  },
  status: {
    disponivel: "Disponível",
    reservado: "Reservado",
    aguardando_ponto: "Aguardando ponto",
    entrega_prevista: "Entrega prevista",
    recebido: "Recebido",
    destinacao_informada: "Destinação informada",
    rascunho: "Rascunho",
    aguardando_confirmacao: "Aguardando confirmação",
    concluido: "Concluído",
    arquivado: "Arquivado",
  },
};

export function byId(id) {
  return document.getElementById(id);
}

const ROTULOS_INTERESSE = {
  pendente: "Pendente",
  selecionado: "Selecionado",
  recusado: "Recusado",
  cancelado: "Cancelado",
  encerrado: "Encerrado",
};

export function labelForInteresse(valor) {
  return ROTULOS_INTERESSE[valor] || valor || "Não informado";
}

export function labelFor(grupo, valor) {
  return ROTULOS[grupo]?.[valor] || valor || "Não informado";
}

export function setMessage(element, text = "", kind = "") {
  if (!element) return;
  element.textContent = text;
  element.className = kind ? `form-message ${kind}` : "form-message";
  if (kind === "error" && text) {
    // Foco acessível: erro anunciado e alcançável por teclado.
    element.setAttribute("tabindex", "-1");
    element.focus();
  }
}

export function setGlobalMessage(text = "", kind = "") {
  const element = byId("global-message");
  if (!element) return;
  element.textContent = text;
  element.className = kind ? `message ${kind}` : "message";
  element.hidden = !text;
}

export function handleError(error, target, { redirectOnUnauthorized = true } = {}) {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      if (!redirectOnUnauthorized) {
        setMessage(target, error.message, "error");
        return;
      }
      setGlobalMessage("Sua sessão terminou. Entre novamente para continuar.", "error");
      window.setTimeout(() => window.location.assign("./login.html"), 250);
      return;
    }
    if (error.status === 403) {
      setMessage(target, "Seu perfil não pode executar esta ação.", "error");
      return;
    }
    if (error.status === 404) {
      setMessage(target, "O recurso solicitado não foi encontrado.", "error");
      return;
    }
    setMessage(target, error.message, "error");
    return;
  }
  if (!(error instanceof ApiError)) {
    // Falha de rede: a operação pode ter sido aplicada; peça reconciliação.
    setMessage(
      target,
      "Não foi possível confirmar a operação. Recarregue a página para conferir o estado atual.",
      "error",
    );
    return;
  }
  setMessage(target, error.message || "Ocorreu um erro inesperado.", "error");
}

export function comBotaoOcupado(botao, acao) {
  // Bloqueia duplo envio enquanto a requisição está em andamento.
  return async (...argumentos) => {
    if (!botao || botao.dataset.ocupado === "1") return undefined;
    botao.dataset.ocupado = "1";
    botao.disabled = true;
    try {
      return await acao(...argumentos);
    } finally {
      delete botao.dataset.ocupado;
      botao.disabled = false;
    }
  };
}

export async function requestAllPages(path, filters = {}) {
  const records = [];
  let page;
  do {
    const params = new URLSearchParams({ ...filters, offset: String(records.length), limite: "100" });
    page = await requestApi(`${path}?${params.toString()}`);
    records.push(...page);
  } while (page.length === 100);
  return records;
}

export async function loadSession() {
  return requestApi("/api/usuarios/me");
}

export async function requireSession() {
  try {
    return await loadSession();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      window.location.assign("./login.html");
      return null;
    }
    setGlobalMessage(error.message || "Não foi possível verificar sua sessão agora.", "error");
    return null;
  }
}

const NAVEGACAO_AUTENTICADA = [
  { pagina: "catalogo.html", href: "./catalogo.html", texto: "Catálogo" },
  { pagina: "itens.html", href: "./itens.html", texto: "Meus itens", pessoa: true, id: "items-link" },
  { pagina: "interesses.html", href: "./interesses.html", texto: "Interesses", pessoa: true },
  { pagina: "onde-descartar.html", href: "./onde-descartar.html", texto: "Onde descartar" },
  { pagina: "pontos.html", href: "./pontos.html", texto: "Pontos" },
  { pagina: "notificacoes.html", href: "./notificacoes.html", texto: "Notificações" },
  { pagina: "perfil.html", href: "./perfil.html", texto: "Meu perfil" },
];

function renderAuthenticatedNavigation(usuario) {
  const navigation = document.querySelector(".header-actions");
  if (!navigation) return;
  // Todos os cabeçalhos usam a mesma ordem e as mesmas regras de visibilidade.
  navigation.querySelectorAll("a.nav-link").forEach((link) => link.remove());
  const links = document.createDocumentFragment();
  for (const entrada of NAVEGACAO_AUTENTICADA) {
    if (entrada.pessoa && usuario.tipo !== "pessoa") continue;
    const link = createElement("a", "nav-link", entrada.texto);
    link.href = entrada.href;
    if (entrada.id) link.id = entrada.id;
    if (window.location.pathname.endsWith(`/${entrada.pagina}`)) {
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
    }
    links.append(link);
  }
  navigation.insertBefore(links, byId("session-chip") || byId("logout-button"));
}

export function setupAuthenticatedHeader(usuario) {
  const sessionChip = byId("session-chip");
  const userName = byId("user-name");
  const roleBadge = byId("role-badge");
  const description = byId("role-description");

  if (sessionChip) {
    sessionChip.hidden = false;
    sessionChip.textContent = labelFor("tipo", usuario.tipo);
  }
  if (userName) userName.textContent = usuario.nome;
  if (roleBadge) roleBadge.textContent = labelFor("tipo", usuario.tipo);
  if (description) description.textContent = roleDescription(usuario.tipo);
  renderAuthenticatedNavigation(usuario);

  const logoutButton = byId("logout-button");
  if (logoutButton) logoutButton.hidden = false;
  if (logoutButton && !logoutButton.dataset.bound) {
    logoutButton.dataset.bound = "true";
    logoutButton.addEventListener("click", async () => {
      logoutButton.disabled = true;
      try {
        await requestApi("/api/auth/logout", { method: "POST" });
        window.location.assign("./index.html");
      } catch (error) {
        logoutButton.disabled = false;
        handleError(error, byId("global-message"));
      }
    });
  }
}

export function getFormData(form) {
  return new FormData(form);
}

export function addressFromForm(data) {
  return {
    logradouro: String(data.get("logradouro") || "").trim(),
    numero: String(data.get("numero") || "").trim(),
    complemento: String(data.get("complemento") || "").trim() || null,
    cep: String(data.get("cep") || "").trim(),
    cidade: String(data.get("cidade") || "").trim(),
  };
}

export function userPayloadFromForm(form) {
  const data = getFormData(form);
  return {
    nome: String(data.get("nome") || "").trim(),
    email: String(data.get("email") || "").trim(),
    senha: String(data.get("senha") || ""),
    tipo: "pessoa",
    endereco: addressFromForm(data),
  };
}

export function profilePayloadFromForm(form) {
  const data = getFormData(form);
  return {
    nome: String(data.get("nome") || "").trim(),
    email: String(data.get("email") || "").trim(),
    endereco: addressFromForm(data),
  };
}

export function itemPayloadFromForm(form) {
  const data = getFormData(form);
  const destino = String(data.get("destino") || "doacao");
  const valorTexto = String(data.get("valor") || "").trim();
  return {
    titulo: String(data.get("titulo") || "").trim(),
    descricao: String(data.get("descricao") || "").trim(),
    categoria: String(data.get("categoria") || ""),
    marca: String(data.get("marca") || "").trim(),
    modelo: String(data.get("modelo") || "").trim(),
    condicao: String(data.get("condicao") || ""),
    destino,
    valor: destino === "revenda" && valorTexto !== "" ? Number(valorTexto) : null,
  };
}

export function fillAddress(form, camposEndereco) {
  form.elements.logradouro.value = camposEndereco?.logradouro || "";
  form.elements.numero.value = camposEndereco?.numero || "";
  form.elements.complemento.value = camposEndereco?.complemento || "";
  form.elements.cep.value = camposEndereco?.cep || "";
  form.elements.cidade.value = camposEndereco?.cidade || "";
}

export function fillProfileForm(form, usuario) {
  form.elements.nome.value = usuario.nome || "";
  form.elements.email.value = usuario.email || "";
  fillAddress(form, usuario.endereco);
}

export function roleDescription(tipo) {
  if (tipo === "pessoa") {
    return "Ofereça eletrônicos ou encontre itens para reaproveitar, com a mesma conta.";
  }
  if (tipo === "ponto_coleta") {
    return "Gerencie seus pontos de coleta e acompanhe as entregas previstas e recebidas.";
  }
  return "Explore o catálogo e encontre eletrônicos para reaproveitar.";
}

export function createElement(tag, className = "", text = "") {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== "") element.textContent = text;
  return element;
}

export function createItemCard(item, { owned = false, onEdit = null, onDelete = null } = {}) {
  const article = createElement("article", "item-card");
  const tags = createElement("div", "item-tags");
  tags.append(
    createElement("span", item.destino === "descarte" ? "tag tag-warm" : "tag", labelFor("destino", item.destino)),
    createElement("span", "tag tag-neutral", labelFor("status", item.status)),
  );

  const title = createElement("h3", "", item.titulo);
  const description = createElement("p", "item-card-description", item.descricao);
  const meta = createElement("div", "item-meta");
  const valor = item.valor === null || item.valor === undefined
    ? "Sem preço"
    : `R$ ${Number(item.valor).toFixed(2)}`;
  meta.append(
    createElement("span", "", labelFor("categoria", item.categoria)),
    createElement("span", "", labelFor("condicao", item.condicao)),
    createElement("span", "", valor),
  );
  const city = createElement("small", "", `Proprietário em ${item.cidade_proprietario || "cidade não informada"}`);
  article.append(tags, title, description, meta, city);

  if (owned) {
    const actions = createElement("div", "item-actions");
    const edit = createElement("button", "button button-secondary", "Editar");
    edit.type = "button";
    edit.dataset.itemId = item.id;
    edit.addEventListener("click", () => onEdit?.(item.id));
    const remove = createElement("button", "button button-ghost", "Excluir");
    remove.type = "button";
    remove.dataset.itemId = item.id;
    remove.addEventListener("click", () => onDelete?.(item.id));
    actions.append(edit, remove);
    article.append(actions);
  }
  return article;
}

export function renderEmptyState(list, title, description) {
  const empty = createElement("div", "empty-state");
  empty.append(
    createElement("strong", "", title),
    createElement("span", "", description),
  );
  list.append(empty);
}
