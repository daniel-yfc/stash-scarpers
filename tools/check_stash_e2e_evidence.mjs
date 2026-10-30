#!/usr/bin/env node
// Local-only audit of sanitized Stash E2E results. Never contacts Stash or Tailnet.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const STATUSES = new Set(["PASS", "FAIL", "BLOCKED", "UNVERIFIED", "NOT_APPLICABLE"]);
const HEX40 = /^[a-f0-9]{40}$/i;
const HEX64 = /^[a-f0-9]{64}$/i;
const SAFE_ID = /^E2E-[A-Z0-9-]{2,72}$/;
const SAFE_FIELD = /^[A-Za-z][A-Za-z0-9._-]{0,75}$/;
const REASONS = new Set([
  "GOLDEN_VALUE_MISMATCH", "SCRAPER_OR_ENTRYPOINT_NOT_LOADED",
  "NO_COMMITTED_SEARCH_CASE", "SEARCH_RESULTS_INVALID",
  "SEARCH_SELECTION_NOT_UNAMBIGUOUS", "DETAIL_RESULT_NOT_UNAMBIGUOUS",
  "UNKNOWN_CASE_ID", "INVALID_INVENTORY_RESPONSE", "STASH_VERSION_MISMATCH",
  "NETWORK_OR_TIMEOUT (details intentionally redacted)", "INVALID_GRAPHQL_RESPONSE",
  "GRAPHQL_ERRORS_PRESENT", "GRAPHQL_DATA_MISSING", "UNEXPECTED_INVENTORY_ERROR",
  "UNEXPECTED_SCRAPE_ERROR",
]);

function error(message) { throw Error(message); }
function keysExactly(obj, allowed, where) {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) error(where + ": expected object");
  for (const key of Object.keys(obj)) if (!allowed.includes(key)) error(where + ": unexpected key");
}
function resultStatus(statuses) {
  const applicable = statuses.filter((s) => s !== "NOT_APPLICABLE");
  return !applicable.length ? "UNVERIFIED"
    : applicable.includes("FAIL") ? "FAIL"
    : applicable.includes("BLOCKED") ? "BLOCKED"
    : applicable.every((s) => s === "PASS") ? "PASS" : "UNVERIFIED";
}
function mustStatus(value, label) {
  if (!STATUSES.has(value)) error(label + ": unknown status");
}
function validTimestamp(value) {
  return typeof value === "string" && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(value)
    && Number.isFinite(Date.parse(value));
}
function validateAgentResult(row) {
  keysExactly(row, ["id", "status", "reason", "checks", "actual_sha256", "loaded_count"], "agent result");
  if (row.id === "E2E-LOADER") {
    if (row.status === "PASS" && (!Number.isInteger(row.loaded_count) || row.loaded_count < 0)) {
      error("loader PASS requires loaded_count");
    }
    if (row.checks !== undefined || row.actual_sha256 !== undefined) error("loader may not claim data extraction");
  } else if (row.status === "PASS" || row.reason === "GOLDEN_VALUE_MISMATCH") {
    if (!Array.isArray(row.checks) || !row.checks.length) error("extraction requires field checks");
    const names = new Set();
    for (const check of row.checks) {
      keysExactly(check, ["field", "pass"], "field assertion");
      if (!SAFE_FIELD.test(check.field) || typeof check.pass !== "boolean" || names.has(check.field)) error("invalid field assertion");
      names.add(check.field);
    }
    if (row.status === "PASS" && !HEX64.test(row.actual_sha256 || "")) error("PASS requires sanitized digest");
    if (row.actual_sha256 !== undefined && !HEX64.test(row.actual_sha256)) error("invalid digest");
    if (row.status === "PASS" && !row.checks.every((check) => check.pass)) error("PASS with failing assertions");
    if (row.reason === "GOLDEN_VALUE_MISMATCH" && !row.checks.some((check) => !check.pass)) {
      error("mismatch requires failed assertion");
    }
  } else if (row.checks !== undefined || row.actual_sha256 !== undefined) {
    error("non-extraction result must not include field values");
  }
}
function validateHumanResult(row, report) {
  keysExactly(row, ["id", "status", "checks", "evidence_sha256"], "human result");
  const checks = row.checks;
  keysExactly(checks, ["loader", "extraction", "postprocess", "source_truth", "identity", "persistence"], "manual checks");
  for (const key of ["loader", "extraction", "postprocess", "source_truth", "identity", "persistence"]) {
    mustStatus(checks[key], "manual " + key);
  }
  if (report.environment === "production" && checks.persistence !== "NOT_APPLICABLE") {
    error("production cannot claim a persistence operation");
  }
  if (row.status === "PASS") {
    for (const key of ["loader", "extraction", "postprocess", "source_truth"]) {
      if (checks[key] !== "PASS") error("manual PASS requires completed " + key);
    }
    if (!["PASS", "NOT_APPLICABLE"].includes(checks.identity)) error("manual PASS requires identity review");
    if (!["PASS", "NOT_APPLICABLE"].includes(checks.persistence)) error("manual PASS requires explicit persistence disposition");
    if (!HEX64.test(row.evidence_sha256 || "")) error("manual PASS requires evidence digest");
  }
  if (row.evidence_sha256 !== undefined && !HEX64.test(row.evidence_sha256)) {
    error("invalid manual evidence digest");
  }
}
export function validateReport(report) {
  keysExactly(report, [
    "schema_version", "executed_at", "executor", "environment", "mode",
    "scraper_commit", "stash_version", "results", "status",
    "proof_scope", "persistence", "production_ready",
  ], "report");
  if (report.schema_version !== 1 || !validTimestamp(report.executed_at)) error("invalid evidence version or timestamp");
  if (!["AGENT_API", "AGENT_UI", "HUMAN_UI"].includes(report.executor)) error("invalid executor");
  if (!["test", "production"].includes(report.environment)) error("invalid environment");
  if (!HEX40.test(report.scraper_commit || "")) error("missing pinned scraper commit");
  if (typeof report.stash_version !== "string" || !/^v?\d+\.\d+\.\d+(?:[-+.][A-Za-z0-9.-]+)?$/.test(report.stash_version)) {
    error("missing exact Stash version");
  }
  if (report.production_ready !== false) error("evidence report cannot claim production readiness");
  if (!Array.isArray(report.results) || !report.results.length) error("missing results");
  const ids = new Set();
  for (const row of report.results) {
    if (!row || !SAFE_ID.test(row.id || "") || ids.has(row.id)) error("invalid or duplicate result ID");
    ids.add(row.id);
    mustStatus(row.status, "result");
    if (report.executor === "AGENT_API") {
      if (row.reason !== undefined && !REASONS.has(row.reason) && !/^HTTP_STATUS_\d{3}$/.test(row.reason)) {
        error("unexpected reason (may contain sensitive details)");
      }
      validateAgentResult(row);
    } else {
      validateHumanResult(row, report);
    }
  }
  if (report.executor === "AGENT_API") {
    if (!["inventory", "golden", "search"].includes(report.mode)
        || report.proof_scope !== (report.mode === "inventory" ? "LOADER_ONLY" : "LOADER_AND_EXTRACTION")
        || report.persistence !== "UNVERIFIED") error("invalid agent proof boundaries");
    if (report.results[0].id !== "E2E-LOADER") error("agent report must start with loader");
  } else {
    if (report.mode !== "manual" || report.proof_scope !== "HUMAN_VERIFIED") {
      error("invalid human/agent UI proof boundary");
    }
    if (!["PASS", "NOT_APPLICABLE", "UNVERIFIED"].includes(report.persistence)) error("invalid persistence aggregate");
    const hasPersistence = report.results.some((row) => row.status === "PASS" && row.checks.persistence === "PASS");
    if (report.environment === "production" && report.persistence !== "NOT_APPLICABLE") {
      error("production persistence is forbidden");
    }
    if (report.environment === "test" && (hasPersistence !== (report.persistence === "PASS"))) {
      error("persistence aggregate does not match manual checks");
    }
  }
  if (report.status !== resultStatus(report.results.map((row) => row.status))) error("aggregate status mismatch");
  return { executor: report.executor, status: report.status, mode: report.mode,
    environment: report.environment, scraper_commit: report.scraper_commit, stash_version: report.stash_version };
}

export function evaluatePilot(reports) {
  if (!reports.length) return { ready: false, reasons: ["NO_REPORTS"] };
  for (const r of reports) validateReport(r);
  const commits = new Set(reports.map((r) => r.scraper_commit));
  const versions = new Set(reports.map((r) => r.stash_version));
  const reasons = [];
  if (commits.size !== 1 || versions.size !== 1) reasons.push("REVISION_OR_VERSION_MISMATCH");
  if (reports.some((r) => r.environment !== "test")) reasons.push("TEST_INSTANCE_REQUIRED");
  if (reports.some((r) => ["FAIL", "BLOCKED", "UNVERIFIED"].includes(r.status))) {
    reasons.push("INCOMPLETE_OR_FAILED_REPORT");
  }
  const manual = reports.filter((r) => ["HUMAN_UI", "AGENT_UI"].includes(r.executor));
  if (!manual.length) reasons.push("MANUAL_OR_UI_CONFIRMATION_REQUIRED");
  for (const id of ["E2E-TRANCE-40625", "E2E-TRANCE-40641"]) {
    if (!manual.some((r) => r.results.some((c) =>
      c.id === id && c.status === "PASS" && c.checks.extraction === "PASS"
      && c.checks.source_truth === "PASS" && c.checks.postprocess === "PASS"
      && (id !== "E2E-TRANCE-40625" || c.checks.identity === "PASS")))) {
      reasons.push(id + "_NOT_VERIFIED");
    }
  }
  if (!manual.some((r) => r.results.some((c) => c.status === "PASS" && c.checks.persistence === "PASS"))) {
    reasons.push("TEST_PERSISTENCE_NOT_VERIFIED");
  }
  return { ready: reasons.length === 0, reasons };
}

export function parseOptions(argv) {
  const options = { files: [], pilotGate: false };
  for (const option of argv) {
    if (option.startsWith("--report=")) options.files.push(option.slice("--report=".length));
    else if (option === "--pilot-gate") options.pilotGate = true;
    else error("unsupported evidence command option");
  }
  if (!options.files.length) error("at least one --report=PATH required");
  return options;
}
function loadReport(file) {
  const stats = fs.statSync(file);
  if (!stats.isFile() || stats.size > 1_000_000) error("invalid report file");
  return JSON.parse(fs.readFileSync(file, "utf8"));
}
function main() {
  try {
    const { files, pilotGate } = parseOptions(process.argv.slice(2));
    const reports = files.map(loadReport);
    const results = reports.map(validateReport);
    const gate = pilotGate ? evaluatePilot(reports) : { ready: false, reasons: ["PILOT_GATE_NOT_REQUESTED"] };
    console.log(JSON.stringify({
      reports_validated: results.length,
      by_status: Object.fromEntries([...new Set(results.map((r) => r.status))].map((s) => [s, results.filter((r) => r.status === s).length])),
      pilot_gate: gate.ready ? "PASS" : "NOT_READY",
      reasons: gate.reasons,
      production_ready: false,
    }));
    if (pilotGate && !gate.ready) process.exitCode = 1;
  } catch {
    // Avoid printing invalid JSON fields or file contents; they could contain secrets.
    console.error("E2E_EVIDENCE_INVALID: report/schema/permission check failed (contents suppressed)");
    process.exitCode = 2;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
