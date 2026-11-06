import {
  fillProfileForm,
  handleError,
  labelFor,
  profilePayloadFromForm,
  roleDescription,
  requestApi,
  requireSession,
  setMessage,
  setupAuthenticatedHeader,
} from "./comum.js";

let usuario;

function renderProfile() {
  setupAuthenticatedHeader(usuario);
  fillProfileForm(document.getElementById("profile-form"), usuario);
  document.getElementById("role-description").textContent = roleDescription(usuario.tipo);
  document.getElementById("account-role").textContent = labelFor("tipo", usuario.tipo);
  document.getElementById("account-city").textContent = usuario.endereco?.cidade || "Não informada";
  document.getElementById("account-tip").textContent = usuario.tipo === "ponto_coleta"
    ? "Gerencie seus pontos de coleta e confirme o recebimento dos equipamentos entregues."
    : "Com a mesma conta, você pode oferecer eletrônicos, demonstrar interesse e acompanhar suas entregas.";
}

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
    renderProfile();
    setMessage(message, "Perfil atualizado com sucesso.", "success");
  } catch (error) {
    handleError(error, message);
  }
}

async function initProfile() {
  usuario = await requireSession();
  if (!usuario) return;
  renderProfile();
  document.getElementById("profile-form").addEventListener("submit", updateProfile);
}

document.addEventListener("DOMContentLoaded", initProfile);
