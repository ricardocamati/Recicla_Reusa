import { loadSession, labelFor } from "./comum.js";

async function initHome() {
  const authenticatedLinks = document.getElementById("authenticated-links");
  const greeting = document.getElementById("home-greeting");
  try {
    const usuario = await loadSession();
    authenticatedLinks.hidden = false;
    greeting.textContent = `Você está conectado como ${labelFor("tipo", usuario.tipo)}.`;
  } catch (error) {
    authenticatedLinks.hidden = true;
  }
}

document.addEventListener("DOMContentLoaded", initHome);
