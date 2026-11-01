const assert = require("node:assert/strict");
const fs = require("node:fs");
const { normalize, searchRecords, excerpt } = require("../preview/search.js");

const records = [
  { source: "A", title: "Schur response", text: "Eliminate the interior vertices.", url: "chapter.html#a" },
  { source: "B", title: "Volume", text: "The Schur complement gives a boundary response.", url: "chapter.html#b" },
  { source: "C", title: "Café", text: "A literal <script> string is searchable.", url: "chapter.html#c" }
];
assert.equal(normalize("CAFÉ"), "cafe");
assert.deepEqual(searchRecords(records, "   "), { total: 0, items: [] });
assert.deepEqual(searchRecords(records, "SCHUR").items.map(x => x.source), ["A", "B"]);
assert.deepEqual(searchRecords(records, "Schur boundary").items.map(x => x.source), ["B"]);
assert.deepEqual(searchRecords(records, "missing").items, []);
assert.deepEqual(searchRecords(records, "cafe").items.map(x => x.source), ["C"]);
assert.deepEqual(searchRecords(records, "<script>").items.map(x => x.source), ["C"]);
assert.equal(searchRecords(records, "Schur", 1).total, 2);
assert.equal(searchRecords(records, "Schur", 1).items.length, 1);
assert.equal(excerpt("Short passage.", "passage"), "Short passage.");
assert.ok(excerpt("a ".repeat(200) + "boundary evidence", "boundary").includes("boundary"));

let actualQueries = 0;
if (process.argv[2]) {
  const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  for (const query of ["barrier", "Schur", "boundary", "forest", "asymmetric", "flat triangle"]) {
    const found = searchRecords(data.records, query);
    assert.ok(found.total > 0, query);
    assert.ok(found.items.every(x => x.url.startsWith("section9/")), query);
    actualQueries++;
  }
  assert.equal(searchRecords(data.records, "qzxqzx-nonexistent-word").total, 0);
}
console.log(JSON.stringify({ status: "passed", pureSearchAssertions: 11, actualEditionQueries: actualQueries }));
