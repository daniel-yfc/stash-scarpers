---
assignment_id: WAVE2E-D-PR93-DURATION-DEFER-GATEB-20261104
workstream: "WS-2E-00 / Wave 1B Gate B"
role: "Independent QA (executed in chat ace76ce3 per user designation, lease GATEB-PR93-LEASE-20261104-02)"
date: 2026-11-04
head_sha: 88d27a5764c30fec1ab8bb5a325382e72a2ef09e
verdict: GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE
---

# PR #93 Gate B 獨立 QA — 修訂 Duration 範圍（omission candidate）

## 1. 裁決

**`GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE`**

- 本裁決只對新 HEAD `88d27a5` 與 Controller 決策 `WS-2E-DEF01-DEFER-20261104` 的修訂契約成立：Clips Scene.Duration 對映已移除，實機 Duration 為 null 是**預期行為**。
- **v4 的 `GATE_B_FAIL`（HEAD `d6d6fbf`）維持原判、不被本裁決推翻**；Duration null 不是「DEF-01 已修復」的證據 — 缺陷是被正式 defer（根因 R3 H4：Stash `scrapedScene()` 以 IntPtr 讀 Duration、只接受 Go int，scraper 字串值必然被棄；還原規格在 `docs/qa/PR93-DURATION-DEFERRED-SPEC.md`）。
- PASS 不授權合併；merge authorization 仍由 Controller/user 另行判定。

## 2. Preconditions / Provenance

- PR #93 HEAD（本輪 ls-remote 實測）：`88d27a5764c30fec1ab8bb5a325382e72a2ef09e`（鏈：ce7ef6c → d6d6fbf → f4be5cf omission → 88d27a5 test-only）。PR 仍 Draft/未合併。
- Omission 查核：BRAVO.yml 對 d6d6fbf 的唯一功能變更是移除 clipSceneScraper 的 Duration 對映；Title/Code/URLs/Details/Tags/Image/QF/路由逐字未動（diff + YAML 本體雙重確認）。
- 套件：離線重建 BRAVO.zip SHA-256 = `004ef0679152fc954822ebadaaf534c050ec2a2fb3e710612d7e6280a863dbcf`，verify-only OK，index version `f4be5cf`（版號 = 最後動 BRAVO.yml 的 omission commit；HEAD 88d27a5 為 test-only）。
- Lease：`GATEB-PR93-LEASE-20261104-02`（user 於本 chat 核發，stash-test only，舊 lease 未重用）；隔離來源 `gateb-pr93-r4` 安裝，installedPackages 驗明 BRAVO = `f4be5cf`，listScrapers 單筆 [URL]。
- 離線 Gate A：test_bravo_clips 14 passed（含 source-only deferred Duration 案例）。Exact-head CI：本 chat 無 checks 讀取工具，未獨立重讀（Agent D chat 報 10 success + 1 skipped，不借用為本輪驗證）。

## 3. 修訂 Live 矩陣（expected / actual）

| Case | Title | Code | URLs | Details | Duration | Image | 結果 |
|---|---|---|---|---|---|---|---|
| Clips 284 ×2 | ✓ 雙 trial 符合 | ✓ 284 | ✓ canonical | ✓ 產品專屬描述 | null（預期） | 空 | 符合修訂契約 |
| Clips 282 ×2 | ✓ 來源專屬 | ✓ 282 | ✓ | ✓ 與 284 互異 | null（預期） | 空 | 符合 |
| Clips 283 ×2 | ✓ ハルキリーマン交尾 | ✓ 283 | ✓ | ✓ 正確描述 | null（預期） | 空 | 符合（無回歸） |
| QueryFragment 284 | ✓ | ✓ | ✓ | ✓ | null（預期） | 空 | 符合 |

（每頁 trial 2 前執行 reloadScrapers；原始 request/response 全存 evidence/。）

## 4. Image（poster-only）

三頁頁面 HTML（本 lease 期間直抓，HTTP 200）各含 2 個 `<video>`（pageBackground + 產品 comp-kbfkf16e_video），**皆無 poster 屬性**；scraper Image 於全部擷取皆空，無 myfans logo/導覽/廣告等無關圖回傳 — fail-closed 與來源一致。Poster-present 分支本輪仍無 live 頁可驗（UNVERIFIED_BRANCH，沿前輪紀錄）。

## 5. 負例

- Title-less（fixture）：新 HEAD 測試 1 passed（Title 空、Code 999、URLs canonical、Image 空、無捏造）；live 受控重播無對應頁面，沿 fixture 層證據分開陳述。
- Invalid URL `clips/999999`：Title/Code/Details/Duration/Image 全 null（fail-closed）；Tags 回站台通用 meta keywords（與前輪相同原始事實，非產品 metadata，未持久化）。
- Fragment 空輸入/空 Title：兩變體皆安全報錯，無 `clips/%7Btitle%7D` 假 URL、無假成功。
- Unmatched `/dvds/284`：upstream panic（index out of range）— 已知 Stash 上游行為，分開記錄，不歸因 PR #93。
- 控制：KOShop product 41979 回 Title「ナマ狂い種壺待機」/ Code `BWB365_DVD`（凍結案例），無跨 scraper 影響。

## 6. 環境復原

Rollback 完成並驗證：candidate 卸除 → 基線 BRAVO `b92acdd`（yfc）重裝 → 隔離來源移除 → reloadScrapers → 測前/測後比對 **5/5 全等**（version / stats 15-1-1 / 來源 / scraping 設定 / 21 套件）。全程僅唯讀擷取，零 Scene 持久化；production 未觸及。Lease -02（20261104）已釋放。

## 7. 證據

`~/workspace/qa-pr93-gateb-defer-20261104/`：本報告、PREFLIGHT-20261104.md、LEASE-RECORD-20261104-02.md、evidence/（installed/listScrapers、矩陣 request/response、expected-actual-matrix.json、負例、控制、page-html ×3、rollback 全紀錄、MANIFEST-LIVE.sha256）、三支執行腳本。
