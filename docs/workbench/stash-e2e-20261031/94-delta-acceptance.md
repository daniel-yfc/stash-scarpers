---
doc_id: DOC-E2E-94
title: "Stash Live Delta Acceptance Contract"
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
    - delta-qa
    - acceptance-gates
---

# Live E2E 增量驗收契約

**Gate scope:** 僅處理本工作包已修復的 E2E finding；不自動重跑 21 個 Scraper 全量 Live QA，亦不再審 QA-17/18/19 或 CodeQL 既有 dismissals。  
**Must pin:** Repo exact PR HEAD、受測 Scraper 最後來源 commit/version、ZIP SHA-256、Stash build、URL／模式、測試時間、授權與獨立 reviewer。  
**Allowed statuses:** `FIXED_VERIFIED`、`PARTIALLY_FIXED`、`STILL_FAILING`、`BLOCKED_SITE`、`UPSTREAM_STASH`、`NOT_RUN`；不得自動把環境可達性當功能通過。

## 1. 三重 Gate（每個 PR 缺一不可）

| Gate | 作業 | 合格 |
| --- | --- | --- |
| A — deterministic | schema/Ajv、變更 YAML 的 fixture、對應 unit/regression、session policy | 受影響的既有測試全 PASS；新負例先紅後綠 |
| B — actual Stash | 安裝**PR 候選包**到隔離 stash-test；對原 fail case、1–3 正常案、第二布局/關鍵負例實際執行 Stash GraphQL/UI | 來源值對照、未回傳 bogus data、版本指紋完全對應 |
| C — integration | exact PR HEAD CI、CodeQL、來源 ZIP build/verify、必要跨功能 smoke | 無未解新高風險且源碼與產物一致，Controller review 完成 |

### 1.1 候選包來源鏈（必做）

1. 每個 PR 在完整 Git 歷史下對**該分支**執行 `tools/build_scraper_source.py`；確認只包含 `scrapers/*.yml`，不包含 `scrapers/private/`。
2. 取得 `index.yml` 中被改 Scraper 的 **version / date / path / sha256**，計算 ZIP 實體 SHA-256，比對一致。
3. 在 stash-test 使用隔離安裝來源或受控卸載／覆寫程序，**不得載入兩個同 name 的 scraper 而造成版本 shadowing**；執行 reload。
4. 以 Stash `installedPackages`、`listScrapers` 與測試實際選擇的 Scraper identity 確認受測的是候選版；若只能證明 public/main 版，Gate B = `NOT_RUN / WRONG_REVISION`。
5. QA 結束後記錄是否保留分支測試套件及如何安全回復已發布 main 版本。PR preview artifact 不是正式永久 Source URL；**不得為做 Gate B 先 merge**。

### 1.2 需要保存的單次測試資訊（公開只記去敏索引）

```json
{
  "finding_id": "STASH-E2E-05",
  "case_id": "JUSTICE-URL-CANONICAL",
  "repo_head": "<40-hex-pr-sha>",
  "scraper_id": "Justice01",
  "package_version": "<source-version>",
  "package_sha256": "<64-hex>",
  "stash_build": "v0.31.1-182-g9e9ad972",
  "method": "STASH_GRAPHQL",
  "source_page_state": "COMPLETED_TARGET_PAGE",
  "expected": "single canonical URL",
  "observed_summary": "<redacted-nonsecret-field-summary>",
  "evidence_ref": "<private-evidence-reference>",
  "result": "NOT_RUN",
  "reviewer_status": "PENDING"
}
```

上述是**欄位結構範例，不是執行過的 test run**。保存含公開可辨識測試頁的最低必要資訊即可；原始 GraphQL / Cookie / Chrome profile / HAR 留受限工作區，不上傳公開 Repo。

## 2. 各 Finding 的具體驗收

| ID | Case / 原始 probe | 正向驗收 | 必要負例／例外 |
| --- | --- | --- | --- |
| 01 | GVWiki URL CDP + 三種重啟 | 固定 `/json/version` 重啟後可用 | CDP ACL/GraphQL authentication 經授權審核；失聯時錯誤清晰 |
| 02 | BRAVO DVD `/dvds/234`, `/dvds/084` | 新路由若列為支援，兩個完成頁 Title/Code 正確 | 未匹配 URL panic 僅 `UPSTREAM_STASH`，不得冒稱已解 |
| 03 | BRAVO Clips `/clips/284`, `/clips/282` | Title/Code 與來源完成頁一致 | Date/Studio 不存在時不得捏造；保留 Details/Tags |
| 04 | BRAVO 空 Title 直接 Fragment | 不再產出 `clips/%7Btitle%7D` 假 URL | 正常 Search→QueryFragment 仍能保留選定 URL |
| 05 | Justice01 `justice115th` | URLs 恰一個、有效且 canonical 優先 | 無 canonical 時 og:url fallback；不得 newline/duplicate |
| 06a | KOShop `KERO256` | 結果 URL 保留 `product_id` 且能進入 detail | 非預期追蹤參數不能破壞商品識別 |
| 06b | KOShop valid 41979 / missing 99999999 | 41979 Title/Code 正確 | 99999999 不得回任何可寫入的錯誤商品 metadata |
| 07 | KOTube `29-01-0209-01` / Trance `TC-05-0013-01` | 精確碼查詢含目標，結果不失控 | 無站台/模式可行性時如實保留 LIMITATION，不宣稱 PASS |
| 08 | CK-Download `detail/34418`＋一個 DVD case | URL Title 與搜尋結果一致，Code 仍正確 | 不得回通用 site title 或錯誤頁 Title |
| 09 | ACCEED `ACSM051` / `ACST431` | 授權完成頁資料正確（若有登入 session） | 匿名登入重導不得冒充產品 Title；不足授權列 BLOCKED_AUTH |
| 10 | Trance performerByURL | 真實 performer identity 正確 | 「指定なし」不能建立有效 Performer |
| 11 | GAMES + Justice01 + RGBEE stub A/B | 欄位/Name 必要條件經 Stash A/B 確認 | `name:null` 不得產生誤導性實體 |
| 12 | GVWiki `JST56X`、Gayerdar `GD-025`、Pubu `348474` | 有效搜尋可命中目標，或有資料支持的限制 | 無法定位站台因素時保留 `NOT_RUN` / `BLOCKED_SITE`，不亂改 YAML |

## 3. M6 最小跨功能 Smoke

- Public Source/Preview package hash/installed version 對應、Reload Scrapers 後可選取。
- 1 個非 CDP 的合法 scene URL、1 個 CDP 的合法 scene URL（固定 endpoint）。
- 1 次 `sceneByName` → 選取 result → `sceneByQueryFragment` → 詳情 Metadata。
- 1 次不存在商品／登入頁負面測試；**不能被 Stash 接受為可直接寫入的 Scene 資料**。
- 持久化僅在 staging 且**實體備份可還原已確認、明確授權**時測；驗證寫入→讀回→重跑去重→記錄清理。測試 Scene 資料不得當作真實作品匹配。
- 網路/登入封鎖由 M5 獨立判 `BLOCKED_SITE` / `BLOCKED_AUTH`，不以未修第三方站點強迫 PR FAIL。

## 4. 完成／發布裁決（不可跨級）

| 級別 | 最低條件 |
| --- | --- |
| `LIMITED_STAGING_ACCEPTED` | CDP/備份/權限 Gate，必要 Scraper 正負面結果皆 PASS，沒有新的錯誤寫入 |
| `LIMITED_SCRAPER_RELEASE` | 明確 allowlist 已驗證的 Scraper ID+revision；未驗證或有缺陷者明示不支援/未驗證 |
| `FULL_STASH_E2E_PASS` | 核准範圍的必要 modes 全部驗證；上游/站台例外已明確分類並經 Controller 接受 |
| `PRODUCTION_READY` | 另需 [Production Gate](../../30-production-gate.md) 完整檢查、QA-06 輪替/撤銷 attestations、正式環境登入/ACL/備份/回滾與使用者批准 |

每個 Gate B 都需要**獨立 reviewer 核對實際私有 artifact**；只有本表的模板或 Agent 自行聲稱 PASS 不構成 `FIXED_VERIFIED`。
