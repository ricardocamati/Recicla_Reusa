import {
  handleError,
  setMessage,
  userPayloadFromForm,
  requestApi,
} from "./comum.js";

async function register(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("register-message");
  setMessage(message);
  try {
    await requestApi("/api/usuarios", {
      method: "POST",
      body: JSON.stringify(userPayloadFromForm(form)),
    });
    form.reset();
    setMessage(message, "Conta criada. Faça login para acessar o catálogo.", "success");
    document.getElementById("login-link").focus();
  } catch (error) {
    handleError(error, message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("register-form").addEventListener("submit", register);
});
