---
doc_id: DOC-QG-20
title: Quality Gate Overview
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - ci
last_verified: "2026-09-29"
authority: canonical
routing:
  intents:
    - quality-gate
    - validation
---

# Scraper 品質管線總覽

## 目的

本文件提供品質管線的高层概覽。詳細規則以 [`03_Quality_Gate_Rules.md`](03_Quality_Gate_Rules.md) 為準；渲染後 DOM 檢查以 [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) 為準。

## 技術檢核原則

1. XPath/JSON scraper 必須有非空白的根層級 `name:`；檔名一致是專案慣例。
2. `driver.useCDP` 只能宣告於頂層 `driver` 區塊。
3. 公開 `scrapers/*.yml` 不得包含 `driver.cookies`；需要登入的版本置於 `scrapers/private/`。
4. `sceneByFragment` 不是每個 scraper 的必填項目。
5. 日期格式使用 Go reference layout，例如 `2006-01-02`。
6. Schema、raw-response scrutiny、rendered-DOM fixture、live Stash/CDP 是不同證據層，不得互相取代。

## 驗證層級

| 層級 | 工具 | 證明範圍 |
|---|---|---|
| Schema | `npm run validate` | YAML 符合官方 schema |
| URL ordering | `npm run validate-sort` | URL array 排序 |
| Repository policy | `bash tools/validate-all.sh` | 命名、公開 cookies、fragment、日期政策 |
| Python regression | `python -m pytest tools/tests/` | 工具與測試套件 |
| Documentation | `python tools/check_scraper_docs.py` | 文件範例與規則 |
| Documentation index | `python tools/check_docs_index.py` | 文件 ID、路徑與索引 |
| Raw scrutiny | `node tools/scrutiny.js scrapers/<Scraper>.yml --search` | HTTP 加 JSDOM；不執行站點 JavaScript |
| Fixture control | `node tools/verify-scraper-fixtures.mjs --self-test` | 檢查器本身；不是站點 fixture 證據 |
| Evidence labels | `python tools/check_evidence_labels.py` | 拒絕缺少 artifact 的驗證聲稱 |
| CDP claim gate | `python tools/check_live_cdp_status.py` | 失敗閉合；不是 live Stash 執行 |

## CI 工作流

- `validate.yml`：schema、sorting、quality gate、pytest、safeguard 與文件檢查。
- `cdp-evidence-gate.yml`：拒絕沒有 artifact 的 live CDP 聲稱。
- `pr-check.yml`：針對 PR 變更的 scraper 執行檢查。
- `scrutiny.yml`：手動 raw-response probing，不是 rendered-DOM 或 live CDP 驗證。
- `link-check.yml`：檢查 Markdown 連結。
- `eval.yml`：手動評估測試。

## 狀態追蹤

- 綠色 CI 不代表 live selector、rendered-DOM fixture 或 production readiness。
- Live 測試結果記錄於 [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md)。

**最後更新**: 2026-09-29
