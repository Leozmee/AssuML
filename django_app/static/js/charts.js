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

  const primary = cssVar("--primary", "#3a80b8");
  const ink = cssVar("--ink", "#1e3346");
  const muted = cssVar("--muted", "#93a8bb");
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

function assumlGauge(divId, value, min, max, title) {
  const primaryDark = cssVar("--primary-dark", "#1e3a5f");
  const muted = cssVar("--muted", "#93a8bb");
  const ink = cssVar("--ink", "#1e3346");
  const line = cssVar("--line", "#eaf1f7");
  const successBg = cssVar("--success-bg", "#e3f8ea");
  const warningBg = cssVar("--warning-bg", "#fef1dc");
  const dangerBg = cssVar("--danger-bg", "#fde4e4");

  const data = [
    {
      type: "indicator",
      mode: "gauge+number",
      value: value,
      title: { text: title, font: { size: 13, color: muted } },
      number: { font: { color: ink } },
      gauge: {
        axis: { range: [min, max], tickcolor: muted },
        bar: { color: primaryDark },
        bgcolor: "rgba(0,0,0,0)",
        bordercolor: line,
        steps: [
          { range: [min, min + (max - min) * 0.33], color: successBg },
          { range: [min + (max - min) * 0.33, min + (max - min) * 0.66], color: warningBg },
          { range: [min + (max - min) * 0.66, max], color: dangerBg },
        ],
      },
    },
  ];
  Plotly.newPlot(
    divId, data,
    {
      margin: { t: 60, l: 20, r: 20, b: 20 },
      paper_bgcolor: "rgba(0,0,0,0)",
      font: { color: muted },
    },
    { responsive: true, displayModeBar: false }
  );
}
