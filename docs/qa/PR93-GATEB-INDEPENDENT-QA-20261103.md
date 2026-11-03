---
doc_id: QA-PR93-GATEB-20261103
title: PR #93 Gate B Independent QA
status: active
layer: qa
owner: agent-d-independent-qa
audience:
  - agent
  - maintainer
applies_to:
  - scrapers/BRAVO.yml
last_verified: "2026-11-03"
authority: evidence
---

# PR #93 Gate B 獨立 QA 報告 v3 — Corrective HEAD `ce7ef6c` Live 重跑

**Assignment ID:** `WAVE2E-D-GATEB-PR93-20261103`（re-performance）
**Workstream:** `WS-2E-00 / Wave 1B Gate B`
**Role:** Agent D / Independent Live QA
**Candidate HEAD:** `ce7ef6c8f5c5663f41295e92a0603bca486abe98`（新 commit `fix(e2e-bravo-clips): correct Gate B Duration and Details selectors (WAVE2E-G)`，於前 HEAD `86e34a2` 之上；PR 仍 open/Draft/未合併，base `4bbafca9` 未變）
**執行日期:** 2026-11-03 晚間（Asia/Taipei）
**Lease:** `GATEB-PR93-LEASE-20261103-02`（owner 指令「re perform」授予，同 lease-01 規格；已釋放）
**前輪:** v2 報告（HEAD `86e34a2`）= GATE_B_FAIL（DEF-01 Duration、DEF-02 Details）。本 v3 只對新 HEAD 成立，舊結果不沿用。

---

## 1. Executive Verdict

| 項目 | 裁決 |
|---|---|
| **GATE_B_VERDICT** | **`GATE_B_FAIL`** |
| DEF-02 Details | ✅ **CLOSED**（實機雙頁回正確產品描述） |
| DEF-01 Duration | ❌ **STILL OPEN（P1）**（284/282/283 三頁 + QF 路徑，實機恆 null） |
| **BASELINE_VERDICT** | **`BASELINE_BLOCKED_LIVE_QA`** |
| G0 / Agent F | 不可推進 / 未就緒 |
| 環境復原 | ✅ RESTORED_VERIFIED（逐欄與基線一致）；lease 已釋放 |
| Merge authorization | NOT_AUTHORIZED（維持） |

**一句話：** 修正版把 Details 修好了（證據確鑿），但 Duration 換了 U+200B-proof 複合 selector 後在 Stash 實機**依然 null**——其前提（標籤含 U+200B 致比對失敗）已被本輪證據否定：同管線內 Details 的 translate() 謂詞與 Code 的簡單 preceding:: 都正常，唯獨 Duration 的複合謂詞在 Stash 的 XPath 引擎（antchfx）求值為空（lxml 與 Chrome 原生皆回「30」）。剩此一項 P1，Gate B 不能放行。

## 2. 新鮮度與離線重驗（新 HEAD）

- PR #93 HEAD `ce7ef6c`（ls-remote 雙路徑一致）；vs `86e34a2` 僅 1 commit，變更集中於 BRAVO.yml（Duration/Details selector + `$desc` common）、fixtures（284/282/extra-headings/no-cover 更新至今日 DOM 形狀，新增 clip-duration-price、clip-richtext-mixed）、test_bravo_clips.py。
- Exact-HEAD CI（ce7ef6c）：9 success + 1 skipped + 0 failure（含 CodeQL、evidence、fixture-manifests、Full Suite、Source Build）。
- Gate A 離線（本輪重跑）：test_bravo_clips **11 passed**（原 8，+3）；fixture runner self-test 1 passed（本地需 npm ci 補 jsdom 後通過，屬本地環境項）；新 selector 先以 lxml 對**前輪實機 rendered DOM** 求值：Duration →「30」、Details → 雙頁正確描述（離線成立，實機見 §4）。
- 套件 provenance：重建 BRAVO.zip（僅 BRAVO.yml，8657 B），SHA-256 = **`cdb9d2c57ea549c9167e683f1f56dcfadcd8ad4fb672d8c496f48c5fb938de78`**，index version `ce7ef6c`。
- **文件陳舊註記（P2/資訊）**：PR body 未隨新 HEAD 更新——body 內 HEAD_SHA 仍寫 `86e34a2`、BRAVO.zip digest 仍為舊值 `a4d24b1f…`。本輪 digest 以重建實測為準（上行）；建議實作端同步 PR body 以免後續驗證誤引。

## 3. M0 / Lease / B0-installed

- Preflight 與 lease-01 起點逐項相同（Stash `v0.31.1-182-g9e9ad972`、15/1/1、21 套件、BRAVO 基線 `b92acdd`、CDP 固定形式）；基線還原點重存（R1）。
- 隔離來源 `gateb-pr93-r2`（Muse 內建儲存，連結 2026-11-05 到期）安裝：`installedPackages` BRAVO = **`ce7ef6c`**；listScrapers 單筆 `["URL"]`；套件差異僅 BRAVO 一件（R2–R4、R7 末）。**B0 PASS。**

## 4. B1/B2 Live（2 trials × 2 頁 + 283 加驗 + QF，證據 R5–R7）

| 欄位 | 284 | 282 | 283（加驗） | 判定 |
|---|---|---|---|---|
| Title | ✅ 正確 | ✅ 正確（非繼承） | ✅ 正確 | PASS |
| Code | ✅ 284 | ✅ 282 | ✅ 283 | PASS |
| URLs | ✅ | ✅ | ✅ | PASS |
| Tags | ✅ 來源 meta keywords | ✅ 同來源清單 | — | PASS |
| Date / Studio | ✅ null（來源無） | ✅ | ✅ | PASS |
| Image | ✅ null（poster 不存在，v2 rendered DOM 已證；本輪 5 次擷取皆然） | ✅ | ✅ | PASS（B3） |
| Details | ✅ 產品描述全文正確 | ✅ 產品描述全文正確 | ✅ 正確 | **DEF-02 CLOSED** |
| **Duration** | ❌ **null**（應 1800） | ❌ **null** | ❌ **null** | **DEF-01 OPEN** |

QF 路徑（scrapeSingleScene url=284）結果同 URL 路徑：Details 正確、Duration null。

## 5. B3–B6（本輪重跑，證據 R7/R8）

- **B3 PASS**：Image 於所有擷取皆空，與 rendered DOM poster=0 一致；無無關圖回傳。
- **B4 PARTIAL（同 v2）**：真實負例 `/clips/999999` 全欄 null、fail-closed、無捏造；受控 title-less live 重播仍無對應頁面可執行（fixture 層已驗，分開陳述）；scene_count 全程恆 15。
- **B5 PASS**：QF 實機可用且結果與 URL 路徑一致；fragment-by-title 安全報錯 NULL，無 `clips/%7Btitle%7D`、無捏造。
- **B6 PASS**：`/dvds/284` 仍觸 upstream panic（#97，非本 PR 引入、不宣稱修復）；GVWiki 控制擷取正常；隔離僅 BRAVO 一件。

## 6. DEF-01 機制收窄（本輪新增證據，供實作端隔離）

已排除（實機證據）：
- ❌ 站台/DOM 因素：rendered DOM 中「30」h2 與 作品TIME h2 皆在，0–8s 各時點穩定（v2 L9）。
- ❌ U+200B 標籤前提：修正版 selector 已對標籤與候選值做 translate() 去 U+200B，且 **Details selector 同樣使用 translate()+normalize-space() 謂詞並實機成功** → translate 函數與去 U+200B 邏輯在 Stash 管線內可用。
- ❌ javascript postProcess 引擎：本輪 Details 的 javascript postProcess（trim 含 \u200b）實機正確執行；Image 的 JS postProcess 上輪亦正常。Duration 沿用同一 JS 形式。
- ❌ preceding:: 軸本身：Code 的 `preceding::h2[1]`（簡單形）實機正常。

剩餘嫌疑（指向明確）：Duration 新 selector 的**複合謂詞形狀**——在 reverse axis（preceding::）的 step 上疊加三段 and 謂詞、且謂詞內再嵌一條 `preceding::h2[...]` 軸測試，另含 substring() 數字首字測試。此形狀在 lxml（libxml2）與 Chrome 原生 XPath 皆求值為「30」，在 Stash 的 antchfx 求值為空。QA 觀察（非指令）：改用 forward-axis 錨定（如自 'Clip' 標籤 following:: 首個數字開頭 h2）或拆分謂詞，是與現有證據相容的修正方向；實作端決定並須以實機回歸證明，不得以 fixture/離線通過代替。

## 7. 復原與 lease 釋放（證據 R9）

解除 candidate → yfc 重裝基線 → 移除暫時來源 → reload → 逐欄比對：version/stats/來源/scraping 設定/installedPackages 21 件**全欄與基線一致**（BRAVO 回 `b92acdd`、`["FRAGMENT","URL"]`）。**ROLLBACK_STATUS = RESTORED_VERIFIED；lease -02 釋放。** Production 未觸及。

## 8. Controller 建議

1. PR #93 維持 Draft、不合併；DEF-02 記 CLOSED，DEF-01 退回實作端（依 §6 收窄結果修正 selector 形狀）。
2. 下一輪 Gate B 可縮小為**聚焦複驗**：新 HEAD 之 B0-installed + 284/282/283 Duration 實機 + 其餘欄位迴歸抽查（流程與 lease 規格同本輪）。
3. 順手修 PR body 的 HEAD/digest 陳舊值。
4. G0 不推進；Agent F 不開始正式整合。

## 9. 證據索引（live 重跑）

目錄 `evidence-live2/`（digest 見 `MANIFEST-LIVE2.sha256`）：R1 基線還原點、R2 available、R3/R4 安裝驗證、R5 B1/B2 原始回應（雙頁 ×2 trials）、R6 clips/283、R7 fragment/負例、R8 GVWiki 控制、R9 復原後狀態。v2 的 rendered DOM 證據（`evidence-live/L9`、`dom-*.html`）仍適用（站台 DOM 未變，本輪新 selector 已先對其離線求值）。

**Repo 交付（D4）：** v3 報告仍交付本地 QA 包，未 commit/未發 PR 評論（repo 寫入未在本輪授權內）。


---

## 附錄 — 完整運行紀錄（本 assignment 三輪）

| 輪次 | HEAD | Lease | 裁決 | 要點 |
|---|---|---|---|---|
| v1（授權前） | `86e34a2` | 未授予 | `BLOCKED_OPS_AUTHORIZATION` | 離線全驗通過（HEAD/CI/ZIP digest 重建/結構/獨立 XPath 重算）；未連入 stash-test |
| v2（live 首跑） | `86e34a2` | `GATEB-PR93-LEASE-20261103-01` | **`GATE_B_FAIL`** | DEF-01 Duration null、DEF-02 Details 零寬空白（雙頁 ×3 trials）；B0/B3/B5/B6 PASS；復原驗證完成 |
| v3（修正版重跑） | `ce7ef6c` | `GATEB-PR93-LEASE-20261103-02` | **`GATE_B_FAIL`** | DEF-02 CLOSED；DEF-01 仍 null（284/282/283+QF），機制收窄至複合謂詞形狀（見 §6）；復原驗證完成 |

證據分置：`evidence/pr93-gateb-20261103/offline/`（v1 離線 E1–E8）、`live-run1/`（v2 實機 L 系列）、`live-run2/`（v3 實機 R 系列）。Rendered DOM 全文（dom-284.html / dom-282.html，各約 900KB、含站台完整頁面內容）不入 repo，僅以 SHA-256 記錄於 `live-run1/MANIFEST-LIVE.sha256`，原檔保留於 QA 本地證據包（~/workspace/qa-pr93-gateb-20261103/evidence-live/）。
