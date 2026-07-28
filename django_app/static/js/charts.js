/**
 * Helpers Plotly.js pour AssuML — dark theme.
 * Utilise Plotly depuis le CDN (chargé dans base.html).
 */

function assumlPlot(divId, jsonData, layout) {
  const data = typeof jsonData === "string" ? JSON.parse(jsonData) : jsonData;

  // Couleur des barres/lignes si non spécifié
  if (data && data.length > 0 && !data[0].marker) {
    data[0].marker = { color: "#5b87ad" };
  }

  const defaultLayout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor:  "rgba(0,0,0,0)",
    font: { family: "system-ui, sans-serif", color: "#94a3b8", size: 12 },
    margin: { t: 20, l: 48, r: 12, b: 44 },
    xaxis: {
      gridcolor: "rgba(255,255,255,0.05)",
      linecolor: "rgba(255,255,255,0.07)",
      tickcolor: "rgba(255,255,255,0.07)",
      tickfont:  { color: "#64748b" },
    },
    yaxis: {
      gridcolor: "rgba(255,255,255,0.05)",
      linecolor: "rgba(255,255,255,0.07)",
      tickcolor: "rgba(255,255,255,0.07)",
      tickfont:  { color: "#64748b" },
    },
    ...layout,
  };
  Plotly.newPlot(divId, data, defaultLayout, { responsive: true, displayModeBar: false });
}

function assumlGauge(divId, value, min, max, title) {
  const data = [
    {
      type: "indicator",
      mode: "gauge+number",
      value: value,
      title: { text: title, font: { size: 13, color: "#94a3b8" } },
      number: { font: { color: "#e2e8f0" } },
      gauge: {
        axis: { range: [min, max], tickcolor: "#64748b" },
        bar: { color: "#3a5a78" },
        bgcolor: "rgba(0,0,0,0)",
        bordercolor: "rgba(255,255,255,0.07)",
        steps: [
          { range: [min, min + (max - min) * 0.33], color: "rgba(34,197,94,0.2)" },
          { range: [min + (max - min) * 0.33, min + (max - min) * 0.66], color: "rgba(245,158,11,0.2)" },
          { range: [min + (max - min) * 0.66, max], color: "rgba(239,68,68,0.2)" },
        ],
      },
    },
  ];
  Plotly.newPlot(
    divId, data,
    {
      margin: { t: 60, l: 20, r: 20, b: 20 },
      paper_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#94a3b8" },
    },
    { responsive: true, displayModeBar: false }
  );
}
