(function () {
  const metrics = [
    { key: "regular_usd_per_gallon", label: "Regular", short: "Regular" },
    { key: "midgrade_usd_per_gallon", label: "Mid-grade", short: "Mid-grade" },
    { key: "premium_usd_per_gallon", label: "Premium", short: "Premium" },
    { key: "diesel_usd_per_gallon", label: "Diesel", short: "Diesel" }
  ];
  const dataBase = location.pathname.includes("/site/") ? "../data/" : "data/";

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>\"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[character]));
  }

  function parseCSV(text) {
    const rows = [];
    let row = [], cell = "", quoted = false;
    for (let i = 0; i < text.length; i += 1) {
      const char = text[i], next = text[i + 1];
      if (char === '"' && quoted && next === '"') { cell += '"'; i += 1; }
      else if (char === '"') quoted = !quoted;
      else if (char === "," && !quoted) { row.push(cell); cell = ""; }
      else if ((char === "\n" || char === "\r") && !quoted) {
        if (char === "\r" && next === "\n") i += 1;
        row.push(cell); cell = "";
        if (row.some((value) => value !== "")) rows.push(row);
        row = [];
      } else cell += char;
    }
    if (cell || row.length) { row.push(cell); rows.push(row); }
    const headers = rows.shift() || [];
    return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
  }

  async function loadData() {
    const [statusResponse, historyResponse] = await Promise.all([
      fetch(`${dataBase}status.json`, { cache: "no-store" }),
      fetch(`${dataBase}history.csv`, { cache: "no-store" })
    ]);
    if (!statusResponse.ok || !historyResponse.ok) throw new Error("The latest tracker data is not available yet.");
    return { status: await statusResponse.json(), history: parseCSV(await historyResponse.text()) };
  }

  function number(value) {
    const result = Number(value);
    return Number.isFinite(result) ? result : null;
  }

  function dates(history) { return [...new Set(history.map((row) => row.date))].sort(); }
  function latestDate(history) { return dates(history).at(-1) || null; }
  function priorDate(history, day) { return dates(history).filter((date) => date < day).at(-1) || null; }
  function rowsOn(history, day) { return history.filter((row) => row.date === day); }
  function latestRows(history) { const day = latestDate(history); return rowsOn(history, day); }
  function byId(rows) { return Object.fromEntries(rows.map((row) => [row.item_id, row])); }
  function fuel(value) { return value === "" || value == null ? "—" : `$${Number(value).toFixed(4)}`; }
  function pct(value) { return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`; }
  function metricLabel(key) { return metrics.find((metric) => metric.key === key)?.label || key; }

  function moves(previous, current) {
    const old = byId(previous);
    return current.map((row) => {
      const before = old[row.item_id];
      if (!before) return null;
      const changes = metrics.map((metric) => {
        const oldValue = number(before[metric.key]), newValue = number(row[metric.key]);
        if (oldValue == null || newValue == null) return null;
        const difference = newValue - oldValue;
        const score = oldValue ? Math.abs(difference / oldValue) * 100 : Math.abs(difference);
        return { ...metric, oldValue, newValue, difference, score };
      }).filter(Boolean);
      if (!changes.length) return null;
      const biggest = changes.sort((a, b) => b.score - a.score || a.key.localeCompare(b.key))[0];
      return { ...row, ...biggest };
    }).filter(Boolean).sort((a, b) => b.score - a.score || a.item_id.localeCompare(b.item_id));
  }

  function renderNav(active) {
    const target = document.querySelector("#nav");
    if (!target) return;
    target.innerHTML = `<div class="nav"><a class="brand" href="index.html"><span class="brand-mark">$</span>American Gas Tracker</a><nav class="nav-links" aria-label="Main navigation"><a class="${active === "today" ? "active" : ""}" href="index.html">Today</a><a class="${active === "browse" ? "active" : ""}" href="browse.html">Browse</a><a class="${active === "trends" ? "active" : ""}" href="trends.html">Trends</a></nav></div>`;
  }

  function showError(error) {
    const target = document.querySelector("#app");
    if (target) target.innerHTML = `<div class="card"><h2>Data unavailable</h2><p class="lede">${escapeHtml(error.message || error)}</p></div>`;
  }

  function drawLineChart(container, series, options = {}) {
    if (!container) return;
    const width = 820, height = 270, left = 54, right = 20, top = 20, bottom = 38;
    const allValues = series.flatMap((item) => item.values.map((value) => value).filter((value) => value != null));
    if (!allValues.length) { container.innerHTML = `<div class="empty">Not enough values to chart yet.</div>`; return; }
    const min = Math.min(...allValues), max = Math.max(...allValues), spread = max - min || 1;
    const labels = series[0].labels || [];
    const x = (index) => left + (labels.length <= 1 ? 0 : index * (width - left - right) / (labels.length - 1));
    const y = (value) => top + (max - value) * (height - top - bottom) / spread;
    const colors = ["#58d6b0", "#70a7ff", "#f3bd68", "#ff7f8d", "#c99cff", "#83e3ee"];
    const grid = [0, .25, .5, .75, 1].map((fraction) => {
      const value = max - spread * fraction, yy = top + fraction * (height - top - bottom);
      return `<line x1="${left}" x2="${width - right}" y1="${yy}" y2="${yy}" stroke="#2b3f59"/><text x="${left - 8}" y="${yy + 4}" text-anchor="end">${value.toFixed(2)}</text>`;
    }).join("");
    const lines = series.map((item, seriesIndex) => {
      const points = item.values.map((value, index) => value == null ? null : `${x(index)},${y(value)}`).filter(Boolean).join(" ");
      return `<polyline fill="none" stroke="${colors[seriesIndex % colors.length]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${points}"/><text x="${width - right}" y="${top + 15 + seriesIndex * 16}" text-anchor="end" fill="${colors[seriesIndex % colors.length]}">${escapeHtml(item.label)}</text>`;
    }).join("");
    const xLabels = labels.filter((_, index) => index === 0 || index === labels.length - 1 || index === Math.floor(labels.length / 2)).map((label) => {
      const index = labels.indexOf(label);
      return `<text x="${x(index)}" y="${height - 10}" text-anchor="middle">${escapeHtml(label)}</text>`;
    }).join("");
    container.innerHTML = `<svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(options.label || "Trend chart")}">${grid}${lines}${xLabels}</svg>`;
  }

  window.Tracker = { metrics, escapeHtml, loadData, number, dates, latestDate, priorDate, rowsOn, latestRows, byId, fuel, pct, metricLabel, moves, renderNav, showError, drawLineChart };
  if ("serviceWorker" in navigator) navigator.serviceWorker.register(`${dataBase}../sw.js`.replace("data/../", ""), { scope: dataBase.replace("data/", "") || "./" }).catch(() => {});
}());

