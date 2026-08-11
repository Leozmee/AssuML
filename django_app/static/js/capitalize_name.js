/**
 * Met en majuscule la première lettre des champs nom/prénom en direct,
 * pendant la saisie — présent sur l'inscription, la création et la
 * modification de client. La normalisation finale reste aussi faite
 * côté serveur (voir capitaliser_nom() côté Django) en filet de sécurité.
 */
document.addEventListener("input", (event) => {
  const el = event.target;
  if (!el.matches('input[name="nom"], input[name="prenom"]')) return;
  if (!el.value) return;

  const capitalized = el.value.charAt(0).toUpperCase() + el.value.slice(1);
  if (capitalized === el.value) return;

  const pos = el.selectionStart;
  el.value = capitalized;
  el.setSelectionRange(pos, pos);
});
