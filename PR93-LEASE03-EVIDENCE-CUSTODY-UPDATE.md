---
doc_id: PR93-LEASE03-EVIDENCE-CUSTODY-UPDATE-20261106
title: PR #93 Lease-03 Proxy — custody correction and exposure decision (2026-11-06)
status: prepared_locally_pending_controller_and_independent_qa
assignment: PR93-LEASE03-SECURITY-REMEDIATION-20261106
supersedes_status_of:
  - PR93-LEASE03-PROXY-EVIDENCE-CUSTODY-20261105
  - PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105
  - PR93-LEASE03-PROXY-HISTORICAL-HANDOFF-20261105.yaml
date: "2026-11-06"
---

# Custody 更正與 Git 暴露處置（Workstream D + S-04）

## 1. 與現況對齊的七項事實（對應任務 D-01）

1. **Proxy 原始證據已存在於專屬 GitHub 分支**：`docs/qa-pr93-gateb-proxy-20261103@80f5307`（4 commits：`3b36c43`、`ed93399`、`3e09b91`、`80f5307`），僅該分支可達。
2. **先前「未發現 Proxy 原始證據」屬當時查核限制**：歸檔文件原建檔時只查了 v3 分支；同日重查已更正此點，本文件確認該更正脈絡保留、不無聲覆寫。
3. **`MANIFEST-LIVE.sha256` 已發現**：位於證據目錄根，**56 條**。
4. **原始檔案完整重算**：Controller 先前已重算 56/56 PASS；本輪修復者以來源 HEAD 原始 bytes 再驗 `sha256sum -c` → **56/56 OK**（兩次獨立讀取一致）。
5. **公開版本安全去敏審查**：本輪完成分類（無 `CONFIRMED_SECRET`；F-01/F-02 內部基礎設施、F-03 潛在敏感分享連結）並已備妥去敏證據集（本地，未發布）；**是否「通過」由獨立安全 QA 裁決，本文件不自證**。歸檔三文件原標記之 `security_review_pending` 應更新為 `security_classification_complete_sanitized_set_prepared_independent_qa_pending`。
6. **歷史 `ce7ef6c` Gate B FAIL 不變**（舊 Duration=1800 契約）。
7. **修訂契約 `88d27a5` PASS 與 G0 ACCEPTED_CLOSED 不受影響**。

## 2. 仍未關閉的保管缺口（不因本輪工作而改變）

- 原始封存 evidence ZIP（67 entries／836,389 bytes，Agent D 報告值）**仍未取得、未重驗**。
- `pkgbuild/BRAVO.zip` 二進位**仍未直接重算**（digest 僅見於報告互引）。
- Poster-present 路徑仍 `UNVERIFIED_BRANCH`。
- 三文件之修訂：本工作區已備妥三份文件的更正版（加入 2026-11-06 補登段落，歷史裁決文字不動），**未推送**至歸檔分支——待 Controller 批准與獨立 QA 後，方以新 commit 增補（比照歸檔分支既有「同日重查」補登慣例）。

附帶發現（版本對照）：任務書所載歸檔分支 HEAD `99692af` 為現行遠端 HEAD `96f7194` 之祖先（遠端已多一 commit）；更正版以現行 `96f7194` 內容為基底，並記錄此差異。

## 3. Git 暴露分析與處置建議（S-04）

- 可達性：含證據 commits 僅由 `docs/qa-pr93-gateb-proxy-20261103` 可達；無 tag 指向；repo public、**forks = 0**（2026-11-06 API 查核）；PR 留言中之引用屬文字連結，不含證據原值（本輪另於 PR #93 追加更正留言，見 D-02）。
- **Option A（建議）**：內容經分類無秘密 → 保留原始歷史；另行發布去敏證據集（本輪已備妥）並 clearly 標示公開使用版本；歸檔文件補登安全分類結論。比例原則與證據可信度俱合。
- **Option B（備案）**：僅當 Controller 將 F-01（tailnet 位址）升級為必須撤除時啟動——先完成證據保全（已完成 E-01）與秘密撤銷評估（F-01 無可撤銷之憑證），再規劃受控歷史清理。限制如實記錄：force-push 後 GitHub 仍可能經舊 commit SHA 直接存取物件至回收為止；已 clone 副本不可回收；PR refs 與快取不在 repo 控制內。**未經 Controller 明確批准，不執行 force-push 或刪分支（本輪未執行）。**

## 4. 不受影響聲明

本更正不觸及 PR #93 已合併程式碼、現行 G0／G1 裁決與 PR #104 Gate B 工作；無生產操作、無合併、無部署。
