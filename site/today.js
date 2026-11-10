(function () {
  const T = window.Tracker;
  T.renderNav("today");

  function changeCell(row, previous) {
    const old = previous?.[row.item_id];
    if (!old) return `<span class="flat">New</span>`;
    const oldValue = T.number(old.regular_usd_per_gallon), newValue = T.number(row.regular_usd_per_gallon);
    if (oldValue == null || newValue == null) return "—";
    const difference = newValue - oldValue;
    const className = difference > 0 ? "up" : difference < 0 ? "down" : "flat";
    return `<span class="${className}">${difference >= 0 ? "+" : ""}${difference.toFixed(4)}</span><span class="subline">${T.pct(oldValue ? difference / oldValue * 100 : 0)}</span>`;
  }

  function render(data) {
    const { status, history } = data;
    const day = T.latestDate(history), previousDay = T.priorDate(history, day || "9999-99-99");
    const latest = T.latestRows(history), previous = T.byId(T.rowsOn(history, previousDay));
    const biggest = T.moves(T.rowsOn(history, previousDay), latest);
    document.querySelector("#run-stamp").innerHTML = `<span class="metric-label">Last successful snapshot</span><strong>${T.escapeHtml(status.run_time || "Not run yet")}</strong>`;
    document.querySelector("#metrics").innerHTML = [
      ["Items today", status.items], ["Successful days", status.days_with_success], ["New today", status.new_today.length], ["Gone today", status.gone_today.length]
    ].map(([label, value]) => `<div class="card"><div class="metric-label">${label}</div><div class="metric-value">${value}</div></div>`).join("");
    document.querySelector("#sources").innerHTML = (status.sources || []).map((source) => `<div class="source-row"><span>${T.escapeHtml(source.name)}</span><span class="${source.ok ? "ok" : "failed"}">${source.ok ? "OK" : "Failed"} · ${source.count} items</span></div>`).join("") || `<div class="empty">No source result yet.</div>`;
    document.querySelector("#biggest").innerHTML = biggest.slice(0, 8).map((move) => `<div class="move"><div><strong>${T.escapeHtml(move.item)}</strong><small>${T.metricLabel(move.key)}</small></div><div class="${move.difference > 0 ? "up" : "down"}">${move.difference >= 0 ? "+" : ""}${move.difference.toFixed(4)} <small>${T.pct(move.score)}</small></div></div>`).join("") || `<div class="empty">A second snapshot is needed before moves can be calculated.</div>`;
    document.querySelector("#latest-table").innerHTML = latest.length ? `<table><thead><tr><th>State</th><th>Regular</th><th>Mid-grade</th><th>Premium</th><th>Diesel</th><th>Regular change</th></tr></thead><tbody>${latest.map((row) => `<tr><td><span class="state-name">${T.escapeHtml(row.item)}</span><span class="subline">${T.escapeHtml(row.region)}</span></td><td>${T.fuel(row.regular_usd_per_gallon)}</td><td>${T.fuel(row.midgrade_usd_per_gallon)}</td><td>${T.fuel(row.premium_usd_per_gallon)}</td><td>${T.fuel(row.diesel_usd_per_gallon)}</td><td>${changeCell(row, previous)}</td></tr>`).join("")}</tbody></table>` : `<div class="empty">No successful data snapshot yet.</div>`;
    document.querySelector("#data-day").textContent = day ? `Data date: ${day}` : "Waiting for the first run";
  }

  T.loadData().then(render).catch(T.showError);
}());

