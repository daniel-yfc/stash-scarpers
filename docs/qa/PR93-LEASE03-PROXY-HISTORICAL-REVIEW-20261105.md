---
doc_id: PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105
title: PR #93 historical Lease-03 Proxy evidence — version-bounded independent review
status: historical_review_public_manifest_verified_binary_custody_and_security_gaps
layer: qa
owner: controller
audience: [maintainer, agent, auditor]
applies_to: [PR-93, Wave-1B, Gate-B, G0, Duration]
last_verified: "2026-11-05"
authority: controller_historical_addendum
---

# PR #93 — Lease-03 Proxy 證據包獨立判讀之歷史歸檔（2026-11-05）

> **重要更正（同日重查）：** 已發現專屬 Proxy 公開來源分支 `docs/qa-pr93-gateb-proxy-20261103@80f5307`；Controller 已**獨立重算全部 56/56 公開原始檔案之 SHA-256，均與 `MANIFEST-LIVE` 相符**，並回讀 B1/B2 六份 GraphQL 回應。原文有關『Proxy manifest/raw 56 files 未公開／Controller 未重算』之說明現已過期；**封存 evidence ZIP（67 entries）、BRAVO.zip 原始二進位仍未取得**。新來源分支另含兩份完整 HTML 及內網連線資訊，需保密審查。**以 [最新公開證據重查](PR93-LEASE03-PROXY-PUBLIC-EVIDENCE-RECHECK-20261105.md) 為證據可得性與保管狀態之有效裁決；舊 Gate B FAIL 及修訂 G0 PASS 均不變。**


**Decision ID:** `PR93-LEASE03-PROXY-HISTORICAL-20261105`  
**歷史裁決：** **`GATE_B_FAIL / BASELINE_BLOCKED_LIVE_QA`**（只對 **`ce7ef6c8f5c5663f41295e92a0603bca486abe98`** 與當時的 **Clips Duration = 1800** 契約）。  
**原判讀者：** Agent D；對 Lease-03 Proxy 原始證據包執行獨立回讀及雜湊檢查（2026-11-05 轉交 Controller）。  
**此文件作者的核對方式：** GitHub 上公開的歷史 v3／v4／修訂契約報告、Git commit 及 PR #93 merge；**未取得 Lease-03 Proxy 原始 ZIP／MANIFEST-LIVE／原始 GraphQL bytes，無法自行重跑 56/56**。  
**本文件性質：** 版本綁定的 Agent D 判讀歸檔與既有公開證據的交叉對照，**不是**第二次從 Proxy 原始位元組重算的獨立 QA，也不是新的 live Gate B。

## 1. 來源與版本隔離

| 對象 | 固定版本／契約 | 判定 | 意義 |
| --- | --- | --- | --- |
| PR #93 v3 原本 live 複驗 | `ce7ef6c`，**Duration 應為 1800**；lease `GATEB-PR93-LEASE-20261103-02` | **`GATE_B_FAIL`**：DEF-01 尚未修復、DEF-02 CLOSED | [歷史 v3 QA 原報告](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261103.md) |
| **本次補登：Lease-03 Proxy** | **相同 `ce7ef6c`**，**相同舊 Duration 契約**；Proxy lease-03（原始紀錄未公開） | **`GATE_B_FAIL / BASELINE_BLOCKED_LIVE_QA`** | Agent D 就 Proxy 包另行執行完整證據回讀，與 v3 同結論；**不得將兩個執行稱為兩位獨立審查者** |
| PR #93 v4 focused | `d6d6fbf`，舊 Duration 契約 | **`GATE_B_FAIL`**；DEF-01 仍 OPEN | [v4 QA](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261104-v4.md) 已附帶提及「lease-03 Proxy 包於同 HEAD 獨立重現 Duration null 6/6」 |
| PR #93 修訂範圍 | `88d27a5764c30fec1ab8bb5a325382e72a2ef09e`，`WS-2E-DEF01-DEFER-20261104`：Duration **不映射** | **`GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE`**；Duration null **符合新契約**，不代表 DEF-01 原技術問題已修復 | [修訂契約獨立 QA](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-DURATION-DEFER-QA-20261104.md) |
| PR #93 合併 | reviewed HEAD `88d27a5`，merge commit **`ff236c9e91e27321e93f59d2bf12488db714dfc7`** | **`G0_ACCEPTED_CLOSED`** | [Controller G0 post-merge 決策](https://github.com/daniel-yfc/stash-scarpers/blob/docs/pr93-def01-controller-handoff-20261104/docs/qa/PR93-G0-ACCEPTANCE-POSTMERGE-20261104.md) |

**裁決優先序：** 此舊 `ce7ef6c` FAIL 不回溯撤銷、也**不得倒灌**至已按新契約接受並合併的 `88d27a5`／G0。判定單位是「exact HEAD × 當時有效契約 × 受測範圍」，非 PR 編號本身。

## 2. Agent D 對 Proxy 包的原始判讀（待原始包公開／授權交付再重算）

以下為 Agent D 在 2026-11-05 明確交付的結果，**非本 Controller 直接檢查 Proxy 原始 bytes 的結論**：

| 區段 | Agent D 回讀結果 | 機器可讀分類 |
| --- | --- | --- |
| 完整性 | `sha256sum -c`：**MANIFEST-LIVE 56/56 OK**；`pkgbuild/BRAVO.zip` 雜湊 `cdb9d2c57ea549c9167e683f1f56dcfadcd8ad4fb672d8c496f48c5fb938de78`；ZIP 僅含 BRAVO.yml；Proxy evidence ZIP **836,389 bytes / 67 entries** | `REPORTED_VERIFIED_BY_AGENT_D`，Controller 未重算 |
| B0 安裝／路由 | installedPackages 中 BRAVO = `ce7ef6c`；**21 套件**；listScrapers 唯一 BRAVO，supported = `[URL]`、僅 Clips 路由 | `AGENT_D_B0_PASS` |
| B1/B2 | 六次 live 擷取 Title／Code／URLs 正確；284 Details **61 字**、282 Details **65 字**，產品專屬且互不相同；codepoint 比對 Details **無 U+200B**；Duration **6/6 null**（舊契約應為 **1800**）；Image 全空 | `AGENT_D_B1_B2_FAIL_DEF01`；`DEF02_CLOSED` |
| B3 Image | CDP tunnel 逾時後改採 page-HTML 證據；兩頁均無 poster 屬性，Image 空符合觀測；**poster-present 路徑未測** | `POSTER_ABSENT_OBSERVED`，`POSTER_PRESENT_UNVERIFIED_BRANCH` |
| B4 負例 | live `clips/999999`：Title／Code／Details／Duration／Image 等核心產品欄位 null；**URLs 仍回顯 canonical、9 個站台通用 Tags 仍非空**；missing-title fixture 為 repo 測試層（11 passed），lxml `$desc` 限制未當作 live 證據 | `NO_CORE_PRODUCT_IDENTITY`；**不是 all-fields-empty**，不另作此 FAIL 的主導項 |
| B5 QueryFragment | 有效 QF URL → Clips 284 正確欄位，**Duration 仍 null**；兩個空 Title 變體均安全報錯、未產生假 URL | `QF_VALID_EXCEPT_DURATION`、`FRAGMENT_NEGATIVE_SAFE_ERROR` |
| B6 控制／隔離 | KOShop 控制案 Title `ナマ狂い種壺待機`／Code `BWB365_DVD`；歷史 fixture manifest SHA 與 assignment 指定的 `be1885d2…` 前綴一致；不匹配 `/dvds/284` upstream panic 獨立分類，不歸責 PR #93 | `CONTROL_PASS_REPORTED`、`UPSTREAM_PANIC_SEPARATE` |
| 復原 | 比較表 **5/5 true**；stats 前後 **15**；lease-03 **RELEASED**；零 Scene 持久化 | `RESTORATION_VERIFIED_BY_AGENT_D` |

**唯一驅動 Gate B FAIL 的事項：** `DEF-01`，當時正式契約要求 `Duration=1800`，而 B1/B2 六次與 B5 QF 路徑均為 `null`。  
**不應重新打開的事項：** 在此包所述證據範圍內 `DEF-02 Details = CLOSED`；不應將 no-poster 情形升級為 poster-present 驗收。

## 3. Controller 能獨立交叉核實的部分

1. GitHub commit `ce7ef6c8f5c5663f41295e92a0603bca486abe98` 存在，直接 parent 是 `86e34a24642dad2e64ae984e7e9182605e98cbcf`。
2. [v3 原報告](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261103.md) 與 [v3 Handoff](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-HANDOFF-20261103.yaml) 已公開，確實記錄同 HEAD 舊契約下 DEF-01 OPEN／DEF-02 CLOSED，並列出相同**完整** BRAVO.zip SHA-256。
3. [v4 獨立 QA](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261104-v4.md) 的歷史表明文提及 Lease-03 Proxy 在 `ce7ef6c` 重現 `Duration null 6/6`，因此 Proxy 的存在／同向結論早於此份補登。
4. [修訂 Duration PASS 報告](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-DURATION-DEFER-QA-20261104.md) 明確指明 `null` 是新 omission 契約的正確結果；PR #93 GitHub 合併紀錄證明 `88d27a5` 已以普通 merge 方式進入 `ff236c9`。
5. 這些交叉對照**不能替代**對 Proxy 56 檔原始 MANIFEST／Proxy ZIP 67 entries 的檔案級讀取、SHA 重新計算及任何敏感資料去識別化檢查。

## 4. 證據保管缺口與補交契約（舊版建檔時之觀察；已有更正）

**原建檔時的查核敘述（已被後續資料更新）**：在 `docs/qa-pr93-gateb-20261103@37ea851` 並未找到 Proxy 專屬檔案；**但另有** `docs/qa-pr93-gateb-proxy-20261103@80f5307` **已公開完整 MANIFEST 與 56/56 個 referenced files，且 Controller 均重新計算 SHA-256 相符**。只有原封存 evidence ZIP、`pkgbuild/BRAVO.zip` 二進位與發布保密審查仍待補。參照[最新重查報告](PR93-LEASE03-PROXY-PUBLIC-EVIDENCE-RECHECK-20261105.md)。

未來補交原始包時，應由授權保管者依下列程序處理：

1. 提供 Proxy evidence ZIP 原件的 SHA-256、exact byte count 836,389 和 67 entries 的可重播檢查紀錄；每項值均需依原件重算，不能複製 Agent D 摘要。
2. 在**私有、隔離**環境執行 `sha256sum -c` 驗證 56 個 manifest entries 與已記載的 `pkgbuild/BRAVO.zip` digest；保留執行環境與工具版本。
3. 去識別化掃描並逐項稽核：cookies、token、API credentials、內網位址、session、含私人資料的 GraphQL 回應及完整 rendered DOM；**原始 session-bearing HTML/headers 不直接放入公開 repo**。
4. 只將經批准的 sanitized evidence、可重算 public manifest、完整 raw/private custody index 與必需的摘要報告增補於**獨立後續 commit**；任何修改須保留原文與歷史 verdict。
5. 對於缺原始 bytes 的欄位，持續標記 `NOT_INDEPENDENTLY_REHASHED_BY_CONTROLLER`；不得將此備註與 Agent D 的原始 `56/56 OK` 混淆。

詳細保管邊界：[`PR93-LEASE03-PROXY-EVIDENCE-CUSTODY-20261105.md`](PR93-LEASE03-PROXY-EVIDENCE-CUSTODY-20261105.md)。

## 5. 對後續 Gate 的影響

- **G0：** `ACCEPTED_CLOSED`（按修訂 Duration omission 契約）；**不受此舊 FAIL 影響**。
- **本歷史版本的 DEF-01：** `FAILED_AT_OLD_CONTRACT`，**不是當前版本的新缺陷**；技術修復與復原機制另由 `WS-2E-DEF01-DEFER-20261104` 管理。
- **本歷史版本的 DEF-02：** `CLOSED`。
- **Poster-present：** `UNVERIFIED_BRANCH`；不因 URL 擷取成功或 Page HTML 無 poster 而擅自關閉。
- **QueryFragment：** 本包是在 PR #93 的**歷史舊 QF 路由**上測試；不得直接引用為 PR #104 移除 QueryFragment 後的 Gate B 結論。
- **Wave 2E / PR #104：** 本文件**不是**任何 DVD Gate B PASS/FAIL、新候選版測試或合併授權。
- **Merge／Production：** 此歷史檔案不授權任何變更。

**Current historical status (superseded by linked recheck):** `PUBLIC_PROXY_MANIFEST_56_OF_56_INDEPENDENTLY_REHASHED / ORIGINAL_ZIP_BINARY_NOT_REVERIFIED / PUBLICATION_SECURITY_REVIEW_REQUIRED / HISTORICAL_GATE_B_FAIL_OLD_CONTRACT_UNCHANGED / G0_ACCEPTED_UNAFFECTED`.
