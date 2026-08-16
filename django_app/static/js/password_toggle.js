/**
 * Ajoute une icône œil à l'intérieur de chaque champ mot de passe pour en
 * afficher/masquer le contenu — login, inscription, création admin,
 * création client. Générique : s'applique automatiquement à tout
 * input[type="password"] présent sur la page.
 */
document.addEventListener("DOMContentLoaded", () => {
  const EYE_OPEN =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"></path>' +
    '<circle cx="12" cy="12" r="3"></circle></svg>';

  const EYE_CLOSED =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"></path>' +
    '<circle cx="12" cy="12" r="3"></circle>' +
    '<line x1="2" y1="2" x2="22" y2="22"></line></svg>';

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrapper = document.createElement("div");
    wrapper.className = "password-field";
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "password-toggle-icon";
    toggle.innerHTML = EYE_OPEN;
    toggle.setAttribute("aria-label", "Afficher le mot de passe");
    wrapper.appendChild(toggle);

    toggle.addEventListener("click", () => {
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      toggle.innerHTML = showing ? EYE_OPEN : EYE_CLOSED;
      toggle.setAttribute(
        "aria-label",
        showing ? "Afficher le mot de passe" : "Masquer le mot de passe"
      );
    });
  });
});
