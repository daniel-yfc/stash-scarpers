---
doc_id: DOC-E2E-93
title: "Stash E2E Design Decisions and Proposal Review"
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - live-e2e
last_verified: "2026-10-31"
authority: derived
routing:
  intents:
    - design-decisions
    - proposal-comparison
---

# 技術設計參考與方案取捨

## 1. 依據與證據優先序

依 [Repository Documentation Architecture](../../00-documentation-architecture.md)：官方 CommunityScrapers schema/validator → 可執行 repo tools → canonical docs → Skill reference → 具體範例。

針對 Live E2E 結果，再將 **Stash 真實執行並有來源認證的 artifact** 與 **獨立 QA 複核** 分開；本工作包僅記錄使用者提供的 Muse QA v2 摘要，原始私有檔案尚待 reviewer 審核。不能因文字描述已驗證就假定有完整可再生的 Host trace。

| 來源 | 時點/角色 | 採用方式 |
| --- | --- | --- |
| QA-STASH-LIVE-E2E-20261031 v2（Muse） | 2026-10-31 現場測試／21:40 修訂 | **主要實測報告**；CDP 固定 endpoint 更正優先於 v1 |
| FIX-PLAN-STASH-E2E-20261031-v2（使用者） | 2026-10-31 主方案 | **實施規格主來源**，以本目錄記錄的 amendments 管控 |
| Cross-review Controller | 2026-10-31 風險與原碼核對 | 增加候選包指紋 Gate、Fragment 刪除、Owner 隔離等 |
| Perplexity 的 `Stash Scraper 修正建議方案` | 2026-10-31 21:44，標示 DRAFT／未實測 | 僅保留 red→green、第二頁面、可 revert 等方法；不覆蓋 QA v2 實證 |
| GitHub `main@4bbafca9cf7b5d67117ac41136e74a303c28e4f4` | 基準原始碼 | 只證明 repo 內路由、XPath、JS 存在；不代表 live 已修復 |

## 2. 已直接核對的程式碼事實

1. [BRAVO.yml](../../../scrapers/BRAVO.yml) 的 `sceneByURL` 只列 `bravo-japan.com/clips/`；[BRAVO.test.yaml](../../../scrapers/BRAVO.test.yaml) 卻含 7 個 DVD URL；現有 Title/Code/Image 的 XPath 註解寫明對 DVD 版面驗證。故應將 Clips/DVDS 分離，**不是進一步限縮既已只有 Clips 的路由**。
2. [KOShop.yml](../../../scrapers/KOShop.yml) Search `URLs` postProcess 包含 `v.replace(/\\?.*$/, "")`，確實會截除 `?product_id=`；Scene `//title` fallback 可能錯誤接納網站錯誤頁。
3. [CK-Download.yml](../../../scrapers/CK-Download.yml) Title XPath union 包含產品表格、h3 與 `//title`。XPath union 的結果由 document order 決定，**不代表 fallback 的邏輯優先順序**。
4. [Justice01.yml](../../../scrapers/Justice01.yml) Detail URLs 使用 canonical 與 og:url union 後 `concat: "\\n"`；使用單一 canonical 優先並給定缺席備援。
5. [docs/21-quality-gate-rules.md](../../21-quality-gate-rules.md) 規定正常 `sceneByQueryFragment` 必須保留 `queryURL: "{url}"`；不要把「直接 GraphQL 輸入沒 URL」解讀為應刪除全部 QueryFragment。
6. Justice01、RGBEE 等有 fixed Gender/Country/其他 Performer 欄位；但「fixed 導致 name=null stub」仍為**需要 A/B 實測的機制假設**。

## 3. 決策記錄（ADR-lite）

| ID | 決策 | 理由 | 重新開啟條件 |
| --- | --- | --- | --- |
| D1 | BRAVO Clips 先修，再獨立 PR 加 DVD | 不同頁型；避免混用 selector 與 PR 範圍擴大 | DVD 完成頁證明原碼已不可用/不具合法存取 |
| D2 | 優先固定 HTTP `/json/version` | QA v2 在 GVWiki/BRAVO/KOShop 實測有效，無 UUID | Stash/Chrome 重啟後失敗，才研究同步 WS |
| D3 | M1 和 M0 平行；M2 Clips 可平行 | 解耦 metadata correctness 與部署 preflight | 同檔修改或 Gate B 需等待 stable CDP |
| D4 | 正常 QueryFragment 不動；移除不可靠 BRAVO `sceneByFragment` | 前者保留 URL handoff，後者空 Title 可構造 bogus URL | 上游有缺值保護或可靠 Filename→Clips ID |
| D5 | KOShop 兩問題同一 Owner/PR | 相同 YAML；避免 overlapping PR 和漏測 | 無 |
| D6 | 只做受影響的 Live Delta QA + 最小整合 Smoke | 減少無關第三方站點波動/資源浪費 | 實際發現跨 Scraper 共用機制回歸 |
| D7 | 測試 PR 候選 ZIP，**不得以 main 現有安裝代替** | 已裝 main 的 21 packages 不代表分支版本 | 無 |
| D8 | 第一波三條獨立平行 Draft PR，最多六條修復分支 | 首波各自專屬 YAML；第二波避開重疊檔案 | 新的共用檔案需求 |
| D9 | 共用 stash-test 使用單一 QA Lease | 避免 Agent 交互安裝候選包與 Reload 污染 | 實際建立多套隔離測試實例 |
| D10 | PR #92 為工作包文件 Owner | 實作者不能同步覆寫 docs 索引與工作包 | Controller 重新指派 Owner |

## 4. 不採納之 Perplexity 項目（仍保留作設計對照）

- 「BRAVO DVD panic → 把 URL pattern 限縮到 Clips」：既有路由已 Clips-only，不能修根因。
- 「BRAVO Clips 先加 waitForElement」：不能以 JS 時序猜測取代已發現的 DVD XPath 誤路由；只有新 DOM 證據支持才加 wait。
- 「CDP 必須 WebSocket UUID 更新」：QA v2 已證實固定 HTTP `/json/version` 可用；重啟仍待測。
- 「每個 PR 都重跑 21 個 Scraper」：成本高、易受第三方站台風險干擾；改 Gate A + 受影響 Gate B + final smoke。
- 「所有欄位都必須非空、所有 upstream panic 必須由本 repo 消除」：不符合來源頁欄位存在性與權責範圍。

**可採納：** red→green mutation regression、每個變更 Scraper 第二布局交叉案、可回退 commit／PR、發布前比對 package SHA。

## 5. 參考來源與安全界線

- [Stash 官方 scraping 手冊](https://docs.stashapp.cc/in-app-manual/scraping/)；[Stash Scraper Sources](https://docs.stashapp.cc/metadata-sources/scrapers/)。
- [Stash 官方設定文件](https://docs.stashapp.cc/in-app-manual/configuration/)；固定 `/json/version` 應在實際部署網路中由 Stash 進程可達。
- [stashapp/stash Issue #4415](https://github.com/stashapp/stash/issues/4415)（GitHub API 於本次審查確認 Open，主題為 queryURL 缺值的體驗／錯誤）；若新症狀不相同需另行最小重現。
- [品質規則](../../21-quality-gate-rules.md)、[測試指南](../../50-testing-guide.md)、[Rendered-DOM fixture](../../51-rendered-dom-fixture-testing.md)、[驗證 Metadata](../../52-verification-metadata.md)、[Production Gate](../../30-production-gate.md)、[Skill/Host 證據](../../53-skill-evaluation.md)、[Scraper Source builder](../../../tools/build_scraper_source.py)。
- [歷史 Epic #80](https://github.com/daniel-yfc/stash-scarpers/issues/80)、[Draft #84](https://github.com/daniel-yfc/stash-scarpers/pull/84)、[Draft #85](https://github.com/daniel-yfc/stash-scarpers/pull/85)。

外部網站和 GitHub 連結為可讀來源，**不能當成授權登入、繞過限制或分享私有 QA artifact**。
