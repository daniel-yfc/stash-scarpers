---
doc_id: REF-SEC-30
title: Minimal Secrets Policy
status: active
layer: skill
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-10-15"
authority: informational
routing:
  intents:
    - authentication
---

# Minimal Secrets Policy

## Rules

- Never commit active `driver.cookies`, replayable Cookie / Authorization headers, session tokens, API keys, browser profiles, or copied authentication headers anywhere in this repository. This includes `scrapers/private/`: its name conveys no access control.
- Scraper files may contain **fully commented** cookie placement examples using explicit `<LOCAL_ONLY_VALUE>` placeholders. Never commit captured or plausible real cookie values, even in comments. Cookie names/domains may be documented when non-secret; do not instruct users to uncomment within this repository.
- Use the separately authenticated, isolated, local Chrome profile for `useCDP: true`. Any needed active cookie configuration must stay in an independently access-controlled deployment outside this Git working tree (including untracked files).
- `driver.cookies` must be absent (not merely empty) in all tracked scraper YAML. Never combine active Cookie configuration with CDP.
- Local-only scrutiny may read credentials from its process environment; never put credentials in CLI arguments, committed sidecars, logs, screenshots, build artifacts, or generated reports.
- Screenshots, exported browser data, and copied request headers are sensitive if they expose authenticated session state.

## Repository Controls

- Ensure `.gitignore` excludes local debug artifacts, but do not confuse ignored paths with confidentiality: tracked files remain tracked and history remains public. Keep real profiles, sessions, and deployment copies **outside** this repository.
- Require a blocking, redacted, fail-closed tracked-file scanner and a scraper YAML structural check in CI. Use synthetic negative tests; do not print matched secret values.
- Reviewers must reject **any** repository PR that contains replayable authentication material. If previously exposed, revoke/rotate first, then handle history-remediation separately.

## Review Checklist

- [ ] All tracked files, including `scrapers/private/`, contain no live cookies, tokens or authentication values
- [ ] Every included cookie template is commented and uses explicit placeholders
- [ ] Local deployment copies and Chrome profiles exist outside the Git working tree
- [ ] Scrutiny invocation never places cookies in argv, sidecars, reports or CI artifacts
- [ ] Tracked-file scan, YAML structural gate and negative tests pass
