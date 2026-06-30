/**
 * Helpers Plotly.js pour AssuML.
 * Utilise Plotly depuis le CDN (chargé dans base.html).
 */

function assumlPlot(divId, jsonData, layout) {
  const data = typeof jsonData === "string" ? JSON.parse(jsonData) : jsonData;
  const defaultLayout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "Inter, sans-serif", color: "#374151" },
    margin: { t: 40, l: 50, r: 20, b: 50 },
    ...layout,
  };
  Plotly.newPlot(divId, data, defaultLayout, { responsive: true, displayModeBar: false });
}

function assumlGauge(divId, value, min, max, title, colorScale) {
  const data = [
    {
      type: "indicator",
      mode: "gauge+number",
      value: value,
      title: { text: title, font: { size: 14 } },
      gauge: {
        axis: { range: [min, max] },
        bar: { color: "#3b82f6" },
        bgcolor: "white",
        steps: colorScale || [
          { range: [min, min + (max - min) * 0.33], color: "#bbf7d0" },
          { range: [min + (max - min) * 0.33, min + (max - min) * 0.66], color: "#fef08a" },
          { range: [min + (max - min) * 0.66, max], color: "#fecaca" },
        ],
      },
    },
  ];
  Plotly.newPlot(divId, data, { margin: { t: 60, l: 20, r: 20, b: 20 }, paper_bgcolor: "rgba(0,0,0,0)" }, { responsive: true, displayModeBar: false });
}
