---
doc_id: DOC-E2E-91
title: "Stash Live E2E Evidence Ledger (Reported v2)"
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
authority: informational
routing:
  intents:
    - live-e2e-evidence
    - evidence-ledger
---

# Live Stash E2E 實測證據摘要與來源台帳

**Evidence identifier:** `QA-STASH-LIVE-E2E-20261031-01 / v2`  
**Source:** 使用者於 2026-10-31 提供的 Muse（雞仔）正式 Stash 實例驗收報告及 21:40 CST 更正。  
**Baseline:** `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`；**Stash:** `v0.31.1-182-g9e9ad972`（build 2026-10-27）。  
**Veracity boundary:** 本頁是**第二手、去敏的正式追蹤摘要**，不是本文件作者親自登入 Stash、重跑 GraphQL、讀取原始 artifact 或簽發獨立 attestation。未提供原始檔案時，不得由這份 Markdown 推論「已獨立認證」。

## 1. 執行與環境範圍（依 QA 報告）

| 項目 | 報告中已完成 | 尚未取得／未執行 |
| --- | --- | --- |
| 測試方式 | 授權 stash-test 上 Stash GraphQL（UI 同後端，但**非完整 UI 操作證據**） | Production UI / API 測試 |
| 安裝來源 | 獨立 yfc Source，manifest 21、available 21、installed 21，與 Community 並存 | 重新點擊 UI 安裝流程未執行 |
| 套件完整性 | ACCEED、BRAVO ZIP SHA-256 抽驗與 manifest 一致 | 全部 ZIP 逐件 hash 與來源真實性審核 |
| Scraper | 21 個公開 Scraper 可由 Stash 載入；另外 2 個 `scrapers/private/` 變體**未發布** | private 變體實際部署與登入態 |
| URL | 21 個主要 URL 案例 + 3 個延伸案例（共 24） | 站台遭封鎖或登入要求的完整功能 |
| 搜尋 | 20 案（含一個對照），報告列 11 個 PASS（部分附排除） | 有缺陷的搜尋仍未修復 |
| Fragment | 4 案，1 PASS；包含空缺 placeholder 負例 | fc2 檔名 Fragment 未執行 |
| Group / Performer | Group 2/2 PASS；Performer 1 案回傳無意義值 | 其他 Performer URL 模式未執行 |
| 持久化 | 測試 Scene 7 套用 Metadata 後讀回與重跑去重 PASS | 完整 UI 操作、正式環境、備份還原證據 |
| 安全 | 此輪報告未觀察到新的憑證外洩 | **QA-06** 過去已外洩憑證的服務端輪替／撤銷 attestation |

### CDP v2 修訂（覆蓋 v1 推論）

初始 `scraperCDPPath` 空白，13 個宣告 CDP 的 Scraper 在未設定情況下無法使用；v1 以 WebSocket UUID 配置恢復大部分功能。v2 **補測固定 HTTP 路徑** `http://<internal-host>:9222/json/version`，在 GVWiki、BRAVO、KOShop 三個 CDP Scraper 成功，並已設為 stash-test 當前設定。故「必須使用 WS UUID」不是成立的限制。

**仍待驗證：** Stash 重啟、Chrome 重啟、雙重重啟的 recovery、Chrome debugging socket ACL、GraphQL 認證／Tailnet 授權；不能以不含 UUID 取代這些實測。

### 持久化界線

先前測試掃描建立 15 個 Scene；單筆 Scene 7 使用檔名含 `MR-KR2034` 的影片，但套用 `MR-KR2247` 的外部擷取資料。此案例**證明可寫入、讀回及按名稱重用關聯實體**，不證明自動匹配同一作品。不可據此提升 Identify accuracy PASS。報告只記載 `backupDatabase` 回傳無錯誤，尚未實際核對備份產物及可還原性。建議保留測試 Scene 至 M6 後再清理。

## 2. 每個公開 Scraper 狀態（依 v2）

| Scraper ID | URL | Search | 本輪已知風險 / 限制 |
| --- | --- | --- | --- |
| ACCEED | BLOCKED_AUTH | PASS | 未登入詳情回「ログイン」，E2E-09 |
| BoyStudio | PASS | PASS_WITH_EXCLUSIONS | Search 只有 URL stub |
| BRAVO | FAIL | N/A | Clips 欄位空；DVD 未路由；空 Title Fragment |
| CK-Download | PASS_WITH_EXCLUSIONS | PASS | URL Title 通用字串，E2E-08 |
| ClubCK | BLOCKED_SITE | BLOCKED_SITE | 逾時；非 YML 已證實缺陷 |
| Exfeed | PASS | PASS | 此輪沒有重大 finding |
| fc2 | PASS_WITH_EXCLUSIONS | N/A | Details 空；Filename Fragment NOT_RUN |
| GAMES | PASS | PASS | Performer name-null stub，E2E-11 |
| Gayerdar | PASS_WITH_EXCLUSIONS | MISS | Details 空、搜尋未命中 |
| GetFilm | BLOCKED_SITE | BLOCKED_SITE | 站台 HTTP 503 |
| GVWiki | PASS | MISS | 名稱搜尋未命中；CDP 已補測 |
| HunkCh | PASS | PASS | 未登入 Performer name 空 |
| JGVData | PASS | BLOCKED_SITE | 搜尋端點 HTTP 500 |
| Justice01 | PASS_WITH_EXCLUSIONS | PASS | URLs newline/duplicate，E2E-05 |
| KOShop | PASS | PASS_WITH_EXCLUSIONS | 搜尋 URL 遺失 product_id、錯誤頁假陽性 |
| KOTube | PASS | FAIL | 精確 code 查詢回 160 筆，目標缺失 |
| KOVideo | PASS_WITH_EXCLUSIONS | PASS | 匿名 Code 缺少 |
| MensRushTV | PASS | PASS | 受控持久化使用此 Scraper |
| Pubu | PASS | MISS | 查詢回零筆 |
| RGBEE | PASS_WITH_EXCLUSIONS | PASS_WITH_EXCLUSIONS | Studio 尾隨底線；Performer stub |
| Trance | PASS_WITH_EXCLUSIONS | FAIL | Search 60 筆無目標；Performer「指定なし」 |

報告中的 URL 案例統計「有回傳欄位」不等於所有必填欄位符合預期。以上依**原報告的每 Scraper 狀態**，未對缺席欄位自動推論為失敗。201?（不採此類歷史統計）——請以該 v2 報告所列個案及本頁結論為準。

## 3. Finding Ledger（待修、非已驗收）

| ID | 原嚴重度 | 故障 / 實證 | Track | 目前修復證據 |
| --- | --- | --- | --- | --- |
| E2E-01 | P1 | 初始 CDP 未設；固定 HTTP endpoint 三 Scraper 補測通過 | M0/OPS | `PARTIALLY_FIXED`（重啟/ACL待驗） |
| E2E-02 | P1 | BRAVO DVD URL 未匹配；無匹配 URL 可能令 Stash panic | M2b+M4 | `STILL_FAILING`／上游責任待回報 |
| E2E-03 | P2 | BRAVO Clips 套用 DVD selectors，Title/Code 空 | M2 | `STILL_FAILING` |
| E2E-04 | P2 | 空 Title 的直接 Fragment 構造無效 URL；缺 URL QueryFragment 屬 API 邊界 | M2+M4 | `STILL_FAILING`（正常 QueryFragment 保留） |
| E2E-05 | P2 | Justice01 canonical/og:url + newline 合併 | M1 | `STILL_FAILING` |
| E2E-06 | P2 | KOShop Search URL 遺失 query；不存在產品錯誤頁變 Title | M1 | `STILL_FAILING` |
| E2E-07 | P2 | KOTube/Trance 精確碼查詢無正確目標 | M3 | `STILL_FAILING`／先調查 |
| E2E-08 | P2 | CK-Download URL Title fallback 錯誤 | M1 | `STILL_FAILING` |
| E2E-09 | P2 | ACCEED 未登入會回登入頁 Title | M1b | `BLOCKED_AUTH` + 污染風險 |
| E2E-10 | P3 | Trance performerByURL 回「指定なし」 | M1b | `NOT_RUN`（修復驗證） |
| E2E-11 | P3 | Name 未命中卻有 fixed performer 欄位，產生 null stub | M1b | `ROOT_CAUSE_TEST_REQUIRED` |
| E2E-12 | P3 | GVWiki/Gayerdar/Pubu 搜尋 MISS | M3 | `STILL_FAILING`／分類待查 |

**原有分類保持：** 0 P0、2 P1、7 P2、3 P3。嚴重度是 QA v2 原始分類，不因被拆分而冒充新的 finding 總數。ClubCK、GetFilm、JGVData Search 均屬 `BLOCKED_SITE`，未獲新證據前不得誤改 YML。

## 4. 私有原始證據索引（僅引用，不納入公開 repo）

由原 QA 報告列舉、**本次文檔提交未讀取其 bytes**：

- `evidence/listScrapers.json`、`installedPackages.json`、`availablePackages-yfc.json` — Stash inventory / revision。
- `evidence/url_tests.json`、`search_tests.json` — 原始 URL / 搜尋輸出。
- `evidence/fragment_failure_tests.json`、`extra_tests.json`、`perf_tests.json` — 失敗/實體模式。
- `evidence/scenes-after-scan.json`、`persistence_test.json` — Scene 持久化前後；`configuration.json`、`scraping-config.json`、`configureScraping-cdp.json` — 設定前後。
- 原 QA 執行腳本 `run_url_tests.py`、`run_search_tests.py`、`run_fragment_failure_tests.py`、`run_extra_tests.py`、`run_perf_tests.py`、`run_persist_test.py`。

上列檔案應留在**授權的私有 QA workspace**；原始 trace 是否完成、安全去敏、來源是否可驗證，須由獨立 QA reviewer 確認。不要將公共文字摘要偽裝成 Host-origin attestation。

## 5. 已繼承的 Repository 證據與 open obligations

- 原 Stack #87–#90 已合併；基準 `main` tree 為 `f385fbfc0ccaea9e2605ace8681858c27c2c28fa`；既有 CI/CodeQL 不需於本工作包重跑完整人工 QA。
- 以前 QA-17/18/19 增量及 CodeQL #38–#41 dismissal 已由 Controller 接受；**不重審**。
- QA-06 僅確認目前追蹤樹已去敏，**歷史 exposed credential 的服務端 revocation/rotation attestations 仍 OPEN**。
- Live Stash 成功不是 AI Host Skill load PASS；`docs/53-skill-evaluation.md` 維持獨立判定。
- 正式上線 `PRODUCTION_NOT_READY`；不要因這份證據摘要提升正式部署狀態。

參閱 [實施規格](92-fix-implementation-spec.md) 與 [驗收合約](94-delta-acceptance.md)。
