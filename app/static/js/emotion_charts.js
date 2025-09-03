/* Build Emotion Lens charts using Chart.js and a CSS heatmap grid. */
(function () {
  const d = window.__EMOTION_DATA__ || { daily: [], heatDays: [], heatValues: [], distCounts: {}, keyOrder: [] };

  // Trend (last 7 points)
  const ctxTrend = document.getElementById("trendChart");
  if (ctxTrend) {
    const last7 = d.daily.slice(-7);
    const labels = last7.map(x => x.date);
    const values = last7.map(x => x.score || 0);
    new Chart(ctxTrend, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Primary emotion score",
          data: values,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        scales: { y: { min: 0, max: 1 } }
      }
    });
  }

  // Distribution (donut)
  const ctxDist = document.getElementById("distChart");
  if (ctxDist) {
    const labels = Object.keys(d.distCounts);
    const values = labels.map(k => d.distCounts[k]);
    new Chart(ctxDist, {
      type: "doughnut",
      data: { labels, datasets: [{ data: values }] },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });
  }

  // Heatmap (simple CSS grid)
  const grid = document.getElementById("heatmap");
  if (grid) {
    grid.innerHTML = "";
    // Header row: days
    const header = document.createElement("div");
    header.className = "heatmap-row";
    header.appendChild(document.createElement("div")); // empty corner
    d.heatDays.forEach(day => {
      const cell = document.createElement("div");
      cell.className = "heatmap-cell heatmap-header";
      cell.textContent = day.slice(5); // MM-DD
      header.appendChild(cell);
    });
    grid.appendChild(header);

    // Rows per emotion key
    d.keyOrder.forEach((key, idx) => {
      const row = document.createElement("div");
      row.className = "heatmap-row";
      const labelCell = document.createElement("div");
      labelCell.className = "heatmap-cell heatmap-label";
      labelCell.textContent = key;
      row.appendChild(labelCell);
      d.heatValues.forEach(dayArr => {
        const v = dayArr[idx] || 0;
        const cell = document.createElement("div");
        cell.className = "heatmap-cell";
        cell.style.opacity = Math.min(1, v + 0.1);
        cell.title = key + ": " + v;
        row.appendChild(cell);
      });
      grid.appendChild(row);
    });
  }
})();
