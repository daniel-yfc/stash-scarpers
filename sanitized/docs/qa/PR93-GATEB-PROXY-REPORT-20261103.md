---
doc_id: QA-PR93-GATEB-PROXY-20261103
title: PR #93 Gate B Proxy Evidence Package and Agent D Verdict (frozen HEAD ce7ef6c)
date: 2026-11-05
status: complete
scope: PR #93 (fix/e2e-bravo-clips) at frozen HEAD ce7ef6c8f5c5663f41295e92a0603bca486abe98 only
---

# PR #93 Gate B — Proxy 執行證據包與 Agent D 判讀

## 裁決

- **GATE_B_FAIL / BASELINE_BLOCKED_LIVE_QA**（Agent D 獨立判讀，2026-11-05）
- 唯一驅動項：**DEF-01** — Duration 在 B1/B2 六次擷取與 B5 QueryFragment 路徑全為 null，不符本 assignment 當時有效的驗收值 1800。
- DEF-02（Details 污染）在本包證據下 **CLOSED**。

## 範圍綁定（必讀）

本裁決只對凍結 HEAD `ce7ef6c8f5c5663f41295e92a0603bca486abe98` 與當時契約（Duration 驗收值 1800）成立。其後 HEAD `88d27a5` 已在修訂後契約（Duration 不對映、Controller defer 決策 WS-2E-DEF01-DEFER-20261104）下通過 focused 重跑，PR #93 亦已合併 — **本 FAIL 不得解讀為現行版本的 Gate B 結果**。

## 執行摘要

- Lease：`GATEB-PR93-LEASE-20261103-03`（stash-test 專用；執行後已釋放，rollback 經 5/5 比對驗證，零 Scene 持久化）。
- 候選：BRAVO.zip SHA-256 `cdb9d2c57ea549c9167e683f1f56dcfadcd8ad4fb672d8c496f48c5fb938de78`，僅含 BRAVO.yml，於 exact HEAD 獨立重建（第三次重建，digest 一致），verify-only OK；installedPackages 驗明 BRAVO = ce7ef6c（隔離來源）。
- B1/B2：clips/284、282 各 3 次獨立擷取，Title/Code/URLs 全對；Details 61 字／65 字、產品專屬、互不相同、無 U+200B；Duration 6/6 null；Image 全空。
- B3：poster-present 分支 **UNVERIFIED_BRANCH**（兩頁 video 皆無 poster 屬性，Image 全空、無無關圖）。
- B4：live 999999 核心欄位全 null（fail-closed 成立），僅 URLs 回顯 + 站台通用 Tags。
- B5：QF 有效路徑回 284 正確結果；兩個空 Title fragment 變體皆安全報錯，無假 URL。
- B6：KOShop 控制案回凍結值（41979 → Title ナマ狂い種壺待機、Code BWB365_DVD）；fixture manifest SHA 與指定值一致；/dvds/284 upstream panic 獨立分類，未歸責 PR #93。

## Agent D 獨立驗證

Agent D 未採信 handoff 摘要，自行重跑 MANIFEST-LIVE sha256（56/56 OK）、逐筆回讀 B1/B2 原始 response、另做 codepoint 檢查確認無 U+200B、核對 rollback restoration-comparison 五項全 true 與 stats 前後同為 15。判讀全文見 `PR93-GATEB-PROXY-VERDICT-20261105.md`。本判讀與 Agent D 本人 v3 裁決（同 HEAD、GATE_B_FAIL）結論一致，但各自立基於獨立證據，屬互相印證而非互相引用。

## 本目錄檔案

- `PR93-GATEB-PROXY-HANDOFF-20261104.yaml` — Proxy 正式 handoff（裁決欄位 RESERVED_TO_AGENT_D）。
- `PR93-GATEB-PROXY-LEASE-RECORD-20261103-03.md` — lease -03 紀錄。
- `PR93-GATEB-PROXY-VERDICT-20261105.md` — Agent D 判讀全文。
- `evidence/pr93-gateb-proxy-20261103/` — 原始證據 56 檔 + `MANIFEST-LIVE.sha256`（B0–B6、ROLLBACK、RUN-LOG、執行腳本）。
