#!/usr/bin/env node
// Stash v0.31.1 read-only GraphQL E2E. No mutations or credential logging.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const GOLDEN_PATH = path.join(ROOT, "tests/e2e/stash-golden.json");
const INVENTORY_QUERY = `query E2EInventory {
  version { version hash }
  listScrapers(types: [SCENE, PERFORMER]) {
    id name
    scene { urls supported_scrapes }
    performer { urls supported_scrapes }
  }
}`;
const SCENE_QUERY = `query E2EScene($url: String!) {
  scrapeSceneURL(url: $url) {
    title code date duration urls
    performers { name urls }
    studio { name urls }
    tags { name }
  }
}`;
const SEARCH_QUERY = `query E2ESearch($source: ScraperSourceInput!, $input: ScrapeSingleSceneInput!) {
  scrapeSingleScene(source: $source, input: $input) {
    title code date duration urls
    performers { name urls }
  }
}`;
export const QUERIES = Object.freeze({ INVENTORY_QUERY, SCENE_QUERY, SEARCH_QUERY });

class E2EError extends Error {
  constructor(message, status = "FAIL") { super(message); this.status = status; }
}

export function parseArguments(argv) {
  const options = {};
  for (const arg of argv) {
    const match = /^--(mode|env|report|case|expected-version)=(.+)$/.exec(arg);
    if (match) { options[match[1]] = match[2]; continue; }
    if (arg === "--live") { options.live = true; continue; }
    if (arg === "--allow-production-read") { options.productionRead = true; continue; }
    throw new E2EError("Unknown CLI option; see docs/81-stash-e2e-runbook.md");
  }
  return options;
}

export function validateConfiguration(config) {
  if (!["test", "production"].includes(config.env)) {
    throw new E2EError("Explicit --env=test|production is required");
  }
  if (!["inventory", "golden", "search"].includes(config.mode)) {
    throw new E2EError("Explicit --mode=inventory|golden|search is required");
  }
  if (config.env === "production" && !config.productionRead) {
    throw new E2EError("Production requires --allow-production-read");
  }
  if (config.mode !== "inventory" && !config.live) {
    throw new E2EError("Live external scraping requires --live");
  }
  if (!config.baseURL) throw new E2EError("STASH_BASE_URL is required");
  let endpoint;
  try {
    const url = new URL(config.baseURL);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
      throw new Error("invalid URL");
    }
    // Never include secrets in the URL. Allow Tailnet HTTP only by operator choice.
    if (url.pathname !== "/" && url.pathname !== "/graphql") {
      throw new Error("path is not GraphQL");
    }
    if (url.protocol === "http:" && !config.allowPrivateHTTP) {
      const h = url.hostname.replace(/^\[|\]$/g, "");
      if (!["localhost", "127.0.0.1", "::1"].includes(h)) {
        throw new Error("private HTTP requires explicit permission");
      }
    }
    url.pathname = "/graphql";
    endpoint = url.toString();
  } catch {
    throw new E2EError("Use HTTPS STASH_BASE_URL or an explicitly allowed private HTTP endpoint (no URL credentials)");
  }
  const commit = config.commit;
  if (!/^[a-f0-9]{40}$/i.test(commit || "")) {
    throw new E2EError("STASH_COMMIT_SHA (full Git commit) is required for traceability");
  }
  if (!config.report || !path.isAbsolute(config.report)) {
    throw new E2EError("Provide an absolute --report=/private/path/e2e-results.json");
  }
  if (path.resolve(config.report).startsWith(path.join(ROOT, "docs") + path.sep)) {
    throw new E2EError("Do not write runtime evidence directly into tracked documentation");
  }
  return { ...config, endpoint };
}

export async function graphql(query, variables, config, fetchImpl = fetch) {
  let response;
  try {
    response = await fetchImpl(config.endpoint, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(config.apiKey ? { ApiKey: config.apiKey } : {}),
      },
      body: JSON.stringify({ query, variables }),
      redirect: "error", // no credential-bearing redirects
      signal: AbortSignal.timeout(30000),
    });
  } catch {
    throw new E2EError("NETWORK_OR_TIMEOUT (details intentionally redacted)", "BLOCKED");
  }
  if (!response.ok) {
    const status = [401, 403, 429].includes(response.status) ? "BLOCKED" : "FAIL";
    throw new E2EError("HTTP_STATUS_" + response.status, status);
  }
  let payload;
  try {
    const raw = await response.text();
    if (raw.length > 5_000_000) throw new Error("oversized");
    payload = JSON.parse(raw);
  } catch {
    throw new E2EError("INVALID_GRAPHQL_RESPONSE");
  }
  if (payload?.errors?.length) {
    // GraphQL errors may contain URLs, query params, local paths, or tokens.
    throw new E2EError("GRAPHQL_ERRORS_PRESENT");
  }
  if (!payload || typeof payload.data !== "object" || payload.data === null) {
    throw new E2EError("GRAPHQL_DATA_MISSING");
  }
  return payload.data;
}

function normalized(value) {
  return JSON.stringify(value ?? null);
}

export function verifyScene(actual, testcase) {
  if (!actual || typeof actual !== "object") return { status: "FAIL", checks: [{ field: "scene", pass: false }] };
  const checks = [];
  for (const [field, expected] of Object.entries(testcase.expected)) {
    checks.push({ field, pass: normalized(actual[field]) === normalized(expected) });
  }
  if (testcase.performerModelIds) {
    const identities = (actual.performers || []).flatMap((p) =>
      (p.urls || []).flatMap((href) => {
        try {
          const url = new URL(href);
          return url.searchParams.getAll("model[]");
        } catch { return []; }
      }),
    );
    checks.push({
      field: "performerModelIds",
      pass: new Set(identities).size === testcase.performerModelIds.length
        && testcase.performerModelIds.every((id) => identities.includes(id)),
    });
  }
  const digestInput = {
    title: actual.title, code: actual.code, date: actual.date,
    duration: actual.duration, urls: actual.urls,
    performers: actual.performers?.map((p) => ({ name: p.name, urls: p.urls })),
  };
  return {
    status: checks.every((check) => check.pass) ? "PASS" : "FAIL",
    checks,
    actual_sha256: createHash("sha256").update(JSON.stringify(digestInput)).digest("hex"),
    // Deliberately omit raw titles, URLs, HTML, images and error messages.
  };
}

export async function execute(config, { fetchImpl = fetch, cases = null } = {}) {
  const safe = validateConfiguration(config);
  const golden = cases || JSON.parse(fs.readFileSync(GOLDEN_PATH, "utf8")).cases;
  const report = {
    schema_version: 1, executed_at: new Date().toISOString(),
    executor: "AGENT_API", environment: safe.env, mode: safe.mode,
    scraper_commit: safe.commit, stash_version: null,
    results: [],
  };
  function record(id, status, reason, extras = {}) {
    report.results.push({ id, status, ...(reason ? { reason } : {}), ...extras });
  }
  let inventory;
  try {
    inventory = await graphql(INVENTORY_QUERY, {}, safe, fetchImpl);
    report.stash_version = inventory.version?.version || null;
    if (!report.stash_version || !Array.isArray(inventory.listScrapers)) {
      throw new E2EError("INVALID_INVENTORY_RESPONSE");
    }
    if (safe.expectedVersion &&
        report.stash_version.replace(/^v/, "") !== safe.expectedVersion.replace(/^v/, "")) {
      throw new E2EError("STASH_VERSION_MISMATCH");
    }
    record("E2E-LOADER", "PASS", null, { loaded_count: inventory.listScrapers.length });
  } catch (error) {
    record("E2E-LOADER", error.status || "FAIL", error.message instanceof String ? error.message : String(error.message).slice(0, 100));
    return finish(report);
  }
  if (safe.mode === "inventory") return finish(report);

  for (const testcase of golden.filter((c) => !safe.caseId || c.id === safe.caseId)) {
    const loaded = inventory.listScrapers.find((item) => item.name === testcase.scraper);
    if (!loaded || !loaded.scene?.supported_scrapes?.includes(safe.mode === "search" ? "NAME" : "URL")) {
      record(testcase.id, "FAIL", "SCRAPER_OR_ENTRYPOINT_NOT_LOADED");
      continue;
    }
    if (safe.mode === "search" && !testcase.searchQuery) {
      record(testcase.id, "NOT_APPLICABLE", "NO_COMMITTED_SEARCH_CASE");
      continue;
    }
    try {
      let scene;
      if (safe.mode === "golden") {
        const data = await graphql(SCENE_QUERY, { url: testcase.sourceUrl }, safe, fetchImpl);
        scene = data.scrapeSceneURL;
      } else {
        const data = await graphql(SEARCH_QUERY, {
          source: { scraper_id: loaded.id }, input: { query: testcase.searchQuery },
        }, safe, fetchImpl);
        const candidates = data.scrapeSingleScene;
        if (!Array.isArray(candidates)) throw new E2EError("SEARCH_RESULTS_INVALID");
        const selected = candidates.filter((c) => Array.isArray(c.urls) && c.urls.includes(testcase.sourceUrl));
        if (selected.length !== 1) throw new E2EError("SEARCH_SELECTION_NOT_UNAMBIGUOUS");
        const detail = await graphql(SEARCH_QUERY, {
          source: { scraper_id: loaded.id }, input: { scene_input: { urls: [testcase.sourceUrl] } },
        }, safe, fetchImpl);
        if (!Array.isArray(detail.scrapeSingleScene) || detail.scrapeSingleScene.length !== 1) {
          throw new E2EError("DETAIL_RESULT_NOT_UNAMBIGUOUS");
        }
        scene = detail.scrapeSingleScene[0];
      }
      const verified = verifyScene(scene, testcase);
      record(testcase.id, verified.status, verified.status === "FAIL" ? "GOLDEN_VALUE_MISMATCH" : null, {
        checks: verified.checks, actual_sha256: verified.actual_sha256,
      });
    } catch (error) {
      record(testcase.id, error.status || "FAIL", error.message instanceof String ? error.message : String(error.message).slice(0, 100));
    }
  }
  if (safe.caseId && !report.results.some((r) => r.id === safe.caseId)) {
    record(safe.caseId, "FAIL", "UNKNOWN_CASE_ID");
  }
  return finish(report);
}

function finish(report) {
  const checks = report.results.map((r) => r.status);
  report.status = checks.every((s) => s === "PASS") ? "PASS"
    : checks.includes("FAIL") ? "FAIL"
    : checks.includes("BLOCKED") ? "BLOCKED" : "UNVERIFIED";
  return report;
}

function discoverCommit() {
  if (process.env.STASH_COMMIT_SHA) return process.env.STASH_COMMIT_SHA;
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8", timeout: 3000 }).trim();
  } catch { return null; }
}

async function main() {
  const args = parseArguments(process.argv.slice(2));
  const config = {
    mode: args.mode, env: args.env, live: Boolean(args.live),
    productionRead: Boolean(args.productionRead),
    allowPrivateHTTP: process.env.STASH_ALLOW_PRIVATE_HTTP === "1",
    baseURL: process.env.STASH_BASE_URL,
    apiKey: process.env.STASH_API_KEY,
    commit: discoverCommit(), expectedVersion: args["expected-version"] || "v0.31.1",
    report: args.report, caseId: args.case,
  };
  const report = await execute(config);
  fs.mkdirSync(path.dirname(config.report), { recursive: true, mode: 0o700 });
  fs.writeFileSync(config.report, JSON.stringify(report, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  console.log(JSON.stringify({
    status: report.status, environment: report.environment, mode: report.mode,
    stash_version: report.stash_version, cases: report.results.map((r) => ({ id: r.id, status: r.status })),
    report_written: true,
  }));
  if (report.status !== "PASS") process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => {
    console.error("E2E configuration or report write failed; no sensitive details printed.");
    process.exitCode = 2;
  });
}
