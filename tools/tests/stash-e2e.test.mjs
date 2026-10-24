import assert from "node:assert/strict";
import { test } from "node:test";
import {
  QUERIES, parseArguments, validateConfiguration, verifyScene, execute,
} from "../stash-e2e.mjs";

const COMMIT = "0123456789abcdef0123456789abcdef01234567";
const BASE = {
  mode: "golden", env: "test", live: true, commit: COMMIT,
  baseURL: "https://stash-test.example.test",
  report: "/tmp/stash-e2e-test-report.json",
  expectedVersion: "v0.31.1",
};
const inventory = {
  version: { version: "v0.31.1", hash: "abcd" },
  listScrapers: [{
    id: "Trance", name: "Trance",
    scene: { urls: ["trance-video.com/product/detail/"], supported_scrapes: ["URL", "NAME"] },
    performer: { urls: [], supported_scrapes: ["URL"] },
  }],
};
const sceneA = {
  title: "【先行配信】熱狂球児 part28", code: "TR-16-0028-01",
  date: "2026-06-25", duration: 1545, urls: [],
  performers: [
    { name: "Model A", urls: ["https://www.trance-video.com/product/search?model%5B%5D=210"] },
    { name: "Model B", urls: ["https://www.trance-video.com/product/search?model%5B%5D=212"] },
  ],
};
const sceneB = {
  title: "【沖修斗】private sex6", code: "TC-05-0013-01",
  date: "2026-10-08", duration: 1167, urls: [],
  performers: [],
};
function mocked(records) {
  return async (_url, options) => {
    const op = JSON.parse(options.body);
    if (op.query.includes("E2EInventory")) return new Response(JSON.stringify({ data: inventory }));
    if (op.query.includes("E2EScene")) {
      return new Response(JSON.stringify({ data: { scrapeSceneURL: records[op.variables.url] ?? null } }));
    }
    if (op.query.includes("E2ESearch")) {
      const isSearch = op.variables.input.query !== undefined;
      return new Response(JSON.stringify({ data: {
        scrapeSingleScene: isSearch
          ? [{ title: sceneB.title, urls: ["https://www.trance-video.com/product/detail/40641"] }]
          : [sceneB],
      } }));
    }
    throw new Error("Unexpected operation");
  };
}
const sourceA = "https://www.trance-video.com/product/detail/40625";
const sourceB = "https://www.trance-video.com/product/detail/40641";

test("no GraphQL mutation or data-writing operations are included", () => {
  for (const query of Object.values(QUERIES)) {
    assert.match(query, /^query E2E/);
    assert.doesNotMatch(query, /\bmutation\b|\bsceneCreate\b|\bsceneUpdate\b|\breloadScrapers\b/);
  }
});

test("configuration fails closed without target, live consent, or production approval", () => {
  assert.throws(() => validateConfiguration({ ...BASE, env: undefined }), /--env/);
  assert.throws(() => validateConfiguration({ ...BASE, mode: "golden", live: false }), /--live/);
  assert.throws(() => validateConfiguration({ ...BASE, env: "production", productionRead: false }), /production-read/);
  assert.throws(() => validateConfiguration({ ...BASE, commit: "HEAD" }), /full Git commit/);
  assert.throws(() => validateConfiguration({ ...BASE, report: "repo-report.json" }), /absolute/);
  assert.throws(() => validateConfiguration({ ...BASE, baseURL: "https://user:pass@example.test" }), /STASH_BASE_URL/);
  assert.throws(() => validateConfiguration({ ...BASE, baseURL: "http://100.100.100.100:9999" }), /STASH_BASE_URL/);
  assert.equal(validateConfiguration({ ...BASE, baseURL: "http://100.100.100.100:9999", allowPrivateHTTP: true }).endpoint,
    "http://100.100.100.100:9999/graphql");
  assert.equal(validateConfiguration({ ...BASE, mode: "inventory", live: false }).mode, "inventory");
});

test("only known command line switches are allowed", () => {
  assert.deepEqual(parseArguments(["--mode=golden", "--env=test", "--live"]), {
    mode: "golden", env: "test", live: true,
  });
  assert.throws(() => parseArguments(["--mutation=sceneUpdate"]), /Unknown CLI option/);
});

test("Trance golden assertions validate seconds and distinct performer IDs", () => {
  const testcase = {
    expected: { title: sceneA.title, code: sceneA.code, date: sceneA.date, duration: 1545 },
    performerModelIds: ["210", "212"],
  };
  assert.equal(verifyScene(sceneA, testcase).status, "PASS");
  assert.equal(verifyScene({ ...sceneA, duration: 2545 }, testcase).status, "FAIL");
  assert.equal(verifyScene({
    ...sceneA, performers: [
      { name: "A", urls: ["https://www.trance-video.com/product/search"] },
      { name: "B", urls: ["https://www.trance-video.com/product/search"] },
    ],
  }, testcase).status, "FAIL");
  assert.equal(verifyScene(null, testcase).status, "FAIL");
});

test("mock Stash inventory and two URL scrapes complete, with only sanitized digests", async () => {
  const report = await execute(BASE, { fetchImpl: mocked({ [sourceA]: sceneA, [sourceB]: sceneB }) });
  assert.equal(report.status, "PASS");
  assert.equal(report.results.length, 3);
  assert.equal(report.results[1].status, "PASS");
  assert.equal(report.results[2].status, "PASS");
  assert.match(report.results[1].actual_sha256, /^[a-f0-9]{64}$/);
  assert.doesNotMatch(JSON.stringify(report), /Model A|model%5B%5D=210|API.?Key/i);
});

test("name search to selected detail is asserted without a database write", async () => {
  const report = await execute({ ...BASE, mode: "search" }, { fetchImpl: mocked({}) });
  assert.equal(report.status, "PASS");
  assert.equal(report.results.find((r) => r.id === "E2E-TRANCE-40625").status, "NOT_APPLICABLE");
  assert.equal(report.results.find((r) => r.id === "E2E-TRANCE-40641").status, "PASS");
});

test("network failures and authorization errors are classified BLOCKED without leaking credentials", async () => {
  const unreachable = await execute(BASE, { fetchImpl: async () => { throw Error("s3cr3t"); } });
  assert.equal(unreachable.status, "BLOCKED");
  assert.doesNotMatch(JSON.stringify(unreachable), /s3cr3t/);
  const denied = await execute(BASE, { fetchImpl: async () => new Response("secret", { status: 403 }) });
  assert.equal(denied.status, "BLOCKED");
  assert.doesNotMatch(JSON.stringify(denied), /secret/);
});

test("GraphQL errors and missing scraper are never reported as PASS", async () => {
  const gqlError = await execute(BASE, {
    fetchImpl: async () => new Response(JSON.stringify({ errors: [{ message: "credential leaked" }] })),
  });
  assert.equal(gqlError.status, "FAIL");
  assert.doesNotMatch(JSON.stringify(gqlError), /credential leaked/);
  const missing = await execute(BASE, { fetchImpl: async () => new Response(JSON.stringify({
    data: { version: inventory.version, listScrapers: [] },
  })) });
  assert.equal(missing.status, "FAIL");
  assert.equal(missing.results[1].reason, "SCRAPER_OR_ENTRYPOINT_NOT_LOADED");
});

test("unexpected live values yield a redacted FAIL with field checks", async () => {
  const report = await execute(BASE, { fetchImpl: mocked({ [sourceA]: { ...sceneA, duration: 2545 }, [sourceB]: sceneB }) });
  assert.equal(report.status, "FAIL");
  assert.equal(report.results[1].reason, "GOLDEN_VALUE_MISMATCH");
  assert.equal(report.results[1].checks.find((c) => c.field === "duration").pass, false);
  assert.doesNotMatch(JSON.stringify(report), /2545/);
});
