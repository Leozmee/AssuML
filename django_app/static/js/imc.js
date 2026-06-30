/**
 * Calcul IMC temps réel à partir des inputs poids (kg) et taille (cm).
 * Écoute les événements keyup/change sur #id_poids et #id_taille.
 */
(function () {
  function calculerIMC() {
    const poids = parseFloat(document.getElementById("id_poids")?.value);
    const taille = parseFloat(document.getElementById("id_taille")?.value);
    const label = document.getElementById("imc-resultat");
    if (!label) return;

    if (!isNaN(poids) && !isNaN(taille) && taille > 0) {
      const imc = poids / Math.pow(taille / 100, 2);
      label.textContent = "IMC calculé : " + imc.toFixed(2);
      label.className = "fw-bold text-primary";
    } else {
      label.textContent = "IMC calculé : —";
      label.className = "text-muted";
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const poids = document.getElementById("id_poids");
    const taille = document.getElementById("id_taille");
    if (poids) { poids.addEventListener("keyup", calculerIMC); poids.addEventListener("change", calculerIMC); }
    if (taille) { taille.addEventListener("keyup", calculerIMC); taille.addEventListener("change", calculerIMC); }
    calculerIMC();
  });
})();
