import {
  fillProfileForm,
  handleError,
  profilePayloadFromForm,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;

async function updateProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("profile-message");
  setMessage(message);
  try {
    usuario = await requestApi(`/api/usuarios/${usuario.id}`, {
      method: "PUT",
      body: JSON.stringify(profilePayloadFromForm(form)),
    });
    setupAuthenticatedHeader(usuario);
    fillProfileForm(form, usuario);
    setMessage(message, "Perfil atualizado com sucesso.", "success");
  } catch (error) {
    handleError(error, message);
  }
}

async function initProfile() {
  usuario = await requireSession();
  if (!usuario) return;
  setupAuthenticatedHeader(usuario);
  fillProfileForm(document.getElementById("profile-form"), usuario);
  document.getElementById("profile-form").addEventListener("submit", updateProfile);
}

document.addEventListener("DOMContentLoaded", initProfile);
