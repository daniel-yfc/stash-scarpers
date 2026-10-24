import assert from "node:assert/strict";
import fs from "node:fs";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import { parse } from "yaml";
import { assertMappedCase } from "../tools/verify-scraper-mappings.mjs";

const production = parse(fs.readFileSync("scrapers/Trance.yml", "utf8"));
const document = new JSDOM(
  fs.readFileSync("tests/fixtures/trance/detail-40625.html", "utf8"),
).window.document;

const caseWith = (field, values, extra = {}) => ({
  name: "Trance YAML mapping mutation control",
  mappedExpect: [{ field, values, ...extra }],
});

test("production YAML extracts expected duration and identity-bearing performer URLs", () => {
  assert.doesNotThrow(() =>
    assertMappedCase(caseWith("Duration", ["1545"]), document, production),
  );
  assert.doesNotThrow(() =>
    assertMappedCase(caseWith("Date", ["2026-06-25"]), document, production),
  );
  assert.doesNotThrow(() =>
    assertMappedCase(
      caseWith("Performers.URL", [
        "https://www.trance-video.com/product/search?model%5B%5D=210",
        "https://www.trance-video.com/product/search?model%5B%5D=212",
      ], { routeThrough: "performerByURL" }),
      document, production,
    ),
  );
});

test("production XPath mutation fails fixture assertions", () => {
  const mutated = structuredClone(production);
  mutated.xPathScrapers.sceneScraper.scene.Duration.selector = "//nonexistent";
  assert.throws(() =>
    assertMappedCase(caseWith("Duration", ["1545"]), document, mutated),
    /production YAML field Duration/,
  );
});

test("duration postprocessing mutation fails fixture assertions", () => {
  const mutated = structuredClone(production);
  mutated.xPathScrapers.sceneScraper.scene.Duration.postProcess = [
    { javascript: "return '999999';" },
  ];
  assert.throws(() =>
    assertMappedCase(caseWith("Duration", ["1545"]), document, mutated),
    /production YAML field Duration/,
  );
});

test("performer query-stripping mutation fails identity and route checks", () => {
  const mutated = structuredClone(production);
  mutated.xPathScrapers.sceneScraper.scene.Performers.URL.postProcess = [
    { javascript: "return 'https://www.trance-video.com/product/search';" },
  ];
  assert.throws(() =>
    assertMappedCase(
      caseWith("Performers.URL", [
        "https://www.trance-video.com/product/search?model%5B%5D=210",
        "https://www.trance-video.com/product/search?model%5B%5D=212",
      ], { routeThrough: "performerByURL" }),
      document, mutated,
    ),
    /does not match performerByURL/,
  );
});

test("broken performerByURL routing is rejected even if output URLs are correct", () => {
  const mutated = structuredClone(production);
  mutated.performerByURL[0].url = ["example.invalid/other"];
  assert.throws(() =>
    assertMappedCase(
      caseWith("Performers.URL", [
        "https://www.trance-video.com/product/search?model%5B%5D=210",
        "https://www.trance-video.com/product/search?model%5B%5D=212",
      ], { routeThrough: "performerByURL" }),
      document, mutated,
    ),
    /does not match performerByURL/,
  );
});

test("unsupported Stash date layouts fail explicitly instead of silently passing", () => {
  const mutated = structuredClone(production);
  mutated.xPathScrapers.sceneScraper.scene.Date.postProcess = [
    { parseDate: "02/01/2006" },
  ];
  assert.throws(() =>
    assertMappedCase(caseWith("Date", ["2026-06-25"]), document, mutated),
    /Unsupported parseDate layout/,
  );
});
