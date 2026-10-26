---
doc_id: DOC-TEST-53
title: Skill Evaluation Contract and Host Evidence
status: active
layer: repository
owner: maintainer
audience:
  - maintainer
applies_to:
  - testing
  - skills
last_verified: "2026-10-27"
authority: canonical
routing:
  intents:
    - skill-evaluation
    - trigger-tests
    - workflow-exit
---

# Skill Evaluation — deterministic checks vs real host evidence

This is a **maintainer testing procedure**, not a runtime Skill instruction. The only scraper Skill entry remains `skills/stash-scraper-builder/SKILL.md`. Evaluation prompts and recorded results are outside its runtime directory.

## Scope and corpus

| Suite | Number | Contract |
| --- | ---: | --- |
| `stash-scraper-builder-trigger-cases.json` | 20 | Ten positive/ten negative baseline triggers |
| `near-miss-cases.json` | 10 | Ambiguous neighboring task boundaries |
| `workflow-stop-cases.json` | 10 | No-write, P0–P6 stop rules and forbidden evidence promotion |
| `functional-cases.json` | 5 | Legacy XPath, JSON, script, date-fix and gated/CDP authoring tasks |

The historical five-task notes are at [`legacy-functional-eval.md`](../tests/skill-evals/legacy-functional-eval.md). They are **case requirements**, not a 5/5 pass. Every case has a stable ID, expected intent, and, where needed, stop phase and required evidence axis. The manifest requires **three independent attempts per pinned host/model combination**. Do not edit expected outcomes after seeing results; revise the corpus separately, retaining prior version provenance.

## Deterministic automated gates

From the repository root:

```sh
python tools/evals/validate_cases.py --json
python -m pytest tools/tests/test_skill_eval.py -v
python tools/check_docs_index.py
python tools/check_resource_placement.py
```

`.github/workflows/skill-eval-contract.yml` runs these checks for Skill/Eval changes on pull requests **regardless of base branch**, plus qualifying `main` pushes and manual workflow dispatch. It cannot run Codex, OpenCode, Qwen Code, Stash, real Chrome CDP, or authenticate external trace origin. Green CI establishes **CORPUS_VALIDATED_ONLY** and synthetic evaluator regression, never HOST_EVAL_PASSED.

## Host evaluation procedure

For every host being claimed:

1. Pin the **full Git repository SHA**, Skill content SHA-256, host build/version, actual model name/version, and tool permissions. Do not use `latest` or a floating prompt/Skill version.
2. Install the canonical Skill using that host's supported discovery path. Verify which copy/version loads; beware duplicate/shadowed ids.
3. Run every case **three times** in isolated fresh contexts. Capture *actual* Skill-load events, selected intent, P0–P6 exits, tool actions (including whether any write was attempted), verification steps, and negative/near-miss behavior. Do not record only the final answer.
4. Repeat appropriate controls with the Skill **unavailable**, record token/time cost, and compare the observed change in outcomes. Keep control and with-Skill results distinct.
5. Export sanitized host event traces to an untracked restricted `logs/skill-evals/traces/` directory. Name each file `<CASE_ID>--<host>--<repeat>.json` (for example `STOP-02--codex--1.json`). Never commit traces or any authentication/session data.
6. Use the offline scorer and review the **original, authenticated host evidence** independently. A JSON file labeled `host_export` is not cryptographic authentication or an attestation.

Example **synthetic format only** (not host evidence):

```json
{
  "case_id": "POS-01",
  "host": "codex",
  "repeat": 1,
  "repo_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "skill_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "host_version": "synthetic-1",
  "model": "synthetic-test-model",
  "capture_kind": "synthetic_fixture",
  "event_capture_complete": true,
  "events": [
    {
      "type": "skill_load",
      "skill_id": "stash-scraper-builder",
      "path": "skills/stash-scraper-builder/SKILL.md"
    },
    {"type": "intent", "value": "CREATE"},
    {"type": "phase_exit", "phase": "P0", "status": "PASS"}
  ]
}
```

Required event kinds are `skill_load`, `intent`, `phase_exit`, `tool_action` (classified READ/WRITE/DESTRUCTIVE), and `verification`. Any claimed verification PASS must include a nonempty artifact reference and its 64-character SHA-256. The offline scorer rejects self-declared top-level verdicts, revision/Skill mismatches, unsupported evidence, missing tool-capture assertions, unsafe session material, prohibited writes and downstream phase promotions. **A fully self-authored synthetic event list can satisfy structural conditions, but it never proves a host ran it.**

```sh
python tools/evals/evaluate_traces.py --host codex --repo-sha "$(git rev-parse HEAD)" --trace-dir logs/skill-evals/traces --output logs/skill-evals/codex-offline-report.json
```

The report status is always `OFFLINE_TRACE_ASSESSMENT_ONLY`; `source_trust` is `SYNTHETIC_FIXTURE`, `HOST_EXPORT_UNATTESTED`, or `MISSING`. Running with `--require-complete` deliberately exits 2 until independent Host provenance authentication is provided outside this scorer. **This is a fail-closed boundary, not missing automation disguised as a pass.**

## Acceptance thresholds (never silently relaxed)

- **F0 corpus:** 45 valid/unique cases, correct manifest binding, 3 repetitions per claimed host.
- **F1 positive trigger:** per host at least **95%** actual canonical Skill loads and correct intents.
- **F2 negative/near-miss:** per host at least **95%** correct exclusion; every security-sensitive boundary case **100%**.
- **F3 critical workflow-stop:** **100%**, including no-write and blocked/failed downstream evidence.
- **F4 functional tasks:** all five tasks individually verified at the required axes to claim `5/5`. Stash Loader, site value match and CDP require actual compatible runtime evidence.
- **F5 reproducibility:** each claimed result has pinned SHA/model/host, actual capture, reference/digest, and independent review.

Keep per-host scores separately; never transfer Codex evidence to OpenCode/Qwen Code. Report `NOT_RUN` or `BLOCKED` when no host/Stash runtime is available, and never confuse a fixture self-test with site fixture or Stash/CDP evidence.

## Security and maintenance

No real Cookie, Authorization, CSRF, session token, local browser profile, page dump containing session data, or unredacted raw host conversation belongs in any case, log or committed report. Traces are gitignored; review the redaction and artifact source before accepting them. An offline digest assures only bytes have not changed, not that the bytes originated from a host. See [repository testing guide](50-testing-guide.md) for other verification layers.
