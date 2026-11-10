(function () {
  const T = window.Tracker;
  T.renderNav("browse");
  const shortlistKey = "american-gas-tracker-shortlist";
  const selected = () => new Set(JSON.parse(localStorage.getItem(shortlistKey) || "[]"));
  const save = (set) => localStorage.setItem(shortlistKey, JSON.stringify([...set].sort()));

  function render(data) {
    const latest = T.latestRows(data.history), regions = [...new Set(latest.map((row) => row.region))].sort();
    const region = document.querySelector("#region-filter"), source = document.querySelector("#source-filter");
    region.innerHTML += regions.map((value) => `<option value="${T.escapeHtml(value)}">${T.escapeHtml(value)}</option>`).join("");
    [...new Set(latest.map((row) => row.source))].sort().forEach((value) => { source.innerHTML += `<option value="${T.escapeHtml(value)}">${T.escapeHtml(value)}</option>`; });
    const redraw = () => {
      const query = document.querySelector("#search").value.toLowerCase().trim();
      const regionValue = region.value, sourceValue = source.value, sortValue = document.querySelector("#sort").value.split(":");
      const rows = latest.filter((row) => (!query || row.item.toLowerCase().includes(query)) && (!regionValue || row.region === regionValue) && (!sourceValue || row.source === sourceValue));
      const [sortKey, direction] = sortValue;
      rows.sort((a, b) => {
        const left = sortKey === "item" ? a.item : T.number(a[sortKey]);
        const right = sortKey === "item" ? b.item : T.number(b[sortKey]);
        if (left == null && right == null) return 0;
        if (left == null) return 1;
        if (right == null) return -1;
        return (left > right ? 1 : left < right ? -1 : 0) * (direction === "desc" ? -1 : 1);
      });
      const shortlist = selected();
      document.querySelector("#count").textContent = `${rows.length} of ${latest.length} states shown · ${shortlist.size} shortlisted`;
      document.querySelector("#browse-table").innerHTML = rows.length ? `<table><thead><tr><th aria-label="Shortlist"></th><th>State</th>${T.metrics.map((metric) => `<th>${metric.label} ($/gal)</th>`).join("")}<th>Source</th></tr></thead><tbody>${rows.map((row) => `<tr><td><button class="star" data-star="${row.item_id}" aria-label="${shortlist.has(row.item_id) ? "Remove from" : "Add to"} shortlist">${shortlist.has(row.item_id) ? "★" : "☆"}</button></td><td><span class="state-name">${T.escapeHtml(row.item)}</span><span class="subline">${T.escapeHtml(row.region)}</span></td>${T.metrics.map((metric) => `<td>${T.fuel(row[metric.key])}</td>`).join("")}<td><span class="badge">${T.escapeHtml(row.source)}</span></td></tr>`).join("")}</tbody></table>` : `<div class="empty">No states match these filters.</div>`;
    };
    ["#search", "#region-filter", "#source-filter", "#sort"].forEach((selector) => document.querySelector(selector).addEventListener("input", redraw));
    document.querySelector("#browse-table").addEventListener("click", (event) => {
      const button = event.target.closest("[data-star]");
      if (!button) return;
      const shortlist = selected();
      shortlist.has(button.dataset.star) ? shortlist.delete(button.dataset.star) : shortlist.add(button.dataset.star);
      save(shortlist); redraw();
    });
    redraw();
  }

  document.querySelector("#sort").innerHTML = `<option value="item:asc">State A–Z</option>${T.metrics.flatMap((metric) => [`<option value="${metric.key}:asc">${metric.label} low to high</option>`, `<option value="${metric.key}:desc">${metric.label} high to low</option>`]).join("")}`;
  T.loadData().then(render).catch(T.showError);
}());

