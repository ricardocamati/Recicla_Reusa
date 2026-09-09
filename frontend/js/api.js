const API_BASE = window.RECICLA_API_BASE || "http://127.0.0.1:8000";

function formatErrorDetail(payload) {
  if (!payload || payload.detail === undefined) {
    return "Não foi possível concluir a operação.";
  }
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => item.msg || "Dados inválidos")
      .join(" ");
  }
  return String(payload.detail);
}

export class ApiError extends Error {
  constructor(status, payload) {
    super(formatErrorDetail(payload));
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export async function requestApi(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body !== undefined && options.body !== null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const config = {
    ...options,
    credentials: "include",
    headers,
  };

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, config);
  } catch (error) {
    throw new Error("Não foi possível conectar à API. Verifique se o backend está em execução.");
  }

  let payload = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = await response.json();
  }

  if (!response.ok) {
    throw new ApiError(response.status, payload);
  }
  return payload;
}
