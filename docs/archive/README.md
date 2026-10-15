---
doc_id: DOC-ARCHIVE-00
title: Archive README
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - documentation
last_verified: "2026-10-15"
authority: informational
routing:
  intents:
    - documentation
    - archive
---

# Archive

Historical evidence and record-type documents whose durable findings have been
extracted into normative policy documents or skill references.

Per the repository documentation architecture: evidence that needs to persist
belongs in canonical docs; point-in-time reports live here with `status: archived`.

Do not add new active documents here. Archive by moving the file, updating its
front matter `status` to `archived`, and updating `docs/index.yml` accordingly.
