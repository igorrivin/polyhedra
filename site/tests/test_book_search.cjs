// Pure search regressions; no server, browser, fetch or numerical execution.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { searchRecords, excerpt } = require("../book/search.js");
const records = [
  { source: "Chapter 15", title: "15 Regular quantum Airy transition", text: "The contour and cutoff comparisons are numerical evidence.", url: "15-quantum-airy.html#result" },
  { source: "Chapter 28", title: "28 Marked-torus model", text: "Möbius cancellation has a separate arithmetic role.", url: "28-genus-two-model.html#model" },
];
assert.equal(searchRecords(records, "Airy contour").items[0].url, records[0].url);
assert.equal(searchRecords(records, "mobius").items[0].url, records[1].url);
assert.equal(searchRecords(records, "").total, 0);
assert.equal(searchRecords(records, "unknown phrase").total, 0);
assert.ok(excerpt("A literal <script> is text", "script").includes("<script>"));
if (process.argv[2]) {
  const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  assert.equal(data.schema_version, 1);
  for (const term of ["Airy", "Schur", "marked torus", "Fricke", "arithmetic", "quantum"]) {
    const found = searchRecords(data.records, term);
    assert.ok(found.total > 0, `No complete-edition matches for ${term}`);
    assert.ok(found.items.every(row => !row.url.startsWith("section9/")));
  }
  assert.ok(data.records.some(row => row.url.startsWith("appendix-b-conventions.html")));
  assert.ok(data.records.some(row => row.url.startsWith("references.html")));
}
console.log("Complete-edition search checks passed.");
