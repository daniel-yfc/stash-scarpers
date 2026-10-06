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
last_verified: "2026-10-06"
authority: canonical
routing:
  intents:
    - quality-gate
    - validation
---

# Scraper 品質管線總覽

## 目的

本文件概述儲存庫品質檢查，不代表任何特定 GitHub Actions 執行結果。詳細政策以 [`03_Quality_Gate_Rules.md`](03_Quality_Gate_Rules.md) 為準；實際七個 workflow 的觸發條件與證據邊界見 [`05_CI_Workflows.md`](05_CI_Workflows.md)。`last_verified` 為文件檢視日期，並非 CI 或網站實測日期。

## 技術檢核原則

1. XPath/JSON scraper 必須有非空白根層 `name:`；檔名一致屬專案慣例。
2. `driver.useCDP` 只能宣告於頂層 `driver` 區塊。
3. 本儲存庫公開的 `scrapers/*.yml` 不得包含 `driver.cookies`；需要登入的版本置於 `scrapers/private/`，也不可提交真實工作階段材料。
4. `sceneByFragment` 非通用必填；XPath/JSON fragment mapping 若存在，應符合其 action 的 `queryURL` 要求。
5. 日期格式使用 Go reference layout，例如 `2006-01-02`。
6. Schema、政策閘門、測試、fixture、即時搜尋／詳情頁與 live Stash/CDP 是不同驗證層，不可互相取代。

## 驗證層級

| 層級                     | 指令或工具                                                                         | 僅能證明                                                               |
| ------------------------ | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Schema                   | `node validator/index.mjs -a --ci`                                                 | YAML 符合本儲存庫由 CommunityScrapers 上游衍生的 validator/schema 要求 |
| URL ordering             | `node validator/index.mjs -a -s --ci`                                              | URL array 排序通過                                                     |
| Repository policy        | `bash tools/validate-all.sh`                                                       | 指定 scraper 通過儲存庫政策                                            |
| Python regression        | `python -m pytest tools/tests/ -v`                                                 | 實際執行的回歸測試通過                                                 |
| Documentation            | `python tools/check_scraper_docs.py`                                               | 檢查器所涵蓋的文件範例及矛盾規則                                       |
| Documentation index      | `python tools/check_docs_index.py`                                                 | 登錄範圍內的文件 ID、路徑與索引                                        |
| Raw scrutiny             | `node tools/scrutiny.js scrapers/<Scraper>.yml --search`                           | HTTP 加 JSDOM 的原始回應檢查；不執行站點 JavaScript                    |
| Fixture control          | `node tools/verify-scraper-fixtures.mjs --self-test`                               | 檢查器自測，非站點 fixture 驗證                                        |
| Fixture manifests        | `python tools/run_fixture_manifests.py`                                            | 已提交 manifest 中實際存在的案例；無 manifest 為 `UNVERIFIED`          |
| Evidence/CDP claim gates | `python tools/check_evidence_contract.py`、`python tools/check_live_cdp_status.py` | 證據來源與聲稱檢查；非 live Stash/CDP 執行                             |

## CI 工作流

- `validate.yml`：path-filtered schema、sorting、quality gate、pytest、safeguard 與文件檢查。
- `pr-check.yml`：針對 PR 變更的 scraper 執行政策檢查並回報。
- `fixture-manifests.yml`、`evidence-contract.yml`、`cdp-evidence-gate.yml`：各自檢查 fixture、結構化證據、CDP 聲稱；均不建立實頁驗證。
- `scrutiny.yml`：手動 raw-response probing，不是 rendered-DOM 或 live CDP。
- `link-check.yml`：PR／每週／手動的 advisory Markdown 連結檢查，綠燈不保證所有連結正常。

## 狀態追蹤

- Schema／政策／CI 結果不等於網站 selector 正確；live search 與 live detail 必須分別留存實際證據。
- JavaScript 網站的已完成渲染 DOM fixture，應依 [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) 分類頁面與記錄案例；fixture 通過不等於 live Stash/CDP 驗證。
- 網站實測狀態見 [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md)；詳細命令、修訂版、來源與限制使用 [`test-report-template.md`](test-report-template.md) 記錄。沒有執行的層級保持 `UNVERIFIED`。
- 目前沒有執行五題 skill Eval Pack 的 CI workflow；任何 CI 通過皆不等於 production readiness。

**最後更新**: 2026-10-02
