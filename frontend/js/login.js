import {
  handleError,
  requestApi,
  setMessage,
} from "./comum.js";

async function login(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("login-message");
  setMessage(message);
  try {
    await requestApi("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: String(form.elements.email.value).trim(),
        senha: form.elements.senha.value,
      }),
    });
    setMessage(message, "Login realizado. Redirecionando...", "success");
    window.location.assign("./perfil.html");
  } catch (error) {
    handleError(error, message, { redirectOnUnauthorized: false });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("login-form").addEventListener("submit", login);
});
