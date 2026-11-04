---
doc_id: QA-PR93-GATEB-20261104
title: PR #93 Gate B Independent QA — Focused Rerun v4 (HEAD d6d6fbf)
status: active
layer: qa
owner: agent-d-independent-qa
audience:
  - agent
  - maintainer
applies_to:
  - scrapers/BRAVO.yml
last_verified: "2026-11-04"
authority: evidence
---

# PR #93 Gate B 獨立 QA 報告 v4 — Focused Rerun @ `d6d6fbf`

**Assignment ID:** `WAVE2E-D-GATEB-PR93-FOCUSED-RERUN-20261104`
**Candidate HEAD:** `d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6`（`fix(e2e-bravo-clips): replace reverse-axis Duration selector with forward-axis from Clip label (WAVE2E-G-PR93-DEF01-R2-20261104)`；PR 仍 open/Draft/未合併）
**Lease:** `GATEB-PR93-LEASE-20261104-01`（owner 於本對話一次整批授予，2026-11-04 10:46 CST；已釋放）
**環境:** stash-test 專用；production 未寫入、未修改。

---

## 1. Executive Verdict

| 項目 | 裁決 |
|---|---|
| **GATE_B_VERDICT** | **`GATE_B_FAIL`** |
| DEF-01 Duration | ❌ **仍 OPEN（P1）** — 第三種 selector 形狀（forward-axis）實機仍 null |
| 其餘聚焦項目（B0/B3/B4/B5/B6/B7） | ✅ 全數 PASS |
| **BASELINE_VERDICT** | **`BASELINE_BLOCKED_LIVE_QA`** |
| 環境復原 | ✅ RESTORED_VERIFIED；lease 已釋放 |
| Merge authorization | NOT_AUTHORIZED（即使 PASS 亦然，本輪未達） |

**一句話：** Agent G 依 v3 收窄結果把 Duration 改為 forward-axis，方向假設已被本輪**證偽**——三種 XPath 形狀（簡單 reverse、複合 reverse、forward）在 Stash 實機全數回空，在 lxml/Chrome 全數回「30」。問題不在軸向；剩餘共同因子收窄至「數字測試謂詞的函數組合」與「Duration 欄位後處理/型別轉換」兩處，需實作端以最小探針隔離（§5）。其餘欄位全綠，Details 修復維持有效。

## 2. 版本史（各自獨立，不混雜）

| 版本 | HEAD | Lease | Verdict | 摘要 |
|---|---|---|---|---|
| v1 | `86e34a2` | 未授予 | NOT_RUN（`BLOCKED_OPS_AUTHORIZATION`） | 授權前，僅離線驗證 |
| v2 | `86e34a2` | `GATEB-PR93-LEASE-20261103-01` | FAIL | DEF-01 + DEF-02 雙 P1 |
| v3 | `ce7ef6c` | `GATEB-PR93-LEASE-20261103-02` | FAIL | DEF-02 CLOSED；DEF-01 OPEN（另有 lease-03 Proxy 包於同 HEAD 獨立重現 Duration null 6/6，與 v3 一致） |
| **v4（本輪）** | **`d6d6fbf`** | **`GATEB-PR93-LEASE-20261104-01`** | **FAIL** | DEF-01 仍 OPEN（第三形狀）；其餘全 PASS |

## 3. D-01 前置（本輪重驗）

- PR #93 HEAD `d6d6fbf`（ls-remote 雙路徑一致，2026-11-04 10:36 CST 推送）；vs `ce7ef6c` 僅 1 commit：BRAVO.yml **只有 Duration selector 變更**（Details 等其餘欄位逐字未動，程式化比對確認），fixtures/tests 新增 spacer-after-clip、price-after-clip 迴歸案。
- Exact-HEAD CI（d6d6fbf）：9 success + 1 skipped + 0 failure（含 CodeQL、Full Suite、fixture-manifests、Source Build）。離線：12 tests passed；新 selector 對先前實機 rendered DOM（lxml）雙頁回「30」——僅就緒訊號，未充作實機結果。
- 套件 provenance：重建 BRAVO.zip（僅 BRAVO.yml），SHA-256 = **`fca68a0ce91e89b6eac733defa120e5be0336785c543459a5734cf6815d50349`**，index version `d6d6fbf`。
- 復原點：preflight 與前三輪逐項相同（Stash `v0.31.1-182-g9e9ad972`、15/1/1、21 套件、BRAVO 基線 `b92acdd`），還原點存證 S1；復原程序為套件層卸載/重裝（已三度驗證）。

## 4. D-02 聚焦矩陣（真實 Stash runtime；證據 S2–S9）

B0 安裝驗證：隔離來源 `gateb-pr93-r4` 安裝後 `installedPackages` BRAVO = **`d6d6fbf`**，listScrapers 單筆 `["URL"]`。**PASS**

| Test | Expected | Actual（逐次） | 判定 |
|---|---|---|---|
| B1 clips/284 Duration | 1800 | t1 `null`、t2 `null` | ❌ FAIL |
| B2 clips/282 Duration | 1800 | t1 `null`、t2 `null` | ❌ FAIL |
| B2a clips/283 Duration | 1800 | t1 `null`、t2 `null` | ❌ FAIL |
| B2b QF clips/284 Duration | 1800 | `null` | ❌ FAIL |
| B3 Details（284/282/283） | 各頁產品描述 | 逐字相符（全次） | ✅ PASS |
| B4 Title/Code/URLs（全頁全次） | 各頁真值 | 全數相符、282 非繼承 | ✅ PASS |
| B5 Image | null（poster 不存在） | 全次 `null`、無無關圖 | ✅ PASS |
| B6 title-less / 999999 | 不得視為成功 | fragment 安全報錯 NULL；999999 全欄 null fail-closed | ✅ PASS |
| B7 控制/隔離 | GVWiki 正常、僅 BRAVO 變更 | Code `GV-OAV1372` 正常；套件差異僅 BRAVO；scene_count 全程 15 | ✅ PASS |

錯誤紀錄（GraphQL 層）：fragment 的 invalid-URL 錯誤、`/dvds/284` 的 upstream panic（#97，非本 PR 引入）皆完整存證（S7）。Stash 伺服器端 log 於 QA 環境無主機存取管道——此為證據限制，歷輪皆然；GraphQL error 回應即為可得的伺服器錯誤紀錄。

## 5. DEF-01 三形狀對照與機制再收窄（本輪核心證據）

| # | HEAD | Selector 形狀 | lxml | Chrome | **Stash 實機** |
|---|---|---|---|---|---|
| 1 | `86e34a2` | 簡單 `preceding::h2[1]`（標籤 normalize-space 比對） | 30 | 30 | **null** |
| 2 | `ce7ef6c` | 複合 `preceding::` + translate 去 U+200B + 巢狀 preceding:: 測試 | 30 | 30 | **null** |
| 3 | `d6d6fbf` | `following::` 自 'Clip' + translate + substring 數字首字測試 | 30 | — | **null** |

已證偽：軸向（reverse/forward 皆敗）、U+200B 前提、站台 DOM/時序、標籤文字本身。
三形狀的**共同因子**僅剩二：
1. **數字/內容測試謂詞的函數組合**（形狀 1 的標籤比對在 Code 欄位以同 'Clip' 錨點成功，唯 Duration 的目標節點選擇全數失敗；形狀 2/3 共用 substring+translate 巢狀組合）；
2. **Duration 欄位本身的後處理鏈**：javascript postProcess 回傳**數值**（分鐘×60）與 Stash 對 Duration 的型別轉換——此鏈在三輪中從未被獨立隔離（Details 的 JS 回傳字串且成功，不足以排除數值路徑）；基線 scraper 於 clips 頁同樣從未回傳 Duration（其 selector 為 DVD 取向，屬弱證據，僅供參考）。

**QA 觀察（非指令）：** 下一步隔離應由實作端以最小探針進行，例如在測試頁上分別驗 (a) 無謂詞的最簡 following 選擇、(b) 固定值 postProcess 的 Duration 欄位，逐一拆因子；離線/fixture 通過不得再充作修復證據。Gate B 下一輪仍只需聚焦複驗（B0 + 三頁 Duration + 欄位抽查）。

## 6. 復原與 lease 釋放（證據 S10）

卸載 candidate → yfc 重裝基線 → 移除暫時來源 → reload → 逐欄比對：version/stats/來源/scraping 設定/installedPackages 21 件**全欄與基線一致**（BRAVO 回 `b92acdd`、`["FRAGMENT","URL"]`）。**ROLLBACK_STATUS = RESTORED_VERIFIED；lease `GATEB-PR93-LEASE-20261104-01` 釋放。**

## 7. Controller 建議

1. PR #93 維持 Draft、不合併；DEF-01 退回實作端，依 §5 兩共同因子做探針隔離後再提新 HEAD。
2. DEF-02 與其餘欄位視為穩定，不得因 Duration 修正而回歸（下輪抽查即可）。
3. G0 不推進；Agent F 不開始正式整合。

## 8. 證據索引

目錄 `evidence-live3/`（digest 見 `MANIFEST-LIVE3.sha256`）：S1 基線還原點、S2–S4 安裝驗證、S5 雙頁+283 各 2 trials 原始回應、S6 QF、S7 負例與錯誤紀錄、S8 控制、S9 測試矩陣（machine-readable）、S10 復原後狀態。去敏規格同前輪（tailnet 位址與暫時來源 URL 於 repo 副本遮罩）。

**Repo 交付：** 本 v4 報告與 handoff 交付於本地 QA 包；repo 上架（追加至 `docs/qa-pr93-gateb-20261103` 分支 + PR #93 裁決評論更新）待 owner 另行指示。
