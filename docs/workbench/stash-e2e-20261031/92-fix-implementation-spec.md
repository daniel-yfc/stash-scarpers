---
doc_id: DOC-E2E-92
title: "Stash Live E2E Fix Implementation Specification"
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
    - fix-spec
    - implementation-roadmap
---

# Live E2E 修復實施規格（M0–M6）

**Controller plan status:** `FIX-PLAN-STASH-E2E-20261031-v2 / ACCEPTED_WITH_AMENDMENTS`；以實際 QA v2 補測更正為基礎。  
**Baseline commit:** `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`。  
**Limits:** 此文件授權**規劃，不代表授權實際改 YAML、Stash 或 merge**。正式開發採獨立修復分支與 Draft PR，僅 Controller / 使用者核准範圍內修改；**不自行 merge**。

## 不變約束（Surgical Discipline）

1. 同一檔案在同一輪僅一個主要 Owner；並行研究只能提供 findings，不同時改同檔。
2. 每項實際修復先補「修前 FAIL → 修後 PASS」的可執行回歸；以 source 完成頁 DOM 與 Stash runtime 確認，不只看 Schema。
3. 每個 PR 審核 `Gate A`（schema/fixture/unit）、`Gate B`（候選包指紋 + 真實 stash-test delta）、`Gate C`（exact HEAD CI、CodeQL、來源 ZIP 檢驗）；任何一個缺失不得稱 `FIXED_VERIFIED`。
4. **不**重跑 21 個 Scraper 全量 Live E2E，也不重審 QA-17/18/19 或已接受的歷史 CodeQL dismissal。
5. 禁止從 public repo、歷史提交或 fixture 取用真實 Cookie、API Key、Token；未取得授權不得登入、寫入生產 Scene、開放 Chrome remote debugging。
6. 主張的修復目標是 metadata **正確與可用**，非僅「非空」。

## 裁決 D1–D3

- **D1 DVD:** BRAVO 新增 DVD 功能，但先修既有 Clips。兩個連續、獨立的 PR；`/dvds/` 路由目前不存在，不應把 Stash unmatched-URL panic 當 YAML selector 的直接錯誤。
- **D2 CDP:** 固定 `http://<internal-host>:9222/json/version` 已由 v2 實測在三個 Scraper 可用；先完成重啟 / ACL，不再預先設計 UUID 同步腳本。僅若此固定形式經實測失效才討論替代方案。
- **D3 推進:** M1 Metadata Integrity 與 M0 OPS 平行，BRAVO Clips 可獨立平行開發；Gate B 在 CDP 重啟可靠後進行。

## 工作流與檔案 Owner

| 里程碑 | 工作 Owner / 建議分支 | 修改範圍 | 關鍵交付／相依 |
| --- | --- | --- | --- |
| M0 | OPS（不操作正式站） | stash-test 部署/ACL/備份驗證紀錄 | 固定端點重啟三態、備份實體、存取限制 |
| M1 | WS-B1 `fix/e2e-metadata-integrity` | `scrapers/Justice01.yml`、`KOShop.yml`、`CK-Download.yml` + 相應 sidecars/fixtures/tests | 一個 Draft PR、三個獨立 finding commits |
| M1b | WS-B2 `fix/e2e-identity-safety`（根因先行） | `ACCEED.yml`、Trance/GAMES/Justice01/RGBEE 等必要檔 + tests | 避免與 M1 的 Justice01 同時修改；依 Stash A/B 證據決定改動 |
| M2 | WS-A1 `fix/e2e-bravo-clips` | `BRAVO.yml` Clips 部分 + fixtures/tests | 分離 clip selectors；移除不可靠直接 Fragment |
| M2b | WS-A2 `feat/e2e-bravo-dvds` | `BRAVO.yml` DVD 路由/獨立 scraper + fixtures/tests | 基於 M2（檔案同 Owner 串行）；完整 DVD DOM 證據先行 |
| M3 | WS-C `fix/e2e-search-quality`（先調查） | `KOTube.yml`、`Trance.yml`、經證據確認的 GVWiki/Gayerdar/Pubu | Query 能力與站台參數先驗證；無解停損 |
| M4 | WS-D 文檔／upstream | E2E findings 的文件狀態、[Issue #80](https://github.com/daniel-yfc/stash-scarpers/issues/80) 後續更新、上游 issue | 本工作包不直接改 upstream 或 issue；避免無證據的 panic 因果斷言 |
| M5 | WS-F site monitoring | ClubCK/GetFilm/JGVData 狀態記錄 | 下次增量 QA 前低頻各複測一次；BLOCKED_SITE 非 YAML FAIL |
| M6 | Independent QA | [94-delta-acceptance.md](94-delta-acceptance.md) | 所有經核准修復的原 case、負例、跨功能 smoke；最後 Controller verdict |

## M0 — 操作環境 Gate

**M0-1** 從 Stash 內部驗證 `http://<internal-host>:9222/json/version` 可達（不要把私網主機名貼入公開報告）；分別重啟 Stash、Chrome、兩者，使用相同公開 CDP Scraper（GVWiki）原案擷取，證據留私有。

**M0-2** 驗證 Chrome debugging socket 只被授權主機／容器存取；stash-test GraphQL 須有認證或足夠嚴格 Tailnet ACL，並記錄測試人、存取路徑、收回機制。

**M0-3** 確認 `backupDatabase` 對應的備份產物確實存在且有可還原途徑（或使用已驗證的實例 snapshot），之後才可進行新持久化寫入。原有 15 個測試 Scene 暫留至 M6；Scene 7 的檔名與內容碼不同，不得用作 Identify matching PASS。

## M1 — 第一批 Metadata Integrity（可開發）

- **E2E-05 Justice01:** 現行 `URLs` 將 canonical 與 og:url XPath union 後 `concat: "\\n"`；改採 canonical 優先、og:url 缺席時 fallback，對單一有效 URL 產生結果。Fixture `justice115th`：恰一個可解析 URL、不含換行、與 canonical 一致。不能只在 JS 字串上盲目 split 以掩蓋不正確 selector。
- **E2E-06 KOShop（同一檔案內兩問題一起修）:** Search `URLs` 的 `v.replace(/\\?.*$/, "")` 砍掉 `?product_id=`；保留必要 product_id 並允許相對網址安全正規化，不要無差別保留追蹤參數。Scene Title 不得以 `//title` 接受不存在產品時的錯誤頁；只有有效商品節點存在才回可用 metadata（**驗證整體輸出無錯誤可寫入欄位，不只是 Title 變空**）。Probe：KERO256 → 搜尋結果保留 product_id、可續擷詳情；不存在 ID → 無可寫入假值；有效 41979 凍結案不退化。
- **E2E-08 CK-Download:** Title union `DVDタイトル td | h3 | //title` 遵循 XPath document-order 而非程式設計的 fallback 次序。以有效商品節點做首選與有條件備援；不要再無條件加入 `//title`。Probe `detail/34418` 的 URL 與 Search Title 一致，另加一個 DVD 商品及不存在商品負例。

**驗收：** M1 修前 FAIL／修後 PASS、原樣本＋第二布局樣本、Stash search → selected detail、錯誤頁不污染。

## M1b — 身分與誤導資料（先做根因 A/B）

- **E2E-09 ACCEED:** GraphQL 返回「ログイン」是否真的由 `//div[@id='content4']//blockquote/h2` 抽到，須先對照完成登入頁 DOM、Stash 實際選取的 Scraper 與 response 結構；定位前不改 XPath。未登入頁不得回可寫入 scene；合法登入頁只在使用者另外授權的 Session 測試後才可稱完整 PASS。
- **E2E-11 Performer stub:** 現有固定 Gender/Country 等欄位與 `name: null` 同時存在，**尚未因果驗證**。使用可重現的完成頁 fixture/獨立 Stash A/B 先證明 fixed 值是否造就 stub，再確認 Name-required 的可行 schema 寫法；不能憑猜測在所有 Scraper 刪固定欄位。
- **E2E-10 Trance:** 解析 `performerByURL` 回「指定なし」是否代表無有效 performer；若來源只給占位值，YAML 應拒絕建立該實體，否則留下文件化限制。
- 與 M1 的 `Justice01.yml`、M3 的 `Trance.yml` 相依；同檔修改串行，避免 PR overlap。

## M2/M2b — BRAVO 拆分

- **M2 Clips:** 原路由僅 `/clips/`，但 Title/Code/Image selectors 是 DVD page；建立 `clipSceneScraper` 及 Clips 專用 Title/Code（從完成頁取值）。如來源未提供 Date/Studio，**不要杜撰**。`/clips/284` 和 `/clips/282` 應以真實值比較；先移除可靠性不足的 `sceneByFragment`（`{title}` 空值可能送 `%7Btitle%7D`），保留正常 `sceneByQueryFragment` 搜尋結果 URL 保存行為。禁止將 DVD routing 混入本 PR。
- **M2b DVD:** 基於 Clips PR 的新 HEAD，先確認 `/dvds/234`、`/dvds/084` 及不同 DVD layout 的完成頁，建立獨立 `dvdSceneScraper` 與 `sceneByURL` 模式，至少兩個不同模板通過。未匹配 URL 的 panic 屬上游待查，不應為了使其消失而宣稱 Stash 已修。

## M3 — Search 精確度，設停損

- KOTube `29-01-0209-01`（原 160 筆無目標）、Trance `TC-05-0013-01`（原 60 筆無目標）：先檢查站台 query 參數、HTTP redirect、完成搜尋頁，判斷原始 query 是否在 Stash postProcess 中可用；站台原生精確比對優先。不可無差別逐筆打開 160 個詳情頁；單輪無法定位，`PARTIALLY_FIXED` 或 `BLOCKED_SITE` 需與驗收證據一致，**不能假裝 PASS**。
- GVWiki `JST56X`、Gayerdar `GD-025`、Pubu `348474`：各做匿名/授權環境對照，無 code-level 證據則轉 M5 觀察，不盲改 XPath。

## M4/M5 — 上游、文件、第三方站台

- [stashapp/stash#4415](https://github.com/stashapp/stash/issues/4415) 已由 GitHub API 確認目前 Open，討論缺值 queryURL 的行為；先補充 BRAVO 最小重現再決定開新議題。未匹配 URL panic 同樣先查重。
- [Epic #80](https://github.com/daniel-yfc/stash-scarpers/issues/80) 需在後續授權 PR/Issue 更新新的主幹 SHA、finding 狀態及 M6 憑據；**本工作包不改該 Issue**。
- Draft [#84](https://github.com/daniel-yfc/stash-scarpers/pull/84)（GraphQL harness）/ [#85](https://github.com/daniel-yfc/stash-scarpers/pull/85)（Evidence Validator）**不直接合併**，待 M1 後評估可移植元件。
- M5：ClubCK（timeout）、GetFilm（503）、JGVData Search（500）僅低頻複測恢復狀態，不用偽造 Scraper fix。

## M6 — 最小有效整合驗收

只執行改過的 finding 原案例＋必要負例＋一組跨功能 smoke：來源/套件載入、非 CDP detail、CDP detail、Search→Detail。結果需含精確 PR HEAD、Scraper revision/ZIP SHA、Stash build、證據位置、獨立 QA verdict。詳 [94-delta-acceptance.md](94-delta-acceptance.md)。

若正式發布/部署前 QA-06、登入功能、私網 ACL 或備份仍 OPEN，僅可有限測試發布，不得稱 `PRODUCTION_READY`。
