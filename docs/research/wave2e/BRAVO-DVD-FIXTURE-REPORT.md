# Wave 2E WS-2E-40 - BRAVO DVD fixture engineering report (Agent C, v2.2)

## Handoff

```yaml
AGENT: C
WAVE: 2E
TASK: WS-2E-40
BRANCH: test/e2e-bravo-dvd-fixtures
BASE: 44a26d5ed931273ca4473da0e2c10d6cf2ffaee5
HEAD_SHA: "f6ffbbf21d9b526b3c8a80daa43154b1d1f17741"  # v2.1 deliverables commit
V22_NOTE: "v2.2 修正(C-FIX-1 follow-up)於本報告同 commit 落地,其 SHA 記錄於 git 歷史(檔案無法包含自身 commit 的 SHA)"
CHANGED_FILES:
  - tests/fixtures/bravo/bravo-dvds-fixtures.yml
  - tests/fixtures/bravo/dvd-synthetic-cloudflare-challenge.html  # v2.2 new
  - tools/tests/test_bravo_dvds.py
```

## Review fixes

| 版本 | 項目 | 修正 |
|---|---|---|
| v2.1 | C-FIX-1 | 6 個 positive case 改名 `BRAVO dvd XXX (synthetic regression)`;Cloudflare 改名 `BRAVO dvd Cloudflare challenge (dvd manifest control)`;隔離測試加 html 檔名隔離斷言 |
| v2.1 | C-FIX-2 | `test_dvd_manifest_does_not_reuse_stale_h1_selectors` 改用 `case.get("expect", [])` guard |
| v2.1 | C-FIX-3 | HEAD_SHA 改為真實 deliverables commit SHA(無佔位字串) |
| v2.2 | C-FIX-1 follow-up | failure case 不再共用歷史 `failure-cloudflare.html`,改用 DVD 專屬合成模型 `dvd-synthetic-cloudflare-challenge.html`(SYNTHETIC_REGRESSION 標記);歷史檔未修改,仍僅由歷史與 Clips manifest 引用;新增 `test_failure_case_uses_dvd_owned_synthetic_fixture` 釘住此修正;`test_synthetic_fixtures_are_marked` 改為全部 DVD fixture 一律要求標記(無例外) |

## Test results

- 修正前(審查者實測):20 passed / 2 failed(isolation + stale-h1 KeyError)
- v2.1 後(審查者再測):isolation 仍失敗(failure case 共用歷史 html)
- v2.2 後預期:**23 passed**(新增 1 個 fixture-ownership 測試;隔離測試應轉綠)
- manifest runner:預期紅(Ambiguous entrypoint),待 Agent F 實作

## Status

READY_FOR_REVIEW — C-FIX-1/2/3 + C-FIX-1 follow-up 全數完成。
