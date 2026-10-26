---
doc_id: REF-CORE-00
title: Superseded Skill Read Order
status: archived
layer: skill
owner: maintainer
audience:
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-10-27"
authority: informational
routing:
  intents:
    - archive
---

# DEPRECATED — historical record only

Superseded by `skills/stash-scraper-builder/SKILL.md` on 2026-10-27.
This file is not a runtime route. Do not load it during scraper work.

The former guide required repository documents before opening the skill,
then directed the agent back into SKILL.md. The resulting circular read
order was replaced by a single workflow entry with conditional references.
For historical context, see git history of
`skills/stash-scraper-builder/references/skill-read-order.md`.
