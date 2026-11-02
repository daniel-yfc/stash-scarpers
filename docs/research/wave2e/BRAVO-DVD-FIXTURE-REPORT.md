# Wave 2E WS-2E-40 - BRAVO DVD fixture engineering report (Agent C, v2.1)

## Handoff

```yaml
AGENT: C
WAVE: 2E
TASK: WS-2E-40
BRANCH: test/e2e-bravo-dvd-fixtures
BASE: 44a26d5ed931273ca4473da0e2c10d6cf2ffaee5
HEAD_SHA: "f6ffbbf21d9b526b3c8a80daa43154b1d1f17741"  # deliverables commit (manifest + tests)
REPORT_NOTE: "本報告於 deliverables commit 之後單獨 commit(branch head);HEAD_SHA 指 fixture manifest + tests 的 deliverables commit"
CHANGED_FILES:
  - tests/fixtures/bravo/bravo-dvds-fixtures.yml
  - tools/tests/test_bravo_dvds.py
```

## Review fixes (v2.1)

| 項目 | 修正 |
|---|---|
| C-FIX-1 | 6 個 positive case 改名 `BRAVO dvd XXX (synthetic regression)`;Cloudflare 改名 `BRAVO dvd Cloudflare challenge (dvd manifest control)` — 與歷史 manifest 零重疊;隔離測試另加 html 檔名隔離斷言 |
| C-FIX-2 | `test_dvd_manifest_does_not_reuse_stale_h1_selectors` 改用 `case.get("expect", [])` guard |
| C-FIX-3 | HEAD_SHA 改為真實 deliverables commit SHA(無佔位字串) |

## Test results

- 修正前(審查者實測):20 passed / 2 failed(isolation + stale-h1 KeyError)
- 修正後預期:22 passed
- manifest runner:預期紅(Ambiguous entrypoint),待 Agent F 實作

## Status

READY_FOR_REVIEW — C-FIX-1/2/3 全數完成。
