---
doc_id: PR93-LEASE03-INDEPENDENT-SECURITY-QA-20261106
title: PR #93 Lease-03 Proxy — independent security QA report
status: independent_qa_complete
assignment: PR93-LEASE03-INDEPENDENT-SECURITY-QA-20261106
remediation_assignment: PR93-LEASE03-SECURITY-REMEDIATION-20261106
reviewer: Independent Security Reviewer (different agent from the implementer)
source_branch: docs/qa-pr93-gateb-proxy-20261103
source_head: 80f53073384214da2db902038b3e49c805a110bf
date: "2026-11-06"
verdict: SECURITY_QA_PASS_WITH_NONBLOCKING_FINDINGS
---

# PR #93 Lease-03 Proxy 去敏證據集 — 獨立安全 QA 報告

## 0. 裁決與綁定

**FINAL VERDICT：`SECURITY_QA_PASS_WITH_NONBLOCKING_FINDINGS`**

本裁決綁定以下受測檔案（QA 當日實測值）：

| 綁定對象 | SHA-256 / 值 |
| --- | --- |
| 受審包 ZIP `PR93-LEASE03-SANITIZED-PACKAGE-20261106-v1_0_7bge.zip` | `b0fd77315a8a2921b349abb8448a413b1f8a4a5ebc6d0de8131cab28246414dc` |
| 原始來源 HEAD `docs/qa-pr93-gateb-proxy-20261103` | `80f53073384214da2db902038b3e49c805a110bf` |
| `PUBLIC-SANITIZED-MANIFEST.sha256`（去敏 62 檔清單） | `18364466539f207d597fecd86a2a29ffdc58e015b577bbd00318600809e414fd` |
| `PRIVATE-RAW-MANIFEST.sha256`（原始 62 檔清單） | `335a6e0aece0b3344679fdbd8bae3d68924a529346cdb2d951cefe50abbd30a5` |
| `ORIGINAL-TO-SANITIZED-MAPPING.csv`（62 列對照） | `aa48aa5c390f74adfe70b3faeb3c7c57e968ac5420fccfb86d454fff7b019ba5` |
| 去敏 `MANIFEST-LIVE.sha256`（56 條） | `d792b5f4a93782e9d4342e19ee17e9a1ed561170cecd7c130bcee71415175960` |
| 原始 `MANIFEST-LIVE.sha256`（56 條） | `17d85c2ef6eb53d8bd443e9297bf9e1e25d5b1d5b66e559873f9eff04b6859bd` |
| B3 `page-html-282.html`（原始＝去敏，逐字節相同） | `95582b3040fc0ac43853c7c07866d212c3fd66aeb23de16a11b0c8928e664491` |
| B3 `page-html-284.html`（原始＝去敏，逐字節相同） | `02f6c134020fdaf8597efc58f869a9fd7633581a25647706028684ab6fbdfd3a` |

發布條件（見 §6）：N1 更正須於發布前／發布時記錄於本報告與 custody 補登；N2–N5 一行文字更正於 custody 文件提交時一併修正；僅發布上述清單綁定之去敏集；推送仍須 Controller 另行批准。

## 1. 獨立性與邊界聲明

- 本審查由不同於修復者（implementer）的 Reviewer 執行；修復者自查結論（`PR93-LEASE03-SECURITY-QA.md` 自查表）僅作對照，**未直接採信**，全部關鍵檢查均自來源 HEAD 重新獨立執行。
- 原始證據取自遠端來源分支 pin HEAD `80f5307` 之唯讀 worktree；未修改原始證據分支，未 force-push、未合併、未操作 Stash，未部署。
- 未以任何方式存取 F-03 muse.ai 分享連結（無授權存取私人內容；效期以政策視同屆期，見 §2）。
- 報告內不載任何疑似秘密原值；值一律以 SHA-256 前 12 碼指稱。尾網位址、分享連結原值、主機名原值皆不重述。
- 工具：Gitleaks 8.21.2（QA 自行下載之同版本二進位，獨立安裝）、自撰模式掃描（與修復者不同的 regex 集）、自撰 XPath 重播（selector 直接讀自來源 HEAD 之 `scrapers/BRAVO_JAPAN.yml`）、repo 自帶 `tools/scan_session_material.py`（來源 HEAD 版本）。

## 2. A. 安全分類複核

### 2.1 掃描範圍與結果（獨立重跑）

| 掃描 | 原始樹 | 去敏樹 | 與修復者主張對照 |
| --- | --- | --- | --- |
| Gitleaks 8.21.2 `gitleaks dir` | no leaks found | no leaks found | 一致 |
| 修復者 12 類掃描腳本（重跑） | 399 命中 | 398 命中 | 見 N4：報告稱「399 處」未標樹；交付之 JSON 為去敏樹 398 |
| QA 自撰掃描（18 類，見 QA-TEST-RECORD） | Authorization／Bearer／Basic／JWT／API key／password／secret／私鑰 PEM／cookie 值／GraphQL 認證標頭／AWS key／GitHub token 命中皆 **0** | 同左，皆 **0** | 一致；`CONFIRMED_SECRET = 0` 成立 |

### 2.2 逐項複核

| ID | 修復者分類 | QA 複核 | 結論 |
| --- | --- | --- | --- |
| F-01 | Tailnet 位址＋CDP 端點，6 處，`INTERNAL_INFRASTRUCTURE` | 6 處位置逐一核對（Handoff yaml:9、RUN-LOG:10、post-rollback-packages:29、rollback-log:122、scene-stats-after:29、scene-stats-before:29），與 FINDINGS.yaml 完全一致；去敏樹該類命中 0 | CLOSED：處置正確，非憑證，不需輪替 |
| F-02 | 內部主機名 token，1 處，`INTERNAL_INFRASTRUCTURE`（低） | 僅 Handoff yaml:9 一處；去敏樹同位置為 `stash-test-host` 標記 | CLOSED：處置正確 |
| F-03 | muse.ai 分享連結，10 處／6 檔，`POTENTIALLY_SENSITIVE`（低） | 分布逐一核對：install-record.json ×5、installedPackages.json ×1、rollback-log.json ×1、gateb-index3.yml ×1、proxy_install.py ×1、proxy_rollback.py ×1，共 10；去敏樹 0；連結未存取；其用途（候選 index 下載）由 gateb-index3.yml 檔案結構本身證實，內容為 scraper index，非使用者資料 | CLOSED：去敏＋視同屆期可接受；無輪替機制，無 IR |
| F-04 | Wix instanceId UUID，`PUBLIC_NONSECRET`，保留 | 兩頁共 40 處、去重後 **19 個** distinct UUID（兩種獨立擷取一致），修復者稱 21 個有誤，見 N2；皆為頁面公開原始碼之元件識別碼，任何訪客皆可取得 | CLOSED（數字更正 N2）：保留正確 |
| F-05 | Wix session 識別碼，`FALSE_POSITIVE`，稱「不存在任何 session 值」 | **主張不成立，見 QA-N1（§2.3）**；其餘部分成立：svSession／wixSession2／wixSession3／smSession 僅名稱、無值；mpaSessionId 僅程式碼表達式、無值 | **OPEN（文件更正，N1）**：須改分類，見 §2.3 |
| F-06 | `document.cookie` 程式碼參照，`FALSE_POSITIVE` | 兩頁 L87 為 Wix Thunderbolt `handleAccessTokens` bundle script 標籤＋框架程式碼；全樹無 set-cookie／cookie 值（QA 掃描 0） | CLOSED |
| F-07 | RFC1918 形字串，`FALSE_POSITIVE` | 兩頁 L843 為 SVG `<path d="M523.2 259a39 39 …">` 座標資料，非位址 | CLOSED |
| F-08 | Sentry DSN，`PUBLIC_NONSECRET`，保留 | 全部 email 形命中皆為 Sentry DSN URL（`https://<32ch>@sentry.io`／`sentry.wixpress.com`），廠商 client 端公開值；無個人 email | CLOSED：保留正確 |
| F-09 | 長 hex 224 處，`PUBLIC_NONSECRET` | 兩樹重跑皆為 **216** 處（修復者腳本重跑＋交付 JSON 一致），修復者稱 224 有誤，見 N3；內容為 manifest SHA-256、commit SHA、Wix 資產雜湊 | CLOSED（數字更正 N3） |

### 2.3 QA-N1（本次審查唯一實質發現）：F-05「不存在 session 值」不成立

**事實（QA 獨立重現，三種工具交叉）：**

- 兩份 B3 Page HTML 各含 **2 處**帶引號的 `"sessionId":"<UUID>"`（L880、L952），值為 36 字元 UUID 形字串：
  - page-282：sha12 `a7d1adab33a0`（兩處相同）
  - page-284：sha12 `dffb3e73c870`（兩處相同）
- 該值位於 Wix viewerModel site 描述子物件內，同物件並列 `metaSiteId`、`siteId`、`externalBaseUrl: https://www.bravo-japan.com`、`siteType: UGC`、`dc: virginia-pub`、`editorName: Unknown`、`isSEO: false` 等公開站點詮釋資料——即任何匿名訪客開啟該公開頁面即收到的頁面原始碼。
- 修復者 12 類掃描的 `wix_session` 78 命中中包含此 4 處，但人工分類時誤判為僅名稱／程式碼；repo 自帶 `tools/scan_session_material.py`（來源 HEAD 版）獨立標示兩份 HTML 為 `REPLAYABLE_AUTH_ASSIGNMENT`，QA 以結構化探針（僅鍵名＋值形狀，不載原值）確認即此 4 處。

**為何不是秘密（四點證據）：**

1. **逐次載入不同值**：282 與 284 於同一 proxy 執行輪次內先後匿名抓取，所得 sessionId UUID 不同。穩定憑證不會在同輪次內逐頁更換；此為每次載入新生的匿名識別碼。
2. **匿名取得、無授權脈絡**：Proxy 腳本無 cookie／auth 處理（逐份檢查確認）；該 UUID 發給匿名請求，本身不授予逾越匿名的存取。
3. **公開描述子的一部分**：與 `metaSiteId`／`siteId` 等公開站點詮釋資料同物件，任何訪客皆可取得；非會員認證用途。Wix 會員認證用 svSession cookie，其值全證據集皆不存在。
4. **全證據集無授權使用痕跡**：無任何 request／response JSON 以該值作認證標頭或 cookie（QA 掃描 Authorization／cookie 類皆 0；B1／B2 回應 JSON 已逐筆核對）。

**更正後分類：`PUBLIC_NONSECRET`（匿名、逐次載入之 telemetry／BI 工作階段關聯 ID），去敏集保留，理由如上。** 不需去敏、不需輪替（無可輪替之穩定憑證；值本身已隨時間失效）、不需 Incident Response。

**處置要求（非阻擋）：** 發布前／發布時，F-05 紀錄須改為上述更正分類與理由（本報告即為更正紀錄；custody 補登應載明）。`sanitize.py` 未設 sessionId 規則（僅 mpaSessionId 規則，且該規則命中 0，正確），故去敏 bytes 不需重做；此為文件更正，非證據重製。

## 3. B. 證據完整性（獨立重跑，全部通過）

| # | 檢查 | QA 結果 |
| --- | --- | --- |
| B1 | 原始 `MANIFEST-LIVE` 56/56 驗證（來源 HEAD 原始 bytes） | **56/56 OK，0 失敗** |
| B2 | 原始 62 檔 SHA-256 manifest 驗證（`PRIVATE-RAW-MANIFEST.sha256` 對來源 HEAD） | **62/62 OK，0 失敗** |
| B3 | 去敏 62 檔 SHA-256 manifest 驗證（`PUBLIC-SANITIZED-MANIFEST.sha256` 對去敏樹） | **62/62 OK，0 失敗**；去敏 `MANIFEST-LIVE` 另計 **56/56 OK** |
| B4 | 12 檔已轉換／50 檔 byte-identical 核對 | **12／50，與對照表一致**；轉換細目：tailnet 6 檔（含 1 檔併主機名）、share-link 6 檔（含 2 檔併 tailnet／主機名）、manifest 重產 1 檔 |
| B5 | 62 列原始／去敏 SHA 對照 | **62 列全數與重算值相符，0 不符**；「claimed-identical 卻不同」「claimed-transformed 卻相同」皆 0；原始雜湊未被標示為去敏雜湊 |
| B6 | JSON parse 及 schema 檢查 | 原始＋去敏各 **39 份 JSON，0 解析失敗**；此前損壞的 2 份 JSON，交付版皆為修正後版本（全數可解析；6 份轉換 JSON 對原始套用同一去敏規則後語義相等） |
| B7 | 原始與去敏 XPath expected／actual 重播 | **282／284 兩頁，Title／Code／URLs／Tags／Details／poster 皆原始＝去敏**；且與 `field-summary.json` 預期值逐項相符（title、code、urls、details_len、tags_n、image null、details 前綴）；修復者 `validate_sanitized.py` 亦重跑通過 |
| B8 | 去敏後再次 secret scan | Gitleaks 8.21.2（QA 獨立安裝）原始／去敏兩樹皆 **no leaks found**；QA 自撰掃描去敏樹：tailnet IP **0**、分享連結 **0**（殘留命中僅為已分類公開／誤報類與去敏標記字串本身，如 `REDACTED-TAILNET-IP` 觸發 internal_host 模式、`:9222/json/version` 路徑字串） |

## 4. C. 發布安全

- 兩份 Page HTML 在去敏集**逐字節保留**（SHA 與原始相同，見 §0 綁定表）。保留理由：經 §2 複核，HTML 內無 Authorization／JWT／API key／cookie session 值／私鑰；僅有的 session 類**值**為 QA-N1 之匿名 telemetry sessionId UUID（已更正分類為 `PUBLIC_NONSECRET`，保留理由見 §2.3）。
- 去敏後殘留資訊清單（皆有分類與理由）：
  - Wix `sessionId` UUID（各頁 1 個 distinct 值，2 處）：`PUBLIC_NONSECRET`，匿名逐次載入 telemetry ID，公開頁面原始碼本有之。
  - Wix `instanceId` UUID（19 distinct）：`PUBLIC_NONSECRET`，公開元件識別碼；保留以維持 DOM／XPath 重播保真。
  - Sentry DSN（含 32 字元公開 key）：`PUBLIC_NONSECRET`，廠商 client 端公開值， shipped JS 本有之。
  - CDP 路徑字串（`:9222/json/version` 等，6 處）：去敏後僅餘通用路徑、無主機位址；CDP 路徑為公開知識，無主機不可達。保留為重播保真（屬 F-01 處置之設計選擇，非遺漏）。
  - 去敏標記字串本身（`REDACTED-TAILNET-IP`、`stash-test-host`、`https://REDACTED-FILE-LINK.invalid/gateb-index3.yml`）：標記，非原值。
- 去敏樹確認無殘留：Tailnet 位址 0、分享連結原值 0、內部主機名原值 0（僅餘 `stash-test-host` 標記）、個人 PII 0。

## 5. D. Git 歷史決策 — Option A 建議成立

**建議：`KEEP_HISTORY + PUBLISH_SANITIZED_EVIDENCE`（Option A）。**

獨立查核：

- 含證據 commits（`3b36c43`、`ed93399`、`3e09b91`、`80f5307`）於全量 50 個遠端分支＋全部 tags 查核後，**僅**由 `docs/qa-pr93-gateb-proxy-20261103` 可達；無 tag 指向。
- Repo 為 public；**forks = 0**（2026-11-06 GitHub API 實查：`forks_count: 0`，forks 列表 0 筆）。
- 內容經分類無 `CONFIRMED_SECRET`（§2），歷史重寫（Option B）不成比例；且重寫亦不能可靠回收已發布內容。

**必須如實記錄的限制（本 QA 之條件）：**

- 舊版本仍可由 Git commit SHA 直接取得（`80f5307` 等四個 commit），即使未來刪除分支，GitHub 仍可能經舊 commit SHA 直接存取物件一段時間。
- **forks = 0 不能排除既有下載副本**：任何人於 2026-11-05 發布後皆可 clone 該分支；本地副本無法回收。Option A 的前提是內容分類無秘密（成立），而非「無人取得」。
- F-01 位址已存在於公開歷史與其他已公開文件脈絡；本去敏僅作用於本證據集之公開副本，不主張全域撤除。
- Option B 僅在 Controller 將 F-01 升級分類時啟動；force-push／刪分支須另行批准，本輪未執行任何歷史操作。

## 6. E. 歷史稽核 — 更正版三份 custody 文件

以 `diff` 對 archive 分支現行 HEAD `96f7194` 之原件逐份比對：

| 文件 | 比對結果 |
| --- | --- |
| `PR93-LEASE03-PROXY-EVIDENCE-CUSTODY-20261105.md` | 僅 status 行更新（`security_review_pending` → `security_classification_complete_sanitized_set_prepared_independent_qa_pending`）＋附加一段 2026-11-06 補登；歷史文字未動 |
| `PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105.md` | 僅附加一段 2026-11-06 補登；歷史文字未動。惟補登句「狀態由 `security_classification_complete_…` 更新為 `security_classification_complete_…`」為同值重述（QA-N5），該文件 status 行原本即非 `security_review_pending`，須修正措辭 |
| `PR93-LEASE03-PROXY-HISTORICAL-HANDOFF-20261105.yaml` | 僅附加 `SECURITY_REMEDIATION_20261106:` 區塊；原始欄位未動 |

六項要求查核：

1. 正確指向 Proxy 原始分支與 HEAD：原件已載 `docs/qa-pr93-gateb-proxy-20261103@80f5307`（Handoff yaml:100–101 為完整 HEAD `80f5307…110bf`）；更正版未改動。✓
2. 正確記載公開 manifest 56/56：原件多處載明 Controller 重算 56/56 PASS；更正版未改動。✓
3. 不誤稱原封存 ZIP 和 BRAVO.zip 已重新取得：原件與補登皆明載「仍未取得」；補登稱「封存 ZIP（67 entries）與 BRAVO.zip 二進位缺口維持未關閉」。✓
4. 保留 `ce7ef6c` 舊契約 Gate B FAIL：原件與補登皆保留（`GATE_B_FAIL / BASELINE_BLOCKED_LIVE_QA`）。✓
5. 保留 `88d27a5` 修訂契約 PASS：原件與補登皆保留（`GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE`）。✓
6. 保留 G0 ACCEPTED_CLOSED：原件與補登皆保留（`G0_ACCEPTED_CLOSED`／`G0_ACCEPTED_UNAFFECTED`）。✓

## 7. Finding Closure Matrix

### 修復者 findings（F-01–F-09）

| ID | 分類（更正後） | 處置 | QA 狀態 |
| --- | --- | --- | --- |
| F-01 | `INTERNAL_INFRASTRUCTURE` | 公開副本去敏（6 處） | CLOSED |
| F-02 | `INTERNAL_INFRASTRUCTURE` | 公開副本去敏（1 處） | CLOSED |
| F-03 | `POTENTIALLY_SENSITIVE` | 公開副本去敏（10 處／6 檔）；視同屆期；無輪替 | CLOSED |
| F-04 | `PUBLIC_NONSECRET` | 保留 | CLOSED（數字更正 QA-N2） |
| F-05 | `FALSE_POSITIVE` → **`PUBLIC_NONSECRET`**（QA-N1 更正） | 保留 sessionId UUID，理由見 §2.3；mpaSessionId／svSession 等仍為無值 | **CLOSED WITH CORRECTION（QA-N1）** |
| F-06 | `FALSE_POSITIVE` | 無處置 | CLOSED |
| F-07 | `FALSE_POSITIVE` | 無處置 | CLOSED |
| F-08 | `PUBLIC_NONSECRET` | 保留 | CLOSED |
| F-09 | `PUBLIC_NONSECRET` | 保留 | CLOSED（數字更正 QA-N3） |

### QA 新發現（QA-N1–N5，皆非阻擋）

| ID | 問題 | 嚴重度 | 處置／狀態 |
| --- | --- | --- | --- |
| QA-N1 | F-05「不存在任何 session 值」不成立：兩頁各有 2 處帶引號 `"sessionId":"<UUID>"`（sha12 `a7d1adab33a0`／`dffb3e73c870`）。更正分類為 `PUBLIC_NONSECRET`（匿名逐次載入 telemetry ID），保留理由見 §2.3；不需去敏／輪替／IR | 中（紀錄正確性；安全實質不變） | **CLOSED WITH CORRECTION**：本報告即更正紀錄；發布時須連同本報告／custody 補登載明 |
| QA-N2 | F-04 instanceId distinct 數：修復者稱 21，實測 19（兩種獨立擷取一致） | 低（數字） | OPEN：更正數字後關閉 |
| QA-N3 | F-09 長 hex 數：修復者稱 224，實測 216（兩樹重跑＋交付 JSON 一致） | 低（數字） | OPEN：更正數字後關閉 |
| QA-N4 | 掃描總數未標樹：報告「399 處」為原始樹；交付 JSON（398）為去敏樹；原始樹掃描輸出未附於包內（QA 已重跑：原始 399／去敏 398） | 低（文件） | OPEN：標明兩樹數字並附原始樹輸出後關閉 |
| QA-N5 | HISTORICAL-REVIEW 補登句同值重述（「由 X 更新為 X」）；該文件 status 行原本即非 `security_review_pending` | 低（措辭） | OPEN：修正措辭後關閉 |

### 不適用／未關閉（非本 QA 可關閉）

- 原封存 evidence ZIP（67 entries／836,389 bytes）與 `pkgbuild/BRAVO.zip` 二進位仍未取得、未重驗：維持 open，不屬本 QA 可關閉事項。
- Poster-present 路徑仍 `UNVERIFIED_BRANCH`：維持原狀態。
- `security_review_pending` → 新狀態之正式更新，待 custody 文件提交時生效（本 QA 不代推）。

## 8. 發布就緒決定

**Publication readiness：`READY_WITH_CONDITIONS`（附條件通過）。**

條件：

1. 發布去敏集時須連同本獨立 QA 報告，使 QA-N1 更正分類成為公開紀錄的一部分；不得僅以修復者原版 F-05（「不存在 session 值」）之表述發布。
2. N2–N5 一行文字更正於 custody 文件提交時一併修正（不需重做去敏 bytes、不需重跑掃描）。
3. 僅發布 §0 綁定之去敏集（`PUBLIC-SANITIZED-MANIFEST.sha256` sha `18364466…414fd`）；任何 bytes 變更須重新綁定並重審。
4. 推送至 `security/pr93-lease03-evidence-remediation-20261106` 或任何公開分支，仍須 Controller 另行批准；本 QA 不授權推送、合併或部署。
5. 不啟動秘密輪替、不啟動 Incident Response、不改寫 Git 歷史（Option A）。

## 9. 測試紀錄

獨立測試完整紀錄（含命令、輸出、SHA）見 `QA-TEST-RECORD.md`；QA 腳本與掃描輸出存於本工作區（`qa_*.py`、`qa_sweep_counts.json`、`run/scan/qa-findings-*.json`、Gitleaks 輸出 `/tmp/qa-gitleaks-*.json`）。

## 10. 簽署

- Reviewer：Independent Security Reviewer（與修復者不同之 agent）
- 日期：2026-11-06
- Verdict：`SECURITY_QA_PASS_WITH_NONBLOCKING_FINDINGS`
- 本報告取代修復者 `PR93-LEASE03-SECURITY-QA.md` 中 `PENDING_INDEPENDENT_REVIEW` 之待簽狀態；該文件之修復者自查表仍為自查紀錄，不構成裁決。
