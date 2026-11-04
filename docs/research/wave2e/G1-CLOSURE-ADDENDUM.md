# G1 Closure Addendum — WAVE2E-A-G1-EVIDENCE-CLOSURE-20261104
Workstream: WS-2E-10 / Agent A
Date: 2026-11-04 (Asia/Taipei)
Reference HEAD: 4963523803a728223970c5c401e6cfb3d5635661
Base artifacts: RAW-DOM-VERIFICATION-ADDENDUM.md (16224b4), xpath-evaluation-results.json (4963523), WAVE2E-A-HANDOFF-STATUS.md

## 1. 目的
依 WAVE2E-A-HANDOFF-STATUS.md「What an independent reviewer needs to close G1」逐項對應 Agent A 交付物，完成作者側剩餘 provenance／reproducibility 補件。**独立 QA 的 G1 verdict 不由 Agent A 自證。**

## 2. Reconciliation 項目對應表
| Reconciliation item | Agent A 交付物 | 狀態 | 備註 |
| --- | --- | --- | --- |
| 1. Restricted DOM + privacy-reviewed structural excerpt | `g1-priority-dom-excerpts.json`（234/084/046/00/999999 之 XPath context：節點序列、標籤/class、節點值，無 HTML 原文） | **DELIVERED**（作者側隱私審查完成：僅節點結構與文字值，無 session material） | 原始 rendered HTML 依規範仍留存受限工作區、不上傳 |
| 2. Machine-readable per-page XPath JSON | `xpath-evaluation-results.json`（11 頁，all_checks_pass） | **DELIVERED**（commit 4963523） | 作者產生、非獨立重播 |
| 3. CDP/navigation provenance | 本檔 §3 | **PARTIAL** | 作者工具未記錄 HTTP 狀態碼／redirect chain／network trace；詳 §3 缺口聲明 |
| 4. Independent replay (234/084/046, 00/999999) | 提供比较基準：`g1-priority-dom-excerpts.json` + `xpath-evaluation-results.json` | **OWNER: Independent QA** | Agent A 提供 expected values／結構摘錄，不得自證為 replay |
| 5. Controller policy decisions（soldout image / Tags / Label→Studio / whole-DVD Duration） | — | **OWNER: Controller** | 作者僅報告（4963523 之 meta、policy_defaults_under_controller_review） |
| 6. Reviewer record (identity, source SHA, verdict) | — | **OWNER: Independent QA** | — |

## 3. CDP/navigation provenance（作者工具可及範圍）
- **final URL**：11/11 頁 canonical link 精確等於請求頁面 URL（含 046/084 前導零），詳 `xpath-evaluation-results.json` 之 checks.url_matches_page_url。
- **HTTP status／redirect chain／network result**：**NOT_CAPTURED**——本 session 作者工具無法記錄 status code、redirect hops、partial-page flag。作者分類僅依據 post-render content（`<title>`/og:title="404 | bravo-works"）與結構完整性（22-h2 產品模板）。此為對獨 review 的限制，需由留存受限 DOM 的擷取參數或獨立 QA 補齊。
- **頁面 readiness**：所有 9 個產品頁皆含 22 h2＋品番 label＋canonical＋產品專屬 og:image＋封面 img（alt＝標題行1）——完整水合無疑；2 個 404 頁只剩 2 個導覽 h2＋404 title＋站級 background og:image，无法混入產品。
- **SSR-vs-rendered marker counts**：已存於 `xpath-evaluation-results.json` meta（`ssr_vs_rendered_marker_counts`；SSR 品番 0、封面 img 0）。

## 4. 指定事項確認（二個負面+重點頁）
- **084 Details campt**：`p.font_8` 節點存在但文字内容長度 0（norm 後空字串），`g1-priority-dom-excerpts.json` 之 details.text_len=0；不存在任何相鄰節點可被借用為 Details。
- **084 soldout cover**：唯一 alt 非空 wixstatic img（selector 單一節點，alt=「少年集団強姦」）之 media ID `3b5bfe_8f010d56aefb409a811cd80516dba9b5...` 與 og:image=BR-084soldout.jpg 同 media；該圖為產品專屬 soldout 图示，使用與否待 controller policy。
- **Code leading zero**：046→「046」、084→「084」，原始字串保留。
- **原 source Label／whole-DVD minutes**：已在 `xpath-evaluation-results.json` 以 `Studio_label`／`Duration_min` 保留原始值，未映射。
- **維持基線**：九個產品頁 record＋兩個 404 record 不受新揭開流程影響；不再追加一般網站調查。

## 5. 新設置交付物 SHA-256
- `g1-priority-dom-excerpts.json`：**f8c3da0a2c8c33753d55c4ca80122e567eb5c73eace1214d1f0ee3dba141d8dc**（content SHA-256，已於 2026-11-04 驗證與 committed blob `ab93917c8fe5562f6a614f54df709e9bb54c3158` 一致）。**更正**：原先本檔誤植為 `055aff9236f236694cacb6504380a54376249d81275ff81644df6bd0f6089d59`（為 excerpts 產生後之陳舊 digest，excerpts 曾於 trim 修訂後未同步更新此處陳述）。

## 6. Handoff
```yaml
ASSIGNMENT_ID: WAVE2E-A-G1-EVIDENCE-CLOSURE-20261104
WORKSTREAM_ID: WS-2E-10
AGENT_ROLE: Agent A
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "4bbafca9cf7b5d67117ac41136e74a303c28e4f4"
BRANCH: research/e2e-bravo-dvd-dom
HEAD_SHA: "(本 addendum commit；見 commit 記錄)"
CHANGED_FILES:
  - docs/research/wave2e/G1-CLOSURE-ADDENDUM.md
  - docs/research/wave2e/g1-priority-dom-excerpts.json
DELIVERABLES:
  - "G1-CLOSURE-ADDENDUM.md (reconciliation item mapping + section 2 status claims)"
  - "g1-priority-dom-excerpts.json sha256=f8c3da0a2c8c33753d55c4ca80122e567eb5c73eace1214d1f0ee3dba141d8dc"
EVIDENCE: []
TEST_RESULTS:
  - "excerpt generation + SHA-256 self-check: PASS"
KNOWN_LIMITATIONS:
  - "HTTP status/redirect/network provenance NOT captured by author tooling"
  - "raw restricted DOM remains outside repo (policy); only structural excerpts delivered"
  - "Agent A cannot issue G1 PASS; independent QA holds the verdict"
DEPENDENCIES:
  - "Independent QA: replay items 1-6 and issue G1 verdict"
RISKS_AND_DECISIONS: []
HANDOFF_STATUS: READY
```
