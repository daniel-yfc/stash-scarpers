---
doc_id: PR93-LEASE03-SANITIZATION-REPORT-20261106
title: PR #93 Lease-03 Proxy evidence — preservation, sanitization and revalidation
status: sanitized_set_prepared_locally_not_published
assignment: PR93-LEASE03-SECURITY-REMEDIATION-20261106
source_head: 80f53073384214da2db902038b3e49c805a110bf
date: "2026-11-06"
---

# 去敏與證據保全報告（Workstream E）

## E-01 來源保全紀錄（修改任何公開內容之前完成）

| 項目 | 結果 |
| --- | --- |
| Pin 原始 commit | `docs/qa-pr93-gateb-proxy-20261103` HEAD = `80f53073384214da2db902038b3e49c805a110bf`（遠端讀回確認） |
| 範圍檔案 | 62 檔（證據目錄 57 ＋ Proxy 文件 5），逐檔 SHA-256 存於私有清單 `PRIVATE-RAW-MANIFEST.sha256`（本地受控工作區，不公開原值以外之雜湊對照見 E-04） |
| `MANIFEST-LIVE.sha256` 條目數 | **56** 條（manifest 本身為第 57 檔，不列自身） |
| 原始 bytes manifest 驗證 | `sha256sum -c` → **56/56 OK**（本輪以 checkout 之原始 bytes 重驗；與 Controller 先前 56/56 結論一致，此為修復者複核） |
| 原始證據存放 | 公開 Git 歷史（來源分支）＋本工作區唯讀 checkout 副本 `raw-80f5307/`（本地受控空間，保管責任：本 agent 工作區；存取限本機） |
| 假設澄清 | 原始封存 ZIP（67 entries／836,389 bytes）與 `pkgbuild/BRAVO.zip` 二進位**仍未取得**，不假設本地備份存在；本保全僅及於公開分支之 62 檔 |

## E-02 去敏轉換（62 檔中 12 檔有轉換，50 檔逐字節相同複本）

| 轉換 | 規則 | 檔數 |
| --- | --- | --- |
| `tailnet_ip_redacted` | F-01 位址 → `REDACTED-TAILNET-IP`（保留 URL/JSON 語法有效性） | 6 |
| `internal_hostname_redacted` | F-02 主機名（附連接埠脈絡）→ `stash-test-host` | 1 |
| `file_share_url_redacted` | F-03 分享連結 → `https://REDACTED-FILE-LINK.invalid/gateb-index3.yml` | 6 |
| `manifest_regenerated_for_sanitized_bytes` | 去敏樹之 `MANIFEST-LIVE.sha256` 以去敏後 bytes 重新產生（56 條） | 1 |

**頁面 HTML 處置（明確決策）**：兩份 B3 HTML 經分類後**不需轉換、逐字節保留**——證據中不存在 session 值（F-05 FALSE_POSITIVE）、instanceId 屬公開非秘密（F-04）、Sentry DSN 為廠商公開值（F-08）。因此「公開最小重播 DOM」與原始 DOM 相同，不另造摘要版，以免破壞 XPath 重播；私有原始 DOM 與公開版之對照即對照表中的 `none (byte-identical copy)`。

## E-03 重新驗證（去敏後）

| 檢查 | 結果 |
| --- | --- |
| JSON 解析（原始＋去敏全數 JSON） | **0 失敗** |
| XPath 重播（BRAVO_JAPAN 現行 clips selectors：Title／Code／URLs／Tags／Details／poster img）於 282、284 兩頁 | 原始 vs 去敏 **完全相同**；Title／Code／URLs／Tags／Details 均正確擷出；poster img 為空，與 `POSTER_ABSENT_OBSERVED` 一致 |
| 轉換後 JSON 語義比對（6 檔，原始經同一去敏規則後解析比對） | **全數相等**（僅去敏葉節點不同） |
| 去敏 manifest 完整性 | `sha256sum -c`（去敏樹）→ **56/56 OK** |
| Secret scan（去敏樹） | Gitleaks 8.21.2：no leaks；自訂掃描：Tailscale IP 命中 **0**（殘留命中皆為已分類之公開／誤報類與去敏標記字串本身） |
| 欄位一致性 | field-summary／poster-check 等未轉換檔逐字節相同，結果與原始證據一致 |

**迴歸事件（誠實記錄）**：首版去敏曾使 2 份 JSON 解析失敗——分享連結正規式誤吞跳脫引號前的反斜線，破壞字串邊界。已修正（排除反斜線於 URL 字元類）並全量重跑，上表結果為修正後版本；修正前產物已棄置，未交付。最終狀態：**無 SANITIZATION_REGRESSION**。

## E-04 雙層 Manifest

- **Private Raw Manifest**：`PRIVATE-RAW-MANIFEST.sha256`（62 條，原始 SHA-256）——存本地受控工作區，不隨公開集發布。
- **Public Sanitized Manifest**：`PUBLIC-SANITIZED-MANIFEST.sha256`（62 條，去敏後 SHA-256）；去敏證據目錄內另含重產之 `MANIFEST-LIVE.sha256`（56 條，與原始 manifest 分屬不同 bytes，雜湊不同——屬預期且已於對照表標明）。
- **對照表**：`ORIGINAL-TO-SANITIZED-MAPPING.csv`，欄位 `original_path → original_sha256 → sanitized_path → sanitized_sha256 → transformation`（62 列）。原始雜湊未被標示為去敏檔雜湊。

## 交付位置

去敏證據集與全部報告目前僅存於本地受控工作區 `~/workspace/pr93-lease03-remediation-20261106/`；依授權邊界，**未推送**至 `security/pr93-lease03-evidence-remediation-20261106` 或任何公開分支——推送須待獨立安全 QA 通過並經 Controller 批准。
