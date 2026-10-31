import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import { parse } from "yaml";

// STASH-E2E-09 regression: ACCEED product-page auth guard.
// Red on pre-guard main: the unguarded Title selector extracted ログイン
// from the anonymous login redirect (QA v2 report). Green after every
// page-derived sceneScraper selector was scoped behind $guard.

const root = path.resolve(".");
const scraper = parse(fs.readFileSync(path.join(root, "scrapers/ACCEED.yml"), "utf8"));
const sceneScraper = scraper.xPathScrapers.sceneScraper;

const PAGE_DERIVED_FIELDS = [
  "Title", "Code", "Date", "Details", "Image", "Studio.Name",
  "Tags.Name", "Performers.Name", "Performers.URL",
];

function mappingFor(fieldPath) {
  let field = sceneScraper.scene;
  for (const component of fieldPath.split(".")) field = field[component];
  return field;
}

function expand(selector) {
  let expanded = selector;
  for (const [key, replacement] of Object.entries(sceneScraper.common)) {
    expanded = expanded.split(key.startsWith("$") ? key : "$" + key).join(replacement);
  }
  assert.ok(!/\$[a-zA-Z_][a-zA-Z0-9_]*/.test(expanded), "unresolved common selector: " + expanded);
  return expanded;
}

function extract(document, fieldPath) {
  const mapping = mappingFor(fieldPath);
  if (typeof mapping === "object" && mapping.fixed !== undefined) return [String(mapping.fixed)];
  const result = document.evaluate(
    expand(mapping.selector), document, null,
    document.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null,
  );
  return Array.from({ length: result.snapshotLength }, (_, i) =>
    (result.snapshotItem(i).nodeValue ?? result.snapshotItem(i).textContent ?? "").trim());
}

function loadFixture(file) {
  const html = fs.readFileSync(path.join(root, "tests/fixtures/acceed", file), "utf8");
  return new JSDOM(html).window.document;
}

test("ACCEED scene fields are scoped behind the product-page guard", () => {
  for (const fieldPath of PAGE_DERIVED_FIELDS) {
    const mapping = mappingFor(fieldPath);
    assert.ok(mapping.selector, fieldPath + " must use a page selector");
    assert.ok(
      expand(mapping.selector).startsWith("//body[.//ul[contains(@class,'thongso')]]"),
      fieldPath + " must be scoped behind the ul.thongso product guard",
    );
  }
});

test("ACCEED anonymous login page yields no writable scene metadata", () => {
  const document = loadFixture("auth-login-redirect.html");
  // Red premise (kept visible on purpose): the pre-guard site-template
  // heading selector still matches the login page heading.
  const unguarded = document.evaluate(
    "//div[@id='content4']//blockquote/h2/text()[normalize-space()][1]",
    document, null, document.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null,
  );
  assert.equal(unguarded.snapshotLength, 1);
  assert.equal(unguarded.snapshotItem(0).nodeValue.trim(), "ログイン");
  for (const fieldPath of PAGE_DERIVED_FIELDS) {
    assert.deepEqual(extract(document, fieldPath), [], fieldPath + " leaked on the login page");
  }
});

test("ACCEED committed product fixture still extracts full metadata", () => {
  const document = loadFixture("detail-ACST270.html");
  assert.deepEqual(extract(document, "Title"), ["拘束したノンケを喰う！"]);
  assert.deepEqual(extract(document, "Code"), ["ACST270"]);
  assert.deepEqual(extract(document, "Studio.Name"), ["ノンケ喰い"]);
  assert.deepEqual(extract(document, "URLs"), ["{inputURL}"]);
});

test("ACCEED anonymous search flow preserved", () => {
  assert.equal(scraper.sceneByName.scraper, "searchScraper");
  assert.equal(scraper.sceneByName.queryURL, "https://acceed.jp/search.php?s={}");
  assert.equal(scraper.sceneByQueryFragment.queryURL, "{url}");
  assert.equal(scraper.sceneByQueryFragment.scraper, "sceneScraper");
  assert.equal(scraper.sceneByFragment, undefined, "direct fragment mode must stay removed");
  assert.ok(scraper.sceneByURL.some((route) => route.url.includes("acceed.jp/detail.")));
});
