import assert from "node:assert/strict";
import fs from "node:fs";
import { test } from "node:test";
import { parse } from "yaml";
import { extractSceneURLs, classifyScrapedFields } from "../tools/scrutiny-analysis.mjs";

test("recognizes a singular search scene.URL field from a real scraper YAML", () => {
  const trance = parse(fs.readFileSync("scrapers/Trance.yml", "utf8"));
  const html = '<html><a href="/product/detail/40625">Scene</a></html>';
  const urls = extractSceneURLs(html, trance, "https://www.trance-video.com/product/search?keyword=test", "test", null);
  assert.deepEqual(urls.map((x) => x.url), ["https://www.trance-video.com/product/detail/40625"]);
});

test("recognizes plural scene.URLs and de-duplicates candidates", () => {
  const scraper = {
    sceneByName: { scraper: "search" },
    xPathScrapers: { search: { scene: { URLs: { selector: "//a/@href" } } } },
  };
  const html = '<a href="/scene/1">A</a><a href="/scene/1">B</a><a href="/scene/2">C</a>';
  const found = extractSceneURLs(html, scraper, "https://example.test/search", "query", 2);
  assert.deepEqual(found.map((x) => x.url), ["https://example.test/scene/1", "https://example.test/scene/2"]);
  assert.deepEqual(found.map((x) => x.page), [2, 2]);
});

test("fall back to sceneByURL with array patterns instead of treating arrays as strings", () => {
  const scraper = {
    sceneByName: { scraper: "search" },
    xPathScrapers: { search: { scene: { URL: { selector: "//missing/@href" } } } },
    sceneByURL: [{ url: ["example.test/scene/", "www.example.test/video/"] }],
  };
  const html = '<a href="/scene/7">Valid</a><a href="/video/9">Valid</a><a href="https://evil.test/scene/1">Other</a>';
  const urls = extractSceneURLs(html, scraper, "https://example.test/search", "query", null);
  assert.deepEqual(urls.map((x) => x.url), ["https://example.test/scene/7", "https://example.test/video/9"]);
});

test("report fetched HTML with no XPath matches as NO_FIELDS_MATCHED", () => {
  const output = classifyScrapedFields({ scene: {
    Title: { selector: { count: 0, error: null } },
    Code: { selector: { count: 0, error: null } },
  } });
  assert.deepEqual(output, { status: "NO_FIELDS_MATCHED", matched: 0, total: 2, postProcessExecuted: false });
});

test("distinguish selector matches from fully post-processed verified values", () => {
  const output = classifyScrapedFields({ scene: {
    Title: { selector: { count: 1, error: null } },
    Performers: { Name: { selector: { count: 2, error: null } }, URL: { selector: { count: 2, error: null } } },
    Duration: { selector: { count: 0, error: null }, postProcess: [{ javascript: "return '999'" }] },
  } });
  assert.deepEqual(output, { status: "SELECTOR_MATCHED", matched: 3, total: 4, postProcessExecuted: false });
});

test("report XPath errors and no-selector results separately", () => {
  assert.equal(classifyScrapedFields({ scene: { Title: { selector: { count: 0, error: "Invalid XPath" } } } }).status, "SELECTOR_ERROR");
  assert.equal(classifyScrapedFields({ scene: { Gender: { fixed: "MALE" } } }).status, "NO_SELECTORS");
});
