/**
 * Helpers Plotly.js pour AssuML.
 * Utilise Plotly depuis le CDN (chargé dans base.html).
 * Les couleurs sont lues en direct depuis les variables CSS (:root dans
 * assuml.css) plutôt que codées en dur ici, pour ne jamais désynchroniser
 * les graphiques du thème si celui-ci change.
 */

function cssVar(name, fallback) {
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
}

function assumlPlot(divId, jsonData, layout) {
  const data = typeof jsonData === "string" ? JSON.parse(jsonData) : jsonData;

  const primary = cssVar("--primary", "#2f6a9c");
  const ink = cssVar("--ink", "#1e3346");
  const muted = cssVar("--muted", "#516980");
  const line = cssVar("--line", "#eaf1f7");

  // Couleur des barres/lignes si non spécifié
  if (data && data.length > 0 && !data[0].marker) {
    data[0].marker = { color: primary };
  }

  const defaultLayout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor:  "rgba(0,0,0,0)",
    font: { family: "system-ui, sans-serif", color: ink, size: 12 },
    margin: { t: 20, l: 48, r: 12, b: 44 },
    xaxis: {
      gridcolor: line,
      linecolor: line,
      tickcolor: line,
      tickfont:  { color: muted },
    },
    yaxis: {
      gridcolor: line,
      linecolor: line,
      tickcolor: line,
      tickfont:  { color: muted },
    },
    ...layout,
  };
  Plotly.newPlot(divId, data, defaultLayout, { responsive: true, displayModeBar: false });
}
