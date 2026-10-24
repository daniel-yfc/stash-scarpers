import assert from "node:assert/strict";
import { test } from "node:test";
import { validateReport, evaluatePilot, parseOptions } from "../check_stash_e2e_evidence.mjs";

const COMMIT = "0123456789abcdef0123456789abcdef01234567";
const HASH = "a".repeat(64);
const BASE = {
  schema_version: 1, executed_at: "2026-10-24T12:00:00Z",
  environment: "test", scraper_commit: COMMIT, stash_version: "v0.31.1",
  production_ready: false,
};
function agent() {
  return {
    ...BASE, executor: "AGENT_API", mode: "golden",
    proof_scope: "LOADER_AND_EXTRACTION", persistence: "UNVERIFIED",
    results: [
      { id: "E2E-LOADER", status: "PASS", loaded_count: 21 },
      { id: "E2E-TRANCE-40625", status: "PASS", checks: [
        { field: "duration", pass: true }, { field: "performerModelIds", pass: true },
      ], actual_sha256: HASH },
      { id: "E2E-TRANCE-40641", status: "PASS", checks: [
        { field: "duration", pass: true },
      ], actual_sha256: HASH },
    ],
    status: "PASS",
  };
}
function manual() {
  function row(id, persistence) {
    return {
      id, status: "PASS", evidence_sha256: HASH,
      checks: {
        loader: "PASS", extraction: "PASS", postprocess: "PASS",
        source_truth: "PASS", identity: id.endsWith("40625") ? "PASS" : "NOT_APPLICABLE",
        persistence,
      },
    };
  }
  return {
    ...BASE, executor: "HUMAN_UI", mode: "manual",
    proof_scope: "HUMAN_VERIFIED", persistence: "PASS",
    results: [
      row("E2E-TRANCE-40625", "PASS"),
      row("E2E-TRANCE-40641", "NOT_APPLICABLE"),
    ],
    status: "PASS",
  };
}

test("agent's extraction report validates but does not pass the human/persistence pilot gate", () => {
  assert.equal(validateReport(agent()).status, "PASS");
  const gate = evaluatePilot([agent()]);
  assert.equal(gate.ready, false);
  assert.ok(gate.reasons.includes("MANUAL_OR_UI_CONFIRMATION_REQUIRED"));
  assert.ok(gate.reasons.includes("TEST_PERSISTENCE_NOT_VERIFIED"));
});

test("manual UI evidence with both Trance cases and verified test persistence passes pilot gate", () => {
  assert.equal(validateReport(manual()).executor, "HUMAN_UI");
  assert.equal(evaluatePilot([manual()]).ready, true);
  assert.equal(evaluatePilot([agent(), manual()]).ready, true);
  assert.equal(evaluatePilot([{ ...manual(), executor: "AGENT_UI" }]).ready, true);
});

test("partial, missing and unverifiable claims never promote a pilot", () => {
  const a = manual();
  a.results[1].status = "UNVERIFIED";
  a.status = "UNVERIFIED";
  assert.equal(validateReport(a).status, "UNVERIFIED");
  assert.ok(evaluatePilot([a]).reasons.includes("E2E-TRANCE-40641_NOT_VERIFIED"));
  const b = manual();
  b.results[0].checks.persistence = "NOT_APPLICABLE";
  b.persistence = "UNVERIFIED";
  assert.ok(evaluatePilot([b]).reasons.includes("TEST_PERSISTENCE_NOT_VERIFIED"));
});

test("production cannot claim persistence or pass a test-instance-only pilot gate", () => {
  const p = manual();
  p.environment = "production";
  p.results.forEach((r) => { r.checks.persistence = "NOT_APPLICABLE"; });
  p.persistence = "NOT_APPLICABLE";
  assert.equal(validateReport(p).environment, "production");
  assert.ok(evaluatePilot([p]).reasons.includes("TEST_INSTANCE_REQUIRED"));
  p.results[0].checks.persistence = "PASS";
  assert.throws(() => validateReport(p), /production/);
});

test("reject hidden secrets, raw data or unreviewed manual PASS fields", () => {
  assert.throws(() => validateReport({ ...agent(), api_key: "secret" }), /unexpected key/);
  assert.throws(() => validateReport({
    ...agent(),
    results: [{ id: "E2E-LOADER", status: "PASS", loaded_count: 21, cookie: "x" }],
  }), /unexpected key/);
  const m = manual();
  m.results[0].checks.source_truth = "UNVERIFIED";
  assert.throws(() => validateReport(m), /source_truth/);
  const n = manual();
  delete n.results[0].evidence_sha256;
  assert.throws(() => validateReport(n), /evidence digest/);
  const o = manual();
  o.results[0].checks.headers = "password";
  assert.throws(() => validateReport(o), /unexpected key/);
});

test("agent FAIL, blocked and malformed outcomes are not mistaken for PASS", () => {
  const a = agent();
  a.results[1].status = "FAIL";
  a.results[1].reason = "GOLDEN_VALUE_MISMATCH";
  a.results[1].checks[0].pass = false;
  a.status = "FAIL";
  assert.equal(validateReport(a).status, "FAIL");
  a.results[1].checks[0].pass = true;
  assert.throws(() => validateReport(a), /mismatch requires failed assertion/);
  const b = agent();
  b.results[1] = { id: "E2E-TRANCE-40625", status: "BLOCKED", reason: "HTTP_STATUS_403" };
  b.status = "BLOCKED";
  assert.equal(validateReport(b).status, "BLOCKED");
  const c = agent();
  c.results[1] = { id: "E2E-TRANCE-40625", status: "FAIL", reason: "API key is xyz" };
  c.status = "FAIL";
  assert.throws(() => validateReport(c), /unexpected reason/);
});

test("revision/version mismatches and duplicate IDs fail contract or pilot", () => {
  const a = agent();
  const m = manual();
  m.scraper_commit = "b".repeat(40);
  assert.ok(evaluatePilot([a, m]).reasons.includes("REVISION_OR_VERSION_MISMATCH"));
  const dup = agent();
  dup.results[2].id = dup.results[1].id;
  assert.throws(() => validateReport(dup), /duplicate/);
  const falseClaim = agent();
  falseClaim.production_ready = true;
  assert.throws(() => validateReport(falseClaim), /production readiness/);
  const fake = agent();
  fake.status = "BLOCKED";
  assert.throws(() => validateReport(fake), /aggregate status mismatch/);
});

test("only explicit report paths and an optional pilot gate flag are supported", () => {
  assert.deepEqual(parseOptions(["--report=/tmp/e2e.json", "--pilot-gate"]), {
    files: ["/tmp/e2e.json"], pilotGate: true,
  });
  assert.throws(() => parseOptions(["--api-key=secret"]), /unsupported/);
  assert.throws(() => parseOptions([]), /report/);
});
