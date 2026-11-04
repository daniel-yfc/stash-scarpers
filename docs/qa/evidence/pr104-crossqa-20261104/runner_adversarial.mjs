// CrossQA PR104 section 3: adversarial tests for routeThrough change in
// tools/verify-scraper-mappings.mjs @ 86ce058. Synthetic scraper objects
// mirror the BRAVO dual-route shape; documents via jsdom.
import fs from "node:fs";
import { JSDOM } from "/home/hatch/workspace/crossqa-pr104/repo/node_modules/jsdom/lib/api.js";
import { assertMappedCase } from "/home/hatch/workspace/crossqa-pr104/repo/tools/verify-scraper-mappings.mjs";

const FIX = "/home/hatch/workspace/crossqa-pr104/repo/tests/fixtures/bravo";
const doc234 = new JSDOM(fs.readFileSync(FIX + "/dvd-synthetic-234.html", "utf-8")).window.document;
const docClip = new JSDOM(fs.readFileSync(FIX + "/clip-284.html", "utf-8")).window.document;

const bravo = {
  sceneByURL: [
    { action: "scrapeXPath", url: ["bravo-japan.com/clips/", "www.bravo-japan.com/clips/"], scraper: "clipSceneScraper" },
    { action: "scrapeXPath", url: ["bravo-japan.com/dvds/", "www.bravo-japan.com/dvds/"], scraper: "dvdSceneScraper" },
  ],
  xPathScrapers: {
    clipSceneScraper: { scene: { URLs: { selector: "//link[@rel='canonical']/@href" } } },
    dvdSceneScraper: { scene: { URLs: { selector: "//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href" } } },
  },
};
const single = {
  sceneByURL: [{ action: "scrapeXPath", url: ["example.com/item/"], scraper: "onlyScraper" }],
  xPathScrapers: { onlyScraper: { scene: { URLs: { selector: "//link[@rel='canonical']/@href" } } } },
};
const docForeign = new JSDOM(`<html><head><link rel="canonical" href="https://evil.example.com/dvds/234"></head><body></body></html>`).window.document;
const docBadURL = new JSDOM(`<html><head><link rel="canonical" href="::not a url::"></head><body></body></html>`).window.document;
const docSingle = new JSDOM(`<html><head><link rel="canonical" href="https://example.com/item/42"></head><body></body></html>`).window.document;

let n = 0;
function run(label, item, doc, scraper, expectPass) {
  n++;
  let outcome, err = "";
  try { assertMappedCase(item, doc, scraper); outcome = "PASS"; }
  catch (e) { outcome = "FAIL"; err = e.message; }
  const verdict = (outcome === "PASS") === expectPass ? "AS-EXPECTED" : "*** UNEXPECTED ***";
  console.log(`CASE ${n} ${label}\n  -> ${outcome} ${verdict} ${err ? "| " + err : ""}`);
}

const mk = (name, scraperName, values) => ({
  name, mappedExpect: [{ field: "URLs", values, routeThrough: "sceneByURL", ...(scraperName ? { scraper: scraperName } : {}) }],
});

// 1. Cross-family: dvds URL asserted via clipSceneScraper -> must FAIL (new behavior)
run("cross-family dvds-via-clip", mk("x1", "clipSceneScraper", ["https://www.bravo-japan.com/dvds/234"]), doc234, bravo, false);
// 2. Correct family: dvds URL via dvdSceneScraper -> PASS
run("dvds-via-dvd", mk("x2", "dvdSceneScraper", ["https://www.bravo-japan.com/dvds/234"]), doc234, bravo, true);
// 3. Clips URL via clipSceneScraper on clip page -> PASS
run("clips-via-clip", mk("x3", "clipSceneScraper", ["https://www.bravo-japan.com/clips/284"]), docClip, bravo, true);
// 4. Ambiguous entrypoint: no scraper named on dual-route YAML -> FAIL (pre-existing getField guard)
run("ambiguous-no-scraper", mk("x4", null, ["https://www.bravo-japan.com/dvds/234"]), doc234, bravo, false);
// 5. Missing handler name -> FAIL (fail-closed)
run("missing-handler", mk("x5", "noSuchScraper", ["https://www.bravo-japan.com/dvds/234"]), doc234, bravo, false);
// 6. Single-handler scraper, no scraper name -> PASS (unchanged semantics)
run("single-handler", mk("x6", null, ["https://example.com/item/42"]), docSingle, single, true);
// 7. Foreign-host canonical asserted via dvd route -> FAIL
run("foreign-host", mk("x7", "dvdSceneScraper", ["https://evil.example.com/dvds/234"]), docForeign, bravo, false);
// 8. Invalid URL as canonical -> FAIL (invalid routed URL)
run("invalid-url", mk("x8", "dvdSceneScraper", ["::not a url::"]), docBadURL, bravo, false);
// 9. Wrong-scraper field extraction: clip handler on dvd page yields plain canonical; routeThrough now binds to clip routes -> FAIL (both extraction and route checked)
run("clip-extraction-on-dvd-page", mk("x9", "clipSceneScraper", ["https://www.bravo-japan.com/dvds/234"]), doc234, bravo, false);
