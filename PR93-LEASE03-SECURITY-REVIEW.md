---
doc_id: PR93-LEASE03-SECURITY-REVIEW-20261106
title: PR #93 Lease-03 Proxy evidence — security classification review
status: implementer_review_complete_independent_qa_pending
assignment: PR93-LEASE03-SECURITY-REMEDIATION-20261106
source_branch: docs/qa-pr93-gateb-proxy-20261103
source_head: 80f53073384214da2db902038b3e49c805a110bf
date: "2026-11-06"
---

# PR #93 Lease-03 Proxy 證據安全分類審查（Workstream S）

## 1. 範圍與方法

- 範圍：來源 HEAD `80f5307` 之 Proxy 證據全集——證據目錄 57 檔（含 `MANIFEST-LIVE.sha256`）＋ `docs/qa/` 下 5 份 Proxy 文件，共 **62 檔**，逐檔建立私有原始 SHA-256 清單（E-01 保全先行，見 Sanitization Report）。
- 工具（實際版本與命令留存於工作區）：
  - **Gitleaks 8.21.2**（`gitleaks dir <tree> --no-banner -f json`）：原始樹與去敏樹皆 **no leaks found**。
  - **自訂 12 類模式掃描**：cookie／authorization／bearer・basic／JWT／Wix session 類／api-key・token・password／Tailscale IP／RFC1918／CDP ws・json 端點／內部主機名／email／GraphQL auth／長 hex。命中 399 處，全部經人工脈絡複核。
  - **人工複核**：全部證據 JSON 的 key 清單盤點（token|cookie|auth|password|secret|session 類 key **零**）；Proxy 執行腳本（`proxy_*.py`）逐份檢查——無任何憑證、cookie 或 auth 處理，僅公開索引 URL 與一條檔案分享連結（F-03）。
- 報告不載任何疑似秘密原值；值一律以 SHA-256 前 12 碼指稱。

## 2. 分類結論（逐項詳見 FINDINGS.yaml）

| ID | 項目 | 分類 | 處置 |
| --- | --- | --- | --- |
| F-01 | stash-test 主機 Tailscale 位址（含 `:9222/json/version` CDP 端點形式），6 處 | `INTERNAL_INFRASTRUCTURE` | 公開副本去敏（已完成）；非憑證，不需輪替 |
| F-02 | 內部主機名 token，1 處 | `INTERNAL_INFRASTRUCTURE`（低） | 公開副本去敏（已完成） |
| F-03 | muse.ai 檔案分享連結（候選 index 下載用），10 處／6 檔 | `POTENTIALLY_SENSITIVE`（低） | 公開副本去敏（已完成）；效期未驗證（驗證即使用連結，未嘗試），以政策視同屆期 |
| F-04 | Wix instanceId UUID ×21（頁面 HTML） | `PUBLIC_NONSECRET` | 保留（公開頁面原始碼本有之；保留 DOM 重播保真） |
| F-05 | Wix session 識別碼（svSession／wixSession2／mpaSessionId 等） | `FALSE_POSITIVE` | 無處置；證據中**不存在任何 session 值**（見 §3） |
| F-06 | `document.cookie` 程式碼參照 | `FALSE_POSITIVE` | Wix 框架程式碼，無 cookie 值 |
| F-07 | SVG path 座標形成的 RFC1918 形字串 | `FALSE_POSITIVE` | 非位址 |
| F-08 | Sentry DSN（Wix 廠商 client 端） | `PUBLIC_NONSECRET` | 保留；範圍內無個人 email（email 類命中全為 DSN 主機名） |
| F-09 | 長 hex 字串 224 處 | `PUBLIC_NONSECRET` | manifest SHA-256、commit SHA、Wix 資產雜湊 |

**否定結果（明確記錄）**：Authorization／Bearer／Basic／JWT／API key／password 命中數 **0**；任何 request/response JSON 均無 GraphQL 認證標頭；無個人 PII。

## 3. Wix session 專項判定（對應任務 S-02 五問）

1. **是否僅為匿名元件／工作階段識別碼**：是。HTML 中只有框架程式碼內的識別碼「名稱」——Thunderbolt 綁定碼中的 cookie 名稱集合（svSession、wixSession2、wixSession3、smSession 等字串常值）與 sessionStorage 的 get/set 呼叫。
2. **是否可重用取得授權內容**：否。證據中不存在任何 session「值」；該值由瀏覽器於執行期生成。初篩曾擷出一個 14 字元「mpaSessionId 值」，經脈絡複核實為程式碼表達式 `e.mpaSessionId`（sha12 `0848c445636b`），特此記錄以免重複誤報。
3. **穩定追蹤／關聯用途**：instanceId 為頁面公開原始碼中的元件識別碼，任何訪客皆可取得；mpaSessionId 為執行期 telemetry 關聯 ID，未被擷取進證據。
4. **是否過期**：無值可言，不適用。頁面擷取為匿名抓取（Proxy 腳本無 cookie/auth 邏輯可證）。
5. **是否與可用憑證共同出現**：否，全集無憑證。

## 4. Incident Response 判定（S-03）

`NOT_REQUIRED`。無 `CONFIRMED_SECRET`、無可重用 session、無有效憑證，不啟動撤銷／輪替。F-01/F-02 為 tailnet 內部測試基礎設施位址（僅 tailnet 成員可達），處置方式為公開副本去敏＋歷史保留（Option A，待 Controller 核准）；F-03 無輪替機制，去敏並視同屆期。

## 5. Git 暴露範圍（S-04 摘要，詳見 Custody Update）

- 含證據之 commits：`3b36c43`、`ed93399`、`3e09b91`、`80f5307`，**僅**由分支 `docs/qa-pr93-gateb-proxy-20261103` 可達，無其他分支包含。
- Repo 為 public；**forks = 0**（2026-11-06 以 GitHub API 查核）。
- 暴露窗口：自 2026-11-05 發布起，任何人皆可讀取該分支。因內容分類無秘密，歷史重寫（Option B）不成比例；且須如實記錄：即使重寫，GitHub 仍可能經 commit SHA 直接存取舊物件一段時間，快取／已被他人 clone 的副本無法回收。
- **建議 Option A**：保留歷史、另行發布去敏證據集並標示公開使用版本；Option B 僅在 Controller 將 F-01 升級分類時啟動，且 force-push／刪分支須另行批准（本任務未執行任何歷史操作）。

## 6. 邊界聲明

本審查為修復者（implementer）執行之分類與處置；最終安全 QA 裁決保留予獨立 Reviewer（見 SECURITY-QA 文件）。未執行 force-push、刪除、合併或部署；未以重播方式驗證任何可能有效之秘密；未觸及現行 Stash scraper 或 PR #104 Gate B 工作。
