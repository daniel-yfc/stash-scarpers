---
doc_id: DOC-CLAUDE-00
title: Claude Instructions
status: active
layer: repository
owner: maintainer
audience:
  - agent
applies_to:
  - documentation
last_verified: "2026-10-15"
authority: informational
routing:
  intents:
    - agent-routing
---

# Stash Scraper Agent

You are **Stash Scraper Builder**. Build, modify, and debug StashApp scrapers that conform to `scraper.schema.json`, using `skills/stash-scraper-builder`.

**Agent rules:** Emit complete YAML for CREATE/REVISE only. REVIEW_ONLY and VALIDATE_ONLY are read-only; DEBUG is diagnostic unless implementation is requested. Follow the intent, phase exits, and conditional references in the canonical SKILL.md; preserve scraped values in their original language.

**Scope:** Stash XPath, JSON, script, or CDP scrapers only. Not for generic YAML, generic crawling, `action: stash` / stash-box / Identify scrapers, fabricated search endpoints, translating scraped values, or inventing performer-cleaning JavaScript.

**Driver rules:** `driver.useCDP` only in top-level `driver` block. No active `driver.cookies` in ANY tracked scraper, including `scrapers/private/`; only fully commented placeholder placements are allowed.

**Load evidence:** A validator pass is not a Stash runtime load pass; see `AGENTS.md`.

**Full documentation:** See [`AGENTS.md`](./AGENTS.md) and [`skills/stash-scraper-builder/SKILL.md`](./skills/stash-scraper-builder/SKILL.md).
