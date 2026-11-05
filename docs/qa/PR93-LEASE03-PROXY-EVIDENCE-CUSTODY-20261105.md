---
doc_id: PR93-LEASE03-PROXY-EVIDENCE-CUSTODY-20261105
title: PR #93 Lease-03 Proxy evidence custody / publication gap
status: partial_public_evidence
layer: qa
owner: controller
audience: [maintainer, agent, auditor]
last_verified: "2026-11-05"
authority: evidence_index
---

# PR #93 — Lease-03 Proxy 證據保管與公開界線

**Referenced historical candidate:** `ce7ef6c8f5c5663f41295e92a0603bca486abe98`  
**Decision:** [`PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105.md`](PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105.md)  
**Purpose:** 避免誤把 Agent D 已做的原始包驗證，記為本次 Controller 已對同一原件完成第二次雜湊／資料敏感性審核。

## 1. 已可交叉核對的公開來源

| 來源 | 可公開核對的事實 | 不可替代的事項 |
| --- | --- | --- |
| [原 v3 QA @ ce7ef6c](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261103.md) | 舊 Duration=1800 契約下 `GATE_B_FAIL`、DEF-02 CLOSED；BRAVO.zip 完整 SHA-256 `cdb9d2c57ea549c9167e683f1f56dcfadcd8ad4fb672d8c496f48c5fb938de78` | 它是**v3 自身**的 live QA，不能證明本次 Proxy ZIP 67 entries 全部存在或逐項吻合 |
| [原 v4 QA @ d6d6fbf](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261104-v4.md) | v4 歷史表提前記錄「lease-03 Proxy 包於 `ce7ef6c` 獨立重現 Duration null 6/6」 | 這不是該 Proxy 包公開的 `MANIFEST-LIVE` |
| [修訂契約 PASS @ 88d27a5](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-DURATION-DEFER-QA-20261104.md) | Duration omission 新契約下 PASS，Null 為 expected | 不得拿來證明舊 Duration=1800 契約通過 |
| [PR #93 merge](https://github.com/daniel-yfc/stash-scarpers/pull/93) | accepted merge commit `ff236c9`，來源 HEAD `88d27a5` | 不會回溯修正舊 `ce7ef6c` 的 FAIL |

## 2. Proxy 原始物件之目前保管狀態

Agent D 轉交紀錄中，Proxy 專屬項目為：

| 物件 | Agent D 所述 | Controller 本輪狀態 |
| --- | --- | --- |
| `MANIFEST-LIVE`（Proxy 56 entries） | `sha256sum -c`：56/56 OK | **未提供原始 manifest bytes；NOT_REHASHED** |
| `pkgbuild/BRAVO.zip` | `cdb9d2c57ea549c9167e683f1f56dcfadcd8ad4fb672d8c496f48c5fb938de78`，ZIP 只有 BRAVO.yml | v3 公開報告有相同 digest；**此 Proxy 實體 ZIP 未下載/重新雜湊** |
| Evidence ZIP | 836,389 bytes、67 entries | **未取得 ZIP；byte count/entry count 由 Agent D 報告** |
| B1/B2/B4/B5/B6 raw GraphQL | Agent D 表示逐筆回讀 | **Proxy 原始回應未接入 Controller**；本次報告以 Agent D 的具體結果為引述 |
| Poster-present source | Agent D 表明 CDP tunnel 逾時、Page HTML 無 poster | **poster-present 仍 `UNVERIFIED_BRANCH`** |
| Rollback comparison | 5/5 true，stats 15→15，lease-03 released | **本次未操作 Stash，無法親自查驗歷史 lease 狀態** |

**嚴禁替代驗證：** v3 的 `live-run2/MANIFEST-LIVE2.sha256`、v4 的 `MANIFEST-LIVE3.sha256` 與修訂契約的 `MANIFEST-REPO.sha256` **均為不同輪次**，不能冒稱 Proxy 的 `MANIFEST-LIVE 56/56`。

## 3. 若要將 Proxy 原始證據也補齊

1. 經授權的證據保管者在私有環境提供 Proxy ZIP 與其完整 SHA-256、原始 `MANIFEST-LIVE` 及 manifest 所引用相對路徑。原件必須先通過完整性／檔案結構檢查，不得假定 836,389 bytes／67 entries 永遠正確。
2. 另一位具權限的 QA 在該**同一份原始輸入**重新執行 `sha256sum -c`、逐一驗證 56/56、獨立取得 ZIP entry list 並重算 BRAVO.zip digest。記錄工具版本、執行時間、清單與結果摘要。
3. 對 GraphQL payload、request、headers、瀏覽器 HTML、CDP 事件及 log 進行秘密掃描、遮罩與人員覆核。**原始 cookie、token、tailnet URL、session-bearing HTML 等私密材料不得上傳至公開 Repository。**
4. 保存未去敏原件於受控空間（獨立 custody 與 access record）；Repo 僅上架可重算的公開去敏檔案、manifest、原始證據 digest index、test matrix 與審查記錄。
5. 若原始保管者無法提供該包，保持 `HISTORICAL_VERDICT_ARCHIVED_WITH_RAW_PROXY_EVIDENCE_GAP`，不得標示為完整公開證據鏈或已由 Controller 重算。

**本次 Repo 歸檔範圍：** Decision Record + YAML Handoff + Custody Note。沒有新增、搬運或宣稱公開原始 Proxy ZIP。沒有更改 `scrapers/BRAVO.yml`、PR #93 已合併提交、Stash 生產環境。
