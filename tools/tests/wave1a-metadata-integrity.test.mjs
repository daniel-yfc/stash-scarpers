// Wave 1A — Metadata Integrity regression tests (STASH-E2E-05, 06a, 06b, 08).
//
// These tests execute the *production* YAML selectors and postProcess
// steps from scrapers/Justice01.yml, scrapers/KOShop.yml and
// scrapers/CK-Download.yml against committed fixtures, following the
// pattern of tools/tests/trance-regression.test.mjs. They are an offline
// regression aid, not a substitute for Stash runtime (Gate B) evidence.
//
// Fixture provenance:
// - Captured pages already committed under tests/fixtures/<site>/.
// - *-controlled.html pages are minimal reproductions built only from
//   values recorded in the Live E2E evidence (see each file's header).

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import { parse } from "yaml";

const root = path.resolve(".");

function loadScraper(file) {
  return parse(fs.readFileSync(path.join(root, "scrapers", file), "utf8"));
}

function loadDoc(fixturePath) {
  const dom = new JSDOM(fs.readFileSync(path.join(root, fixturePath), "utf8"));
  return dom.window.document;
}

function loadDocString(html) {
  return new JSDOM(html).window.document;
}

function resolveSelector(selector, common = {}) {
  let expanded = selector;
  const entries = Object.entries(common).sort((a, b) => b[0].length - a[0].length);
  for (const [rawKey, replacement] of entries) {
    const key = rawKey.startsWith("$") ? rawKey : "$" + rawKey;
    expanded = expanded.replaceAll(key, replacement);
  }
  return expanded;
}

function postProcess(raw, steps = []) {
  let output = raw;
  for (const step of steps || []) {
    if (step.replace) {
      for (const op of step.replace) {
        output = String(output).replace(new RegExp(op.regex, "g"), op.with);
      }
    } else if (typeof step.javascript === "string") {
      const code = "(function () {\n" + step.javascript + "\n})()";
      output = new vm.Script(code).runInNewContext({ value: output }, { timeout: 250 });
    } else if (step.parseDate !== undefined) {
      // The javascript step before parseDate already emits the layout's
      // ISO form for the fields asserted here; keep the value as-is.
    } else {
      throw new Error("Unsupported postProcess step: " + Object.keys(step).join(","));
    }
  }
  return output == null ? "" : String(output);
}

// Evaluate one production field against a document; returns the list of
// post-processed values (one per matched node), like Stash's XPath
// scraper before any concat joining.
function fieldValues(doc, scraperDef, domain, fieldPath) {
  let field = scraperDef[domain];
  for (const part of fieldPath.split(".")) field = field?.[part];
  assert.ok(field !== undefined, `missing field ${fieldPath}`);
  if (typeof field === "object" && field.fixed !== undefined) return [String(field.fixed)];
  const selector = resolveSelector(field.selector, scraperDef.common || {});
  const result = doc.evaluate(
    selector, doc, null,
    doc.defaultView.XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null,
  );
  return Array.from({ length: result.snapshotLength }, (_, i) => {
    const node = result.snapshotItem(i);
    const raw = (node.nodeValue ?? node.textContent ?? "").trim();
    return postProcess(raw, field.postProcess);
  });
}

const justice = loadScraper("Justice01.yml");
const koshop = loadScraper("KOShop.yml");
const ck = loadScraper("CK-Download.yml");

// ---- STASH-E2E-05: Justice01 detail URLs --------------------------------

test("Wave1A E2E-05: justice115th yields exactly one URL, equal to canonical", () => {
  const doc = loadDoc("tests/fixtures/justice01/page-justice115th-controlled.html");
  const urls = fieldValues(doc, justice.xPathScrapers.sceneScraper, "scene", "URLs");
  assert.deepEqual(urls, ["https://www.justice01.com/justice115th/"]);
  assert.ok(!urls.join("").includes("\n"), "URL must not contain a newline");
});

test("Wave1A E2E-05: captured Justice01 pages yield exactly the canonical URL", () => {
  for (const [file, url] of [
    ["page-justice4th17.html", "https://www.justice01.com/justice4th17/"],
    ["page-justice095th.html", "https://www.justice01.com/justice095th/"],
    ["page-guilty2nd14.html", "https://www.justice01.com/guilty2nd14/"],
  ]) {
    const doc = loadDoc(path.join("tests/fixtures/justice01", file));
    assert.deepEqual(
      fieldValues(doc, justice.xPathScrapers.sceneScraper, "scene", "URLs"),
      [url],
      file,
    );
  }
});

test("Wave1A E2E-05: og:url is used only when canonical is missing", () => {
  const doc = loadDoc("tests/fixtures/justice01/page-justice095th-no-canonical-controlled.html");
  assert.deepEqual(
    fieldValues(doc, justice.xPathScrapers.sceneScraper, "scene", "URLs"),
    ["https://www.justice01.com/justice095th/"],
  );
});

test("Wave1A E2E-05: no canonical and no og:url yields no URL (no fabrication)", () => {
  const doc = loadDocString(
    '<html><head><title>JUSTICE09(5th) | JUSTICE</title></head><body>'
    + '<article class="post"><h1 class="entry-title">JUSTICE09(5th)</h1></article>'
    + "</body></html>",
  );
  assert.deepEqual(
    fieldValues(doc, justice.xPathScrapers.sceneScraper, "scene", "URLs"),
    [],
  );
});

// Stabilization (Task B, case 4) — canonical present but empty/invalid:
// * Before the stabilization fix, an empty or whitespace-only canonical
//   href still counted as "present": the selector emitted one empty
//   value ("") and the not(canonical) guard suppressed the valid og:url
//   fallback. The guard now tests normalize-space(@href), so an empty /
//   whitespace-only canonical falls back to og:url exactly like an
//   absent canonical (asserted below).
// * A non-empty but malformed canonical still wins and the og:url is
//   NOT used: XPath cannot validate URL syntax, no such page exists in
//   the captured evidence, and guessing a validity rule in the selector
//   could reject legitimate URLs. This residual behavior is documented
//   here rather than silently "fixed" (asserted below so any change is
//   a deliberate, reviewed event).
test("Wave1A E2E-05: empty or whitespace canonical falls back to og:url", () => {
  for (const href of ["", "   "]) {
    const doc = loadDocString(
      `<html><head><link rel="canonical" href="${href}">`
      + '<meta property="og:url" content="https://www.justice01.com/justice095th/"></head>'
      + '<body><article class="post"><h1 class="entry-title">JUSTICE09(5th)</h1></article></body></html>',
    );
    const urls = fieldValues(doc, justice.xPathScrapers.sceneScraper, "scene", "URLs");
    assert.deepEqual(urls, ["https://www.justice01.com/justice095th/"], `href=${JSON.stringify(href)}`);
    assert.ok(!urls.join("").includes("\n"), "URL must not contain a newline");
  }
});

test("Wave1A E2E-05: non-empty malformed canonical still wins (documented limitation)", () => {
  const doc = loadDocString(
    '<html><head><link rel="canonical" href="not-a-url">'
    + '<meta property="og:url" content="https://www.justice01.com/justice095th/"></head>'
    + '<body><article class="post"><h1 class="entry-title">JUSTICE09(5th)</h1></article></body></html>',
  );
  assert.deepEqual(
    fieldValues(doc, justice.xPathScrapers.sceneScraper, "scene", "URLs"),
    ["not-a-url"],
  );
});

// ---- STASH-E2E-06a: KOShop search URLs keep product_id -------------------

test("Wave1A E2E-06a: search URLs preserve and normalize product_id only", () => {
  const doc = loadDoc("tests/fixtures/koshop/search-41979-controlled.html");
  const urls = fieldValues(doc, koshop.xPathScrapers.searchScraper, "scene", "URLs");
  assert.deepEqual(urls, [
    "https://www.ko-shop.com/products/detail.php?product_id=41979",
    "https://www.ko-shop.com/products/detail.php?product_id=40445",
  ]);
  // The preserved URL must route to the detail scraper.
  for (const u of urls) {
    const candidate = u.replace(/^https?:\/\//, "");
    assert.ok(
      koshop.sceneByURL.some((r) => r.url.some((p) => candidate.startsWith(p))),
      `search URL does not route to sceneByURL: ${u}`,
    );
  }
});

test("Wave1A E2E-06a: search URL javascript rejects links without product_id", () => {
  const script = koshop.xPathScrapers.searchScraper.scene.URLs.postProcess
    .find((s) => typeof s.javascript === "string")?.javascript;
  assert.ok(script, "search URLs must use a javascript postProcess");
  const run = (v) => new vm.Script("(function () {\n" + script + "\n})()")
    .runInNewContext({ value: v }, { timeout: 250 });
  assert.equal(run("/products/detail.php"), "");
  assert.equal(run("/products/detail.php?class_id=3"), "");
  assert.equal(
    run("https://www.ko-shop.com/products/detail.php?product_id=41979&utm_source=x"),
    "https://www.ko-shop.com/products/detail.php?product_id=41979",
  );
  // Tracking parameters before and after product_id must not corrupt
  // the product identity: only product_id survives normalization.
  assert.equal(
    run("https://www.ko-shop.com/products/detail.php?utm_source=x&product_id=41979&from=search"),
    "https://www.ko-shop.com/products/detail.php?product_id=41979",
  );
  assert.equal(
    run("/products/detail.php?from=search&product_id=40445"),
    "https://www.ko-shop.com/products/detail.php?product_id=40445",
  );
});

// ---- STASH-E2E-06b: KOShop missing product fails closed ------------------

test("Wave1A E2E-06b: missing-product error page yields no writable metadata", () => {
  const doc = loadDoc("tests/fixtures/koshop/error-missing-product-controlled.html");
  const scene = koshop.xPathScrapers.sceneScraper;
  // Every product-derived field, asserted individually: no Title, Code,
  // Date, Details, Image, Studio (name or URLs) or Tags may be emitted
  // for the controlled product_id=99999999 error page.
  for (const field of ["Title", "Code", "Date", "Details", "Image", "Studio.Name", "Studio.URLs", "Tags.Name"]) {
    assert.deepEqual(fieldValues(doc, scene, "scene", field), [], `scene ${field} must be empty`);
  }
  const group = koshop.xPathScrapers.groupScraper;
  for (const field of ["Name", "Aliases", "Duration", "FrontImage", "Date", "Synopsis", "Studio.Name", "Studio.URLs"]) {
    assert.deepEqual(fieldValues(doc, group, "group", field), [], `group ${field} must be empty`);
  }
});

// Documented limitation (STASH-E2E-06b): scene and group URLs are
// fixed: "{inputURL}". The YAML schema offers no conditional fixed
// value, so on a missing-product scrape Stash will still substitute the
// requested (bogus) URL as the scene/group URL — that echo is input
// data, not extracted metadata, and this suite deliberately asserts the
// raw template to keep the limitation visible. A URL-only result must
// NOT be described as fully safe until Gate B verifies actual Stash
// behavior with the candidate package.
test("Wave1A E2E-06b: URLs remains the fixed {inputURL} echo (documented limitation)", () => {
  const doc = loadDoc("tests/fixtures/koshop/error-missing-product-controlled.html");
  assert.deepEqual(
    fieldValues(doc, koshop.xPathScrapers.sceneScraper, "scene", "URLs"),
    ["{inputURL}"],
  );
  assert.deepEqual(
    fieldValues(doc, koshop.xPathScrapers.groupScraper, "group", "URLs"),
    ["{inputURL}"],
  );
});

test("Wave1A E2E-06b: valid KOShop detail still yields its code and h2 title", () => {
  const doc = loadDoc("tests/fixtures/koshop/product-40445.html");
  const scene = koshop.xPathScrapers.sceneScraper;
  assert.deepEqual(fieldValues(doc, scene, "scene", "Code"), ["JUS180_DVD"]);
  assert.deepEqual(fieldValues(doc, scene, "scene", "Title"), ["JUSTICE 5th 03"]);
  const doc2 = loadDoc("tests/fixtures/koshop/product-38513.html");
  assert.deepEqual(fieldValues(doc2, scene, "scene", "Code"), ["KKUR117_DVD"]);
  // Frozen control 41979 → BWB365_DVD comes from the Live E2E evidence;
  // its detail page HTML was never captured offline, so this suite does
  // NOT claim a 41979 detail pass. Offline, the search side of the
  // control is asserted: card 41979 keeps its identity and title.
  const search = loadDoc("tests/fixtures/koshop/search-41979-controlled.html");
  assert.deepEqual(
    fieldValues(search, koshop.xPathScrapers.searchScraper, "scene", "Title"),
    ["ナマ狂い種壺待機", "JUSTICE 5th 03"],
  );
  // The 41979 detail scrape itself (expect Code BWB365_DVD) is a Gate B
  // case; Search → Detail is not claimed as Live PASS here.
});

test("Wave1A E2E-06b: valid KOShop group result extracts from the same detail page", () => {
  // groupByURL routes the same product detail page to groupScraper
  // (verified site behavior recorded in scrapers/KOShop.yml). Offline
  // this verifies the group selectors against captured pages; the
  // Stash runtime group mode itself remains a Gate B check.
  const group = koshop.xPathScrapers.groupScraper;
  const doc = loadDoc("tests/fixtures/koshop/product-40445.html");
  assert.deepEqual(fieldValues(doc, group, "group", "Name"), ["JUSTICE 5th 03"]);
  assert.deepEqual(fieldValues(doc, group, "group", "Aliases"), ["JUS180_DVD"]);
  assert.deepEqual(fieldValues(doc, group, "group", "Duration"), ["16800"]);
  assert.deepEqual(fieldValues(doc, group, "group", "Date"), ["2024-07-19"]);
  assert.deepEqual(fieldValues(doc, group, "group", "Studio.Name"), ["JUSTICE"]);
  assert.deepEqual(
    fieldValues(doc, group, "group", "FrontImage"),
    ["https://www.ko-shop.com/upload/save_image/84/JUS180_DVD.jpg"],
  );
  const doc2 = loadDoc("tests/fixtures/koshop/product-38513.html");
  assert.deepEqual(fieldValues(doc2, group, "group", "Name"), ["体育教師 8"]);
  assert.deepEqual(fieldValues(doc2, group, "group", "Aliases"), ["KKUR117_DVD"]);
  assert.deepEqual(fieldValues(doc2, group, "group", "Duration"), ["6420"]);
});

// ---- STASH-E2E-08: CK-Download Title priority ----------------------------

test("Wave1A E2E-08: detail/34418 title matches the search-result title", () => {
  const doc = loadDoc("tests/fixtures/ckdownload/product-34418-controlled.html");
  assert.deepEqual(
    fieldValues(doc, ck.xPathScrapers.sceneScraper, "scene", "Title"),
    ["[AVオリジナル]ガチ検証! ヤリチンサッカー部20才が女優の誘惑に負けて欲望丸出しSEX!?"],
  );
  assert.deepEqual(
    fieldValues(doc, ck.xPathScrapers.sceneScraper, "scene", "Code"),
    ["ORCOAV028"],
  );
});

test("Wave1A E2E-08: generic DVDタイトル placeholder falls back to h3 (16942 pattern)", () => {
  const doc = loadDoc("tests/fixtures/ckdownload/product-16942.html");
  assert.deepEqual(
    fieldValues(doc, ck.xPathScrapers.sceneScraper, "scene", "Title"),
    ["バーチャル彼氏 CK DOWNLOADオリジナル～智暉編～"],
  );
});

test("Wave1A E2E-08: real DVDタイトル wins on a different DVD product", () => {
  const doc = loadDoc("tests/fixtures/ckdownload/product-8872.html");
  assert.deepEqual(
    fieldValues(doc, ck.xPathScrapers.sceneScraper, "scene", "Title"),
    ["ブリーフ大好き親父と援交常習少年"],
  );
  const doc2 = loadDoc("tests/fixtures/ckdownload/product-11441.html");
  assert.deepEqual(
    fieldValues(doc2, ck.xPathScrapers.sceneScraper, "scene", "Title"),
    ["BACK PASS ～RCHS 5th Anniversary～"],
  );
});

test("Wave1A E2E-08: empty DVDタイトル falls back to h3", () => {
  const doc = loadDoc("tests/fixtures/ckdownload/product-34479.html");
  assert.deepEqual(
    fieldValues(doc, ck.xPathScrapers.sceneScraper, "scene", "Title"),
    ["[wakasen]HDD蔵出し 大人気モデルひろき君との初めての生ハメ撮りは種付け1発口に2発!"],
  );
});

test("Wave1A E2E-08: error page yields no Title (no //title fallback)", () => {
  const doc = loadDoc("tests/fixtures/ckdownload/failure-cloudflare.html");
  assert.deepEqual(
    fieldValues(doc, ck.xPathScrapers.sceneScraper, "scene", "Title"),
    [],
  );
});
