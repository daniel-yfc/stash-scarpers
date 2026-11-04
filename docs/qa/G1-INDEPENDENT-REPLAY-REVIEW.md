# G1 Independent Replay Review — WAVE2E-D-G1-DVD-DOM-INDEPENDENT-REPLAY-20261104
Reviewer: Agent D（independent DOM replay）
Reviewer platform: Perplexity（Perplexity AI assistant）
LLM model: not exposed to agent（no model identifier provided by platform; recorded for audit honesty）
Environment: agent connector runtime with attached CDP capture files（read-only）；no local CDP/browser process
Reviewed at: 2026-11-04T14:13:00+08:00（Asia/Taipei, post-render session）
Base artifacts: G1-CLOSURE-ADDENDUM.md @ b2f41e1（含 excerpts SHA-256 更正 f8c3da0a…）、xpath-evaluation-results.json @ 4963523、g1-priority-dom-excerpts.json（blob ab93917c…）
Tooling: Python + lxml XPath 1.0 (lxml 5.4.0.0), direct read of the five priority CDP rendered captures; live fetch for freshness check.

## 1. Verdict

**G1_PASS**（XPath reproducibility + content-layer source credibility, 5/5 pages PASS；HTTP/network provenance 依 §3 標記為 NOT_CAPTURED，不影響本 verdict）

## 2. 驗證範圍與方法（非重複作者流程）

1. **來源可信度**：直接讀取 5 個 CDP rendered capture 並獨立重算 SHA-256，與 author 公佈值逐一比對；另以獨立工具即時重擷取 5 個 URL，驗證線上內容一致與兩個 404 頁仍可重現。
2. **XPath 獨立重播**：不沿用 author 之結果檔，直接執行全部 17 個 XPath（Title、Code、URLs、Details、Image、Date、Studio_label、Duration、Price、Discs、Tags、og:title、og:image、page_title、validity_gate、h2_total）於原始 DOM 上，逐一有對照。
3. **獨立簽核**：本檔為最終裁決，含 reviewer identity＋platform＋model、reviewed timestamp、輸入／輸出 SHA、機器可讀結果檔。

## 3. 來源可信度結果

| 頁面 | Author SHA-256 vs 獨立重算 | Live re-capture (fetch_url, 2026-11-04) | HTTP status (本審查) |
| --- | --- | --- | --- |
| /dvds/234 | MATCH | 即時內容一致（Title／Code=234／2018年8月29日／GAYSIAN） | NOT_CAPTURED |
| /dvds/084 | MATCH | 即時內容一致（Title／Code=084／140min／2012年11月17日／Lucifer／廃盤；備考後無描述） | NOT_CAPTURED |
| /dvds/046 | MATCH | 即時內容一致（Title／Code=046 前導零／260min／10,500／2010-09-30；含 GO to BRAVO-CLIPS heading） | NOT_CAPTURED |
| /dvds/999999 | MATCH | fetch 失敗（與 CDP capture 之「404 | bravo-works」一致） | NOT_CAPTURED |
| /dvds/00 | MATCH | fetch 失敗（同上） | NOT_CAPTURED |

- **Author SHA-256 驗證**：5/5 MATCH —— 擷取檔未被竄改，reviewer 與 author 讀取的是同一批 bytes。
- **Live freshness**：3 個產品頁今日線上內容與 CDP capture 一致（Title／Code／Date／Label／Duration，headers 內容不依賴模板變化即重現）；2 個 404 頁今日仍無法擷取，與 capture 日期判定一致。
- **HTTP status／redirect／network layer**：本審查沿用 author 的 **NOT_CAPTURED** 標記——雙方工具皆無法記錄 raw HTTP status code、redirect chain 或 network trace。建議：若 G1 採內容層證據即可（22-h2 產品模板完整水合＋404 頁 title 明示），本項可不予阻擋；如需 raw HTTP 證據則應由具備 network trace 能力之工具補齊後重審。
- **基準修訂**：本審查以 `b2f41e1`（G1-CLOSURE-ADDENDUM.md 之 excerpts SHA-256 更正 055aff92→f8c3da0a）為基準；該更正僅涉及 addendum 對 excerpts 檔之 digest 陳述，不影響 excerpts 內容本身（已驗證與 committed blob `ab93917c…` 一致）。

## 4. 獨立 XPath 重播結果（自 run，非參考 author 之値）

全部 5 頁、17 個 XPath、9 項檢查（title_match／code_match／url_match／image_match／og_title_match／page_title_match／gate_count／h2_total／details_len_match）皆為 **PASS**。

| 頁面 | Title | Code | Details | Image（產品專屬 media ID） | gate h2 | h2 總數 |
| --- | --- | --- | --- | --- | --- | --- |
| 234 | 勃起する白き花よ | 234 | len=367 | 3b5bfe_bfaae957… matches og:image BR234.jpg | 1 | 22 |
| 084 | 少年集団強姦 | 084 | **len=0（欄位缺席，無借用）** | 3b5bfe_8f010d56… matches og:image BR-084soldout.jpg | 1 | 22 |
| 046 | ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題! | **046（前導零保留）** | len=482 | 3b5bfe_eeaa516f… matches og:image BR046-1.jpg | 1 | 22 |
| 999999 | （無） | （無） | （無） | **0（天然 fail-closed）** | **0** | **2（導覽）** |
| 00 | （無） | （無） | （無） | 0 | 0 | **2（導覽）** |

## 5. 結論與 handoff

1. **Author RAW-DOM addendum 之報告值獲獨立重播確認**：五頁 Title／Code／URL／Image／Details（含 084 len=0）/品番 gate/h2 總數與 author 自報一致；無發現任何高估或低估。
2. **兩個負例重播確認**：999999／00 實際 DOM 只有 2 個導覽 h2 且 `<title>`／`og:title` 為「404 | bravo-works」，Img selector n=0 —— 負例判定層級正確，不致混入產品。
3. **084 Details campt**：p.font_8 單一節點、文字長度 0；不存在任何相鄰節點可借用為 Details，符合「缺席維持缺席」。
4. **084 soldout cover**：實際產品 image 之 media ID（`3b5bfe_8f010d56aefb409a811cd80516dba9b5...`）與 og:image=BR-084soldout.jpg 一致；是否採用於走獨立 controller policy，此審查不表意見。
5. **CDP completion 判定**：5/5 頁皆水合至 22 h2＋品番＋產品 og:image，視為完整水合條件已滿足；404 頁只有 2 h2＋404 title，同屬判定充足之負面 criteria。
6. **剩餘唯一留白**：HTTP status／redirect／network trace NOT_CAPTURED by both author and reviewer —— 依內容層證據裁決 G1_PASS，並交由 Controller 決定是否接受此層級或由具 network trace 能力之工具補強後重審。
7. **基準修訂確認**：`b2f41e1` 之 SHA-256 更正（055aff92→f8c3da0a）已納入本審查基準；excerpts 內容本身未變，重播結果不受影響。

```yaml
ASSIGNMENT_ID: WAVE2E-D-G1-DVD-DOM-INDEPENDENT-REPLAY-20261104
WORKSTREAM_ID: WS-2E-10
REVIEWER: Agent D（independent replay）
REVIEWER_PLATFORM: "Perplexity (Perplexity AI assistant)"
LLM_MODEL: "not exposed to agent (no model identifier provided by platform)"
REVIEW_ENVIRONMENT: "agent connector runtime with attached CDP capture files (read-only)"
REVIEWED_AT: "2026-11-04T14:13:00+08:00"
AUTHOR_REFERENCE_COMMIT: "b2f41e179984049940a1e3b1d0754d8c25b0b0da"
REPLAY_RESULTS_FILE_SHA256: "7f78e7f2e4e94f569969ca3afaa076ddc245adb66dc889a2c3e4c258436f000c"
VERDICT: G1_PASS
REMAINING_GAP: "HTTP status / redirect / network provenance NOT captured (content-layer evidence used for verdict)"
STATUS: COMPLETE
```
