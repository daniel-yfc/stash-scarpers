# Exclusive QA Lease Record — PR #93 Gate B Revised Duration Scope (omission candidate)

- Lease ID: GATEB-PR93-LEASE-20261104-02
- Assignment: WAVE2E-D-PR93-DURATION-DEFER-GATEB-20261104 (Independent QA, executed in chat ace76ce3 per user designation)
- Granted by: user (owner) instruction 「在這裡核發新 lease，我立即照修訂矩陣執行」, 2026-11-04 12:25 Asia/Taipei
- Scope: stash-test ONLY; install PR #93 candidate at HEAD 88d27a5764c30fec1ab8bb5a325382e72a2ef09e (package version f4be5cf, BRAVO.zip SHA-256 004ef0679152fc954822ebadaaf534c050ec2a2fb3e710612d7e6280a863dbcf) via isolated source gateb-pr93-r4; revised live matrix (Duration null = expected under WS-2E-DEF01-DEFER-20261104; all retained fields must not regress); restore baseline; release.
- Prior leases (20261103-01/-02/-03, 20261104-01) all released; none reused. (Note: ID -02 chosen because GATEB-PR93-LEASE-20261104-01 was Agent D's v4 focused-run lease, already released.)
- QA owner: this session (exclusive)
- Start: 2026-11-04 12:25 CST (grant)
- End/release: RELEASED 2026-11-04 after restore verification (post-rollback snapshot equal to pre-test snapshot on version/stats/sources/scraping-config/packages, 5/5; BRAVO back to b92acdd from yfc; isolated source gateb-pr93-r4 removed). Verdict: GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE (see report in this workspace).
