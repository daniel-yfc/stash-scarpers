# Exclusive QA Lease Record — PR #93 Gate B

- Lease ID: GATEB-PR93-LEASE-20261103-01
- Assignment: WAVE2E-D-GATEB-PR93-20261103 (WS-2E-00 / Wave 1B Gate B)
- Granted by: user (repo/environment owner) — one-batch authorization message, 2026-11-03 19:38 Asia/Taipei: 「一次整批授權 M0＋PR #93 獨占 lease，我立即重跑 live Gate B」
- Scope: stash-test ONLY (lxc:9098); M0 preflight items within this run; install PR #93 candidate BRAVO (86e34a2) via isolated package source; run B0(installed)-B6 live cases; restore baseline; release lease.
- Exclusions: production Stash (lxc:9999) untouched; no merge; no other PR candidates; no permanent Scene metadata writes (scrape operations are non-persistent; persistence checks read-only).
- QA owner: Agent D (this session, exclusive — no other agent tasked on stash-test in this window)
- Start: 2026-11-03 19:38 CST (grant) / preflight from ~19:40 CST
- End/release: RELEASED 2026-11-03 evening CST after restore verification (RESTORED_VERIFIED, see v2 report §10)
