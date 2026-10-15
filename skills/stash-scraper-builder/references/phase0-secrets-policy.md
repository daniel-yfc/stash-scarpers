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

- Never commit cookies, session tokens, API keys, browser profiles, or copied auth headers into public scraper files.
- Keep login-dependent or cookie-based variants in `scrapers/private/` or equivalent private paths.
- If `useCDP: true` is used in a public scraper, remove all cookie-based configuration from that same file.
- Screenshots, exported browser data, and copied request headers are sensitive if they expose authenticated session state.

## Repository Controls

- Verify `.gitignore` covers private scraper paths, browser profile directories, cookies, and local debug artifacts.
- Add a lightweight pre-commit or CI secret scan to catch tokens, cookies, and credential-like strings before merge.
- Reviewers must reject any public scraper PR that contains replayable authentication material.

## Review Checklist

- [ ] Public file contains no cookies, tokens, or login headers
- [ ] Private workflow is documented without exposing reusable secrets
- [ ] CDP and cookie modes are not mixed in the same public scraper variant
