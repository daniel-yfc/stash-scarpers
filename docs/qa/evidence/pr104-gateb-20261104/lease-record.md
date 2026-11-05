# Exclusive QA Lease Record — PR #104 Gate B (Phase B)

- Lease ID: GATEB-PR104-LEASE-20261105-01
- Assignment: WAVE2E-D-PR104-GATEB-20261104 (Part B)
- Granted by: user (owner/Controller) instruction 「redo live test via stash-test this part」, 2026-11-05 01:13 Asia/Taipei, in this chat (the M0 report chat). Prior leases for other PRs are NOT reused.
- QA identity: Agent D, this session (exclusive).
- Instance: stash-test ONLY.
- Candidate: PR #104 exact HEAD 3f3b4559349e501fdb57bc053f1efb90400540a4; BRAVO.zip SHA-256 5bc3b2b7656d9c988f3552aaae271883e9a0e303f2c5a9e4c46494b232670ddb (M0-verified rebuild).
- Allowed operations: isolated package source (name gateb-pr104) install/uninstall of BRAVO only; configureGeneral scraperPackageSources add/remove of that isolated source; reloadScrapers; scrape-only GraphQL (scrapeSceneURL, scrapeSingleScene, listScrapers, installedPackages, availablePackages, version/stats/configuration reads). NO Scene writes, NO other packages, NO production access.
- CDP: Stash's own driver use (scraperCDPPath fixed /json/version form). QA does not create/close CDP targets directly.
- Rollback ruling (per M0-03 open item, applied with this go-ahead): isolated-source rollback + 5-way before/after comparison is the rollback method (PR #93 precedent); DB backup restore drill not required for this scrape-only run. Baseline BRAVO b92acdd from yfc source is the restore target.
- Evidence: sanitized GraphQL request/response JSON under live/evidence; no credentials/tokens/target URLs recorded.
- Window: from grant until restoration verified and lease released in this session.
