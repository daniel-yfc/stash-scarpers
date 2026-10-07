import assert from "node:assert/strict";
import { test, describe } from "node:test";
import { Validator } from "./index.mjs";

describe("Validator - _collectConfigMappingErrors", () => {
  const validator = new Validator(["-a"]);

  test("returns error when sceneByName is present but sceneByQueryFragment is missing", () => {
    const mockData = {
      name: "TestScraper",
      sceneByName: {
        action: "scrapeXPath",
        scraper: "test",
      },
    };

    const errors = validator._collectConfigMappingErrors(mockData);

    assert.strictEqual(errors.length, 1);
    assert.deepStrictEqual(errors[0], {
      keyword: "sceneByName",
      message: "a `sceneByQueryFragment` configuration is required for `sceneByName` to work",
      params: { keyword: "sceneByName" },
      dataPath: "/sceneByName",
    });
  });

  test("returns no errors when both sceneByName and sceneByQueryFragment are present", () => {
    const mockData = {
      name: "TestScraper",
      sceneByName: {
        action: "scrapeXPath",
        scraper: "test",
      },
      sceneByQueryFragment: {
        action: "scrapeXPath",
        scraper: "test",
      },
    };

    const errors = validator._collectConfigMappingErrors(mockData);

    assert.strictEqual(errors.length, 0);
  });

  test("returns no errors when sceneByName is not present", () => {
    const mockData = {
      name: "TestScraper",
      sceneByURL: [
        {
          action: "scrapeXPath",
          scraper: "test",
        },
      ],
    };

    const errors = validator._collectConfigMappingErrors(mockData);

    assert.strictEqual(errors.length, 0);
  });

  test("returns no errors for an empty data object", () => {
    const errors = validator._collectConfigMappingErrors({});

    assert.strictEqual(errors.length, 0);
  });

  test("getMappingErrors includes _collectConfigMappingErrors results", () => {
    const mockData = {
      name: "TestScraper",
      sceneByName: {
        action: "scrapeXPath",
        scraper: "test",
      },
    };

    const errors = validator.getMappingErrors(mockData);

    const configErrors = errors.filter((err) => err.keyword === "sceneByName");
    assert.strictEqual(configErrors.length, 1);
    assert.strictEqual(
      configErrors[0].message,
      "a `sceneByQueryFragment` configuration is required for `sceneByName` to work",
    );
  });
});

describe("Validator - _collectScraperDefinitionErrors sceneByQueryFragment", () => {
  const validator = new Validator(["-a"]);

  test("validates scraper reference in sceneByQueryFragment", () => {
    const mockData = {
      name: "TestScraper",
      sceneByQueryFragment: {
        action: "scrapeXPath",
        queryURL: "{url}",
        scraper: "missing",
      },
      xPathScrapers: {
        existing: {
          scene: {
            Title: { selector: "//h1" },
          },
        },
      },
    };

    const errors = validator._collectScraperDefinitionErrors(mockData);
    const scraperErrors = errors.filter((e) => e.dataPath?.includes("sceneByQueryFragment"));
    assert.ok(scraperErrors.length > 0, "should report missing scraper for sceneByQueryFragment");
  });

  test("accepts valid sceneByQueryFragment scraper reference", () => {
    const mockData = {
      name: "TestScraper",
      sceneByQueryFragment: {
        action: "scrapeXPath",
        queryURL: "{url}",
        scraper: "existing",
      },
      xPathScrapers: {
        existing: {
          scene: {
            Title: { selector: "//h1" },
          },
        },
      },
    };

    const errors = validator._collectScraperDefinitionErrors(mockData);
    const scraperErrors = errors.filter((e) => e.dataPath?.includes("sceneByQueryFragment"));
    assert.strictEqual(scraperErrors.length, 0);
  });
});
