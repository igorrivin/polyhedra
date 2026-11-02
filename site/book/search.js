// Browser-local passage search. It never executes the numerical toolkit.
(() => {
function normalize(value) {
  return String(value).normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function searchRecords(records, query, limit = 12) {
  const terms = normalize(query).trim().split(/\s+/).filter(Boolean);
  if (!terms.length) return { total: 0, items: [] };
  const matches = [];
  records.forEach((record, order) => {
    const title = normalize(record.title);
    const text = normalize(record.text);
    if (terms.every(term => (title + " " + text).includes(term))) {
      const score = terms.reduce((sum, term) => sum + (title.includes(term) ? 3 : 0) + (text.includes(term) ? 1 : 0), 0);
      matches.push({ record, order, score });
    }
  });
  matches.sort((a, b) => b.score - a.score || a.order - b.order);
  return { total: matches.length, items: matches.slice(0, limit).map(item => item.record) };
}

function excerpt(text, query, length = 230) {
  const terms = normalize(query).trim().split(/\s+/).filter(Boolean);
  const normalized = normalize(text);
  const first = Math.min(...terms.map(term => normalized.indexOf(term)).filter(index => index >= 0));
  const start = Number.isFinite(first) ? Math.max(0, first - 65) : 0;
  const end = Math.min(text.length, start + length);
  return (start ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
}

function mountSearch() {
  const form = document.getElementById("edition-search-form");
  if (!form) return;
  const input = document.getElementById("edition-query");
  const button = form.querySelector("button");
  const status = document.getElementById("edition-search-status");
  const results = document.getElementById("edition-search-results");
  try {
    const data = JSON.parse(document.getElementById("edition-search-data").textContent);
    if (data.schema_version !== 1 || !Array.isArray(data.records)) throw new Error("Invalid search index");
    input.disabled = false;
    button.disabled = false;
    status.textContent = "Search all chapters, appendices and references.";
    function render() {
      const query = input.value.trim();
      results.replaceChildren();
      if (!query) {
        results.hidden = true;
        status.textContent = "Search all chapters, appendices and references.";
        return;
      }
      const found = searchRecords(data.records, query);
      results.hidden = found.total === 0;
      status.textContent = found.total ? `Showing ${found.items.length} of ${found.total} matching passages.` : "No matching passages. Try fewer words, or use the chapter contents.";
      for (const record of found.items) {
        const row = document.createElement("li");
        const source = document.createElement("p");
        source.className = "edition-search-source";
        source.textContent = record.source;
        const link = document.createElement("a");
        link.href = record.url;
        link.textContent = record.title;
        const description = document.createElement("p");
        description.textContent = excerpt(record.text, query);
        row.append(source, link, description);
        results.append(row);
      }
    }
    form.addEventListener("submit", event => { event.preventDefault(); render(); });
    let timer;
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(render, 140); });
    form.addEventListener("reset", () => { clearTimeout(timer); setTimeout(render, 0); });
  } catch {
    status.textContent = "Search is unavailable. Use the contents below; all downloads remain available.";
  }
}

if (typeof module !== "undefined" && module.exports) module.exports = { normalize, searchRecords, excerpt };
if (typeof document !== "undefined") mountSearch();
})();
