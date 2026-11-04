# Wave 2E PR #104 Hardening Report — WAVE2E-F-PR104-HARDENING-20261104-R4

**Owner:** Muse Account ②（PR #104 作者）
**Assignment:** `WAVE2E-F-PR104-HARDENING-20261104-R4`
**Controller Decision:** `PR104_SELECTED_FOR_HARDENING / PR103_HOLD_AS_IS`
**Branch:** `feat/e2e-bravo-dvds-para`
**PR:** https://github.com/daniel-yfc/stash-scarpers/pull/104 （Draft，合併未授權）
**Base HEAD:** `86ce058a49f9d762b193f91c80cc8be867d1c341`
**New HEAD:** `3f3b4559349e501fdb57bc053f1efb90400540a4`（已推送，遠端 ls-remote 核實）
**Baseline:** main `ff236c9e91e27321e93f59d2bf12488db714dfc7`
**Report Language:** zh-TW
**Scope:** 離線加固 + Gate A + exact-head CI。**Gate B NOT_RUN；合併與部署未授權。**

## 1. Preflight（A-00）

- 全部基準經 `git fetch` + `git rev-parse` 核實：main ff236c9、#104 86ce058、
  #103 afe861f、Cross-QA A 6cddba00、Cross-QA B 83875b8，皆與指派書一致。
- 遠端 `feat/*` 無新的平行 Agent F 實作分支取代候選版（僅已知舊分支）。
- 兩份 Cross-QA 報告全文已讀（含 QA-A 證據包對抗頁形狀，僅作測試參考，
  結論皆獨立重算）。
- 變更檔僅 2 個：`scrapers/BRAVO.yml`（+45/−11 含註解）、
  `tools/tests/test_bravo_dvd_integration.py`（+137/−11）。

## 2. A-01 — Date 日曆驗證（PR104-CROSSQA-P1-3 → FIXED）

**問題：** 舊生產 JS 只做格式正規化，`2018年13月1日` → `2018-13-01`、
`2019年2月30日` → `2019-02-30` 被原樣輸出，且 YAML 無 parseDate 後盾。

**修復：** 生產 Date postProcess 改為手動日曆驗證（BRAVO.yml Date 區塊）：
month 1–12、day 不超過該月天數、閏年規則 `(y%4==0 && y%100!=0) || y%400==0`。
不合法日期與無法解析輸入一律回空字串，不猜日期。
驗證全程查表，不使用 `Date` 物件：無 overflow 正規化、無時區依賴。
未加 parseDate 步驟：JS 已保證輸出為合法 ISO 日期，parseDate 屬多餘環節。

**強制表（直接執行已提交 YAML 抽出的 JS，node）：** 10/10 通過。
`2018年8月29日`→`2018-08-29`、`2010年09月30日`→`2010-09-30`、
`2024年2月29日`→`2024-02-29`、`2023年2月29日`→空、`2019年2月30日`→空、
`2018年13月1日`→空、`2018年1月32日`→空、`2026年4月31日`→空、
空字串→空、無法識別文字→空。另驗世紀閏年：`2000年2月29日`有效、
`1900年2月29日`無效。既有 9 筆 G1 有效日期全部維持正確。
**永久測試：** DATE_CASES 擴充 10 筆（共 21 筆），皆由生產 YAML JS 執行。

## 3. A-02 — Product Identity 加固（PR104-CROSSQA-P1-1 → PARTIALLY_FIXED）

**舊 gate：** `//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href` —
只證明文件任一處有 品番 h2。

**新 gate（BRAVO.yml URLs 區塊）：**

```
//link[@rel='canonical'][//h2[contains(.,'品番')]]
  [normalize-space(//h2[contains(.,'品番')]/preceding::h2[2])!='']
  [normalize-space(//h2[contains(.,'品番')]/following::h2[1])!='']/@href
```

僅用 XPath 1.0 核心（絕對路徑、contains、normalize-space、axes），
且兩個新增 predicate 恰好檢查 Title/Code selector 本人回傳的節點是否非空，
語意一致、無額外假設。jsdom 雙向對照（21 頁：6 正例 + 404 + QA-A 對抗頁 +
自建 edge 頁）：全部 7 個有效頁 canonical 不變；新增抑制 4 類；
0 個有效頁迴歸。

**對抗矩陣（永久測試，生產 selector 實測，10 案例）：**

| 案例 | 結果 | 分類 |
|---|---|---|
| Valid product（完整模板） | URLs = canonical | VALID |
| Canonical-only 404（/dvds/555） | [] | SUPPRESSED |
| Fake marker 無 Code h2（QA-A 777 形） | [] | SUPPRESSED（新 gate 關閉） |
| Missing Title（真缺失） | [] | SUPPRESSED（新 gate 關閉） |
| Missing Code（真缺失） | [] | SUPPRESSED（新 gate 關閉） |
| Incomplete hydration（SSR 無 h2） | [] | SUPPRESSED |
| Challenge page（無 canonical） | [] | SUPPRESSED |
| Code 錯位為 label h2（QA-A code-missing 形） | URLs 照常輸出 | RESIDUAL |
| Code ≠ canonical 末段（234 vs /dvds/999） | URLs = /dvds/999 | RESIDUAL |
| Marker 夾在無關 h2 之間 | URLs 照常輸出 | RESIDUAL |

**PRODUCT_IDENTITY_RESIDUAL_RISK（提交 Controller）：**
YAML 層無法證明：(1) Code h2 是正確節點而非鄰近 label（非空檢查分不出來）；
(2) Code == canonical 末段（字串比對具 canonical 格式漂移風險，故未納入
gate；納入後有效頁 canonical 格式一變即掉 URLs，屬完整性迴歸風險）；
(3) canonical == requested URL（請求 URL 不在 XPath 上下文中，根本不可表達）；
(4) marker 與產品區塊的結構真實關聯（純 XPath 無模板約束可證）。
以上三個 RESIDUAL 案例在測試中以「實際輸出值」釘住，不是假裝修掉。
**未宣稱完整 fail-closed。** antchfx 等價性未驗，列 Gate B DVD-XPATH 必測：
若 antchfx 行為分歧，失效方向為 URLs 被抑制（fail-closed 方向）或整欄位失敗，
不產生假陽性。

**未採用的更強方案與理由：** canonical 末段字串比對（substring-after 比較）
經評估後不採用：有效頁 canonical 尾斜線／查詢參數／編碼一變即誤殺，
且 requested-URL 契約無論如何無法在 YAML 表達，半套比對增加 antchfx
複雜度卻換不到完整契約。Consuming-layer 元件未建（需另授權）。

## 4. A-03 — 政策保存（全部維持）

- DVD 欄位恰 {Title, Code, URLs, Details, Date, Image}；
  Clips 欄位恰 {Title, Code, URLs, Tags, Details, Image}，selector 逐字未動。
- Duration（Clips/DVD）、Studio、Tags（DVD）、Performers 皆未恢復；
  084 Details 保持空值、046/084 Code 前導零保持、084 sold-out 圖仍濾除。
- QueryFragment/Fragment 皆不存在；路由 2 條（clips/dvds）不變。
- DEF-01 未重開，無上游 Stash Core workaround。

## 5. A-04 — Gate A（新 HEAD 工作樹實測，CI 見 §6）

| 類別 | 結果 |
|---|---|
| 全套 pytest | **462 passed, 2 skipped, 3 xfailed**（86ce058 時 442；+20 為本輪新測） |
| validate-all | 24/24 PASS |
| Fixture manifests | 20/20 PASS |
| Evidence contract | 17 記錄，0 失敗 |
| Session-material scan | 370 檔 PASS |
| Docs index | 51 OK |
| format:check | 24 檔警告，皆為 main 既有基線檔；本輪 2 變更檔皆乾淨 |
| 套件重建 + verify-only | PASS；BRAVO.zip version `3f3b455` |

**套件來源：** BRAVO.zip SHA-256
`5bc3b2b7656d9c988f3552aaae271883e9a0e303f2c5a9e4c46494b232670ddb`
（提交前後兩次重建一致，確定性建置；舊 86ce058 摘要 `10fa6183…32fa`
已作廢，不得再引用）。無未解釋的測試排除。

## 6. Exact-head CI（2026-11-04 17:31 CST 唯讀查核，HEAD 3f3b455）

10 項檢查皆已完成：**9 成功、1 跳過、0 失敗**。
- CodeQL Analyze（actions / javascript-typescript / python）：成功
- Changed Scraper PR Check（pr-check）：成功
- Validate Scrapers（Full Test & Validation Suite）：成功
- Publish Stash Scraper Source（Build installable scraper source）：成功
- Fixture Manifest Verification（fixture-manifests）：成功
- Evidence Contract（evidence）：成功
- Code scanning results（CodeQL）：成功
- Deploy installable source to GitHub Pages：跳過（Draft PR 預期行為）

Gate A 本機 + 遠端 exact-head CI 雙邊一致。

## 7. 已知限制與未動項目

- P1-2 antchfx runtime：NOT_RUN，Gate B 必測（DVD-XPATH、QF live、無效 Date
  字串 Stash 處理皆屬 Gate B）。
- P2-1 runner getField 誤導訊息：既有、非本輪引入，行為 fail-closed，
  本輪未動（NONBLOCKING，維持）。
- P2-2 Image soldout 子字串過濾：fail-closed 方向可接受；相對路徑補全在現行
  selector 下為死碼，本輪未動（NONBLOCKING，維持）。
- P1-3 修正後 Stash 對空 Date 的處理（丟欄位或報錯）屬 runtime 未知，Gate B 驗證。
- PR #103 維持 HOLD_AS_IS，未動、未合併、未 cherry-pick。

## 8. Owner 最終狀態

`HARDENING_COMPLETE_READY_FOR_DELTA_QA`（CI 綠後生效；CI 若紅則改列
HARDENING_BLOCKED_TECHNICAL_LIMITATION 並回報 Controller）

**下一步（非本任務授權）：** Account ① 獨立 Delta QA（新 HEAD 3f3b455）→
Controller 裁決 Gate B；合併／部署仍須另行授權。
