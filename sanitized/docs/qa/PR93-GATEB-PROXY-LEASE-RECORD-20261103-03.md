# Exclusive QA Lease Record — PR #93 Gate B Proxy Re-run (lease -03)

- Lease ID: GATEB-PR93-LEASE-20261103-03
- Assignment: WAVE2E-D-PR93-GATEB-PROXY-EXEC-20261103 (Proxy QA Runner execution; verdict reserved to Agent D)
- Granted by: user (owner) instruction 「我要核發新 lease -03，照 Proxy 規格完整重跑」, 2026-11-03 22:50 Asia/Taipei, in chat ace76ce3 (Stash Live E2E thread)
- Scope: stash-test ONLY; install PR #93 candidate at frozen HEAD ce7ef6c8f5c5663f41295e92a0603bca486abe98 via isolated source; Proxy spec B0–B6 (B1/B2 = 3 independent scrapes per page); restore baseline; release.
- Prior runs: lease -01 @86e34a2 → GATE_B_FAIL (DEF-01, DEF-02); lease -02 @ce7ef6c → GATE_B_FAIL (DEF-01 only), both restored verified and released. This lease -03 is a NEW grant for the Proxy-format re-run; earlier results are not reused as evidence for this run.
- QA owner: Proxy QA Runner (this session, exclusive)
- Start: 2026-11-03 22:50 CST (grant)
- End/release: RELEASED 2026-11-04 00:43 CST after restore verification (post-rollback snapshot equal to pre-test snapshot on version/stats/sources/scraping-config/packages; BRAVO back to b92acdd from yfc; isolated source gateb-pr93-r3 removed). Evidence: ~/workspace/qa-pr93-gateb-proxy-20261103/ (Proxy §9 layout + MANIFEST-LIVE.sha256 + zip). Verdict: reserved to Agent D (proxy role makes no PASS/FAIL call).
