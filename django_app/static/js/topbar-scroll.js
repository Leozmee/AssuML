/**
 * Rétraction de la top bar au scroll — se compacte en scrollant vers le bas
 * (plus d'espace pour le contenu), se réétend en remontant vers le haut.
 */
(function () {
  const topbar = document.querySelector(".topbar");
  if (!topbar) return;

  const THRESHOLD = 40;  // px avant d'activer la rétraction
  const MIN_DELTA = 10;  // px minimum de mouvement avant de réagir (anti-tremblement)
  let lastScrollY = window.scrollY;
  let ticking = false;

  function onScroll() {
    // Borne la position dans les limites réelles de la page, pour ignorer
    // le rebond élastique (rubber-band) en haut/bas de page sur macOS.
    const maxScroll = Math.max(
      0,
      document.documentElement.scrollHeight - window.innerHeight
    );
    const currentY = Math.min(Math.max(0, window.scrollY), maxScroll);
    const delta = currentY - lastScrollY;

    if (currentY <= THRESHOLD) {
      topbar.classList.remove("is-compact");
      lastScrollY = currentY;
    } else if (delta > MIN_DELTA) {
      // Scroll vers le bas, mouvement significatif → compact
      topbar.classList.add("is-compact");
      lastScrollY = currentY;
    } else if (delta < -MIN_DELTA) {
      // Scroll vers le haut, mouvement significatif → pleine taille
      topbar.classList.remove("is-compact");
      lastScrollY = currentY;
    }
    // sinon : micro-mouvement, on ignore et on ne met pas à jour lastScrollY
    // (le delta continue de s'accumuler jusqu'à dépasser le seuil)

    ticking = false;
  }

  // { passive: true } : indique au navigateur que ce listener n'appelle
  // jamais preventDefault(), il peut donc scroller sans attendre le JS.
  window.addEventListener(
    "scroll",
    function () {
      if (!ticking) {
        window.requestAnimationFrame(onScroll);
        ticking = true;
      }
    },
    { passive: true }
  );
})();
