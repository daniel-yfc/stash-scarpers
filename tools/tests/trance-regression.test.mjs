import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import { parse } from "yaml";

const root = path.resolve(".");
const scraper = parse(fs.readFileSync(path.join(root, "scrapers/Trance.yml"), "utf8"));
const scene = scraper.xPathScrapers.sceneScraper;
const normalize = (script, value) => new Function("value", script)(value);

function fieldValue(doc, key) {
  const field = scene.scene[key];
  const selector = scene.common[field.selector] ?? field.selector;
  const result = doc.evaluate(selector, doc, null, 2, null);
  const raw = result.stringValue.trim();
  return field.postProcess.reduce((value, step) => {
    if (step.javascript) return normalize(step.javascript, value);
    if (step.replace) return step.replace.reduce((s, r) => s.replace(new RegExp(r.regex, "g"), r.with), value);
    return value;
  }, raw);
}

test("Trance duration extracts seconds from real fixtures", () => {
  for (const [file, expected] of [["detail-40625.html", "1545"], ["detail-40641.html", "1167"]]) {
    const dom = new JSDOM(fs.readFileSync(path.join(root, "tests/fixtures/trance", file), "utf8"));
    assert.equal(fieldValue(dom.window.document, "Duration"), expected, file);
  }
});

test("Trance duration rejects invalid formats", () => {
  const script = scene.scene.Duration.postProcess.find((step) => step.javascript)?.javascript;
  assert.ok(script, "Duration must use an executable conversion");
  for (const [input, expected] of [["00:25:45", "1545"], ["19:27", "1167"], ["bad", ""], ["00:68:00", ""], ["", ""]]) {
    assert.equal(normalize(script, input), expected, input);
  }
});

test("Trance performer URLs retain different model identifiers from the actual fixture", () => {
  const dom = new JSDOM(fs.readFileSync(path.join(root, "tests/fixtures/trance/detail-40625.html"), "utf8"));
  const xpath = scene.scene.Performers.URL.selector;
  const nodes = dom.window.document.evaluate(xpath, dom.window.document, null, 7, null);
  const script = scene.scene.Performers.URL.postProcess.find((step) => step.javascript)?.javascript;
  assert.ok(script, "Performer URL normalization missing");
  const urls = Array.from({ length: nodes.snapshotLength }, (_, i) => normalize(script, nodes.snapshotItem(i).nodeValue));
  assert.equal(urls.length, 2);
  assert.equal(new Set(urls).size, 2, "distinct performers must remain distinct");
  assert.ok(urls.some((url) => url.includes("model%5B%5D=210")));
  assert.ok(urls.some((url) => url.includes("model%5B%5D=212")));
  for (const url of urls) {
    const target = url.replace(/^https?:\\/\\//, "");
    assert.ok(scraper.performerByURL[0].url.some((pattern) => target.includes(pattern)), `performerByURL must route ${url}`);
  }
});
