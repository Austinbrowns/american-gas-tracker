(function () {
  const T = window.Tracker;
  T.renderNav("trends");

  function byDay(history, fn) {
    return T.dates(history).map((date) => ({ date, value: fn(T.rowsOn(history, date)) }));
  }

  function average(rows, key) {
    const values = rows.map((row) => T.number(row[key])).filter((value) => value != null);
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  }

  function chart(container, points, label) {
    T.drawLineChart(container, [{ label, labels: points.map((point) => point.date), values: points.map((point) => point.value) }], { label });
  }

  function render(data) {
    const { history } = data, latest = T.latestRows(history), day = T.latestDate(history);
    const items = latest.map((row) => row.item_id).sort();
    const picker = document.querySelector("#item-picker");
    picker.innerHTML = items.map((id) => { const row = latest.find((item) => item.item_id === id); return `<option value="${id}" ${items.indexOf(id) < 5 ? "selected" : ""}>${T.escapeHtml(row.item)}</option>`; }).join("");
    document.querySelector("#metric-picker").innerHTML = T.metrics.map((metric) => `<option value="${metric.key}">${metric.label}</option>`).join("");
    const updateItemChart = () => {
      const metric = document.querySelector("#metric-picker").value;
      const chosen = [...picker.selectedOptions].map((option) => option.value);
      const labels = T.dates(history);
      const series = chosen.map((id) => {
        const rows = T.byId(history.filter((row) => row.item_id === id));
        const name = latest.find((row) => row.item_id === id)?.item || id;
        return { label: name, labels, values: labels.map((date) => T.number(rows[date]?.[metric])) };
      });
      T.drawLineChart(document.querySelector("#item-chart"), series, { label: `${T.metricLabel(metric)} over time` });
    };
    picker.addEventListener("change", updateItemChart); document.querySelector("#metric-picker").addEventListener("change", updateItemChart); updateItemChart();

    const regularSpread = byDay(history, (rows) => { const values = rows.map((row) => T.number(row.regular_usd_per_gallon)).filter((value) => value != null); return values.length ? Math.max(...values) - Math.min(...values) : null; });
    const latestSpread = regularSpread.at(-1)?.value ?? 0, widest = regularSpread.reduce((best, point) => point.value > (best.value ?? -1) ? point : best, { value: -1 });
    document.querySelector("#finding-spread h2").textContent = `The latest regular-price spread is $${latestSpread.toFixed(4)} per gallon`;
    document.querySelector("#finding-spread p").textContent = `For each day, this chart subtracts the lowest state regular price from the highest state regular price. On ${day}, the spread was $${latestSpread.toFixed(4)}; the widest observed spread was $${(widest.value || 0).toFixed(4)} on ${widest.date}.`;
    chart(document.querySelector("#spread-chart"), regularSpread, "Regular price spread");

    const markup = byDay(history, (rows) => { const values = rows.map((row) => { const premium = T.number(row.premium_usd_per_gallon), regular = T.number(row.regular_usd_per_gallon); return premium != null && regular != null ? premium - regular : null; }).filter((value) => value != null); return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; });
    const latestMarkup = markup.at(-1)?.value ?? 0;
    document.querySelector("#finding-markup h2").textContent = `Premium costs $${latestMarkup.toFixed(4)} more than regular on average`;
    document.querySelector("#finding-markup p").textContent = `The daily value is the mean of premium minus regular for every state with both prices. The latest average gap is $${latestMarkup.toFixed(4)} per gallon, which shows how grade choice changes the pump price even within the same state.`;
    chart(document.querySelector("#markup-chart"), markup, "Average premium markup");

    const dieselGap = byDay(history, (rows) => { const values = rows.map((row) => { const diesel = T.number(row.diesel_usd_per_gallon), regular = T.number(row.regular_usd_per_gallon); return diesel != null && regular != null ? diesel - regular : null; }).filter((value) => value != null); return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; });
    const latestDieselGap = dieselGap.at(-1)?.value ?? 0;
    document.querySelector("#finding-diesel h2").textContent = `Diesel is $${latestDieselGap.toFixed(4)} above regular on average`;
    document.querySelector("#finding-diesel p").textContent = `For each day, the tracker averages diesel minus regular across the states. The latest gap is $${latestDieselGap.toFixed(4)} per gallon; this chart recomputes from history.csv every time the page loads.`;
    chart(document.querySelector("#diesel-chart"), dieselGap, "Average diesel gap");

    const averageRegular = byDay(history, (rows) => average(rows, "regular_usd_per_gallon"));
    const firstAverage = averageRegular.find((point) => point.value != null)?.value ?? 0, lastAverage = averageRegular.at(-1)?.value ?? firstAverage, averageChange = lastAverage - firstAverage;
    document.querySelector("#finding-average h2").textContent = `Average regular gas is ${averageChange >= 0 ? "up" : "down"} $${Math.abs(averageChange).toFixed(4)} since the first run`;
    document.querySelector("#finding-average p").textContent = `This is the unweighted mean of the 51 state/DC regular prices for each day. It moved from $${firstAverage.toFixed(4)} on the first available day to $${lastAverage.toFixed(4)} on ${day}, a change of ${averageChange >= 0 ? "+" : "-"}$${Math.abs(averageChange).toFixed(4)}.`;
    chart(document.querySelector("#average-chart"), averageRegular, "Average regular price");
  }

  T.loadData().then(render).catch(T.showError);
}());

