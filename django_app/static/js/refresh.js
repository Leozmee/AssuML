/**
 * Auto-refresh pour la page monitoring.
 * Fait un fetch vers REFRESH_URL toutes les REFRESH_INTERVAL ms
 * et met à jour les éléments [data-refresh-key].
 */
(function () {
  const REFRESH_INTERVAL = 10000;

  function refreshMonitoring() {
    const url = document.body.dataset.refreshUrl;
    if (!url) return;

    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then((r) => r.json())
      .then((data) => {
        document.querySelectorAll("[data-refresh-key]").forEach((el) => {
          const key = el.dataset.refreshKey;
          if (data[key] !== undefined) {
            el.textContent = data[key];
          }
        });
      })
      .catch(() => {});
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (document.body.dataset.refreshUrl) {
      setInterval(refreshMonitoring, REFRESH_INTERVAL);
    }
  });
})();
