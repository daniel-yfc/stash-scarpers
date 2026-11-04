---
doc_id: QA-G1-DVD-DOM-REPLAY-20261104
title: G1 Independent DOM Replay — BRAVO DVD 234/084/046/00/999999
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

# G1 獨立 DOM 重播簽核 — Agent D

**Assignment ID:** `WAVE2E-D-G1-DVD-DOM-INDEPENDENT-REPLAY-20261104`
**被審對象:** Agent A 交付（branch `research/e2e-bravo-dvd-dom` @ `9b4ab10`；基準 `xpath-evaluation-results.json` @ `4963523`、`G1-CLOSURE-ADDENDUM.md` @ `9b4ab10`）
**範圍:** 僅 DVD 234、084、046、00、999999 五頁之來源可信度 + XPath 重播 + 簽核。未重做 Agent C 的 Duration/Studio 政策，未重測已合併的 Clips G0，未評及其餘 6 個產品頁。

---

## 1. 簽核裁決

| 項目 | 裁決 |
|---|---|
| **G1_VERDICT（本五頁範圍）** | **`G1_PASS`** |
| 附帶 minor finding | 1 項（文件 digest 陳述錯誤，見 §5；不阻擋本裁決，建議 A 更正） |

A 的五頁證據（selector 集 + 逐欄 expected 值 + 節點數）經獨立重新擷取後**全數重現**；A 自承缺失的 HTTP/redirect provenance 由本輪補齊，且與其內容分類一致（產品頁 200、負例頁真 404）。

## 2. 來源可信度（獨立重新擷取，證據 capture-provenance.json）

方法：隔離環境（本機 VM）以 CDP 操作環境指定之 headless Chrome（stash-test 瀏覽器），匿名唯讀瀏覽公開頁面；未登入、未經 Stash 擷取、未修改任何 Stash 狀態。每頁全新 target；完成條件明示（產品頁＝品番 h2 出現；負例＝page title 含 404；上限 40s 後再 settle 3s）。

| 頁面 | HTTP 狀態 | Redirect | 完成條件 | DOM bytes | DOM SHA-256（前 16） |
|---|---|---|---|---|---|
| 234 | **200** | 無（chain=1） | hinban_h2_present | 1,074,165 | `16c327c5c52b3655` |
| 084 | **200** | 無 | hinban_h2_present | 1,064,608 | `4c9c02f0209bedc1` |
| 046 | **200** | 無 | hinban_h2_present | 1,072,083 | `ef360e9a9ae5fa44` |
| 00 | **404** | 無 | page_title_404 | 763,374 | `73696b5d80600a1d` |
| 999999 | **404** | 無 | page_title_404 | 763,387 | `5fd72ed7698653c2` |

註：DOM SHA 與 A 的 input SHA 不同屬預期（不同日期/工作階段擷取，Wix DOM 含動態內容）；重播比對的是 selector 求值結果，不是 DOM 位元組。原始 DOM 依 A 既定規範留存受限本地（`raw/`），不上傳；完整 SHA-256 見 manifest。

## 3. XPath 獨立重播（lxml，A 的原始 selector 逐字取自其 evaluation JSON）

對五頁 × 全部 17 欄位逐項比對 node_count 與 values（證據 replay-results.json）：

| 頁面 | 結果 | 重點 |
|---|---|---|
| 234 | ✅ 全欄相符 | Title「勃起する白き花よ」、Code「234」、副標「Mr.Lily 編」；h2 總數 22 |
| 084 | ✅ 全欄相符 | Title「少年集団強姦」、Code「084」前導零保留；**Details 節點存在（count=1）但正規化文字長度 0** — 與 A 主張（空白 Details、無相鄰節點可借用）一致；soldout 圖 URL 與 A 記錄一致（採用與否屬 Controller 政策，不在本輪範圍） |
| 046 | ✅ 全欄相符 | Title「ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!」、Code「046」前導零保留 |
| 00 | ✅ 全欄相符 | 品番 gate 節點數 0；Title/Code/Details/Image/Date 全空；og:title 與 page title 皆「404 \| bravo-works」；h2 僅 2（導覽） |
| 999999 | ✅ 全欄相符 | 同 00 |

比對語義註記（兩處皆為正規化假象，非內容差異，已於 replay-results.json 逐欄標示 match_mode）：
- **Details（234/046）**：與 A 值僅在 inline 元素邊界的空白有別（★、Part.01 處）；去除全部空白後字串**完全相同**。
- **h2_total**：A 的 values 只存前 3 個 h2（其格式截斷），node_count=22 才是總數；本輪 count 與前 3 值皆相符。

## 4. 與 A 交付的交叉一致性

- A 的 `g1-priority-dom-excerpts.json` 內容與其 evaluation JSON 一致（084 details text_len=0、046=482、234=367，與 evaluation 的正規化字元數吻合）。
- A 的 addendum §3 自承 HTTP status/redirect NOT_CAPTURED — 本輪 §2 已補齊，且實測（404 真狀態碼）支持其以內容分類 404 的判斷。
- A 的歷史主張「CDP 必要性」（SSR 無品番/封面）未在本輪重測範圍（本輪只驗 rendered DOM 重播），不予置評。

## 5. Minor finding（不阻擋）

**F-G1-01（文件完整性，minor）：** A 的 `G1-CLOSURE-ADDENDUM.md` §5 陳述 `g1-priority-dom-excerpts.json` 的 SHA-256 為 `055aff9236f2…9d59`，但該檔於 branch `9b4ab10` 的實際 blob SHA-256 為 **`f8c3da0a2c8c33753d55c4ca80122e567eb5c73eace1214d1f0ee3dba141d8dc`**，兩者不符。檔案內容本身與 evaluation JSON 交叉一致（§4），故研判為陳舊/誤植的 digest 陳述，而非內容造假；建議 A 以新 commit 更正該行，避免後續驗證者誤判。**本裁決不依賴該 digest**（重播基準是 evaluation JSON 的 selector 與值，且已由獨立擷取重現）。

## 6. 範圍與限制

- 本 PASS 僅涵蓋五頁的「來源可信度 + XPath 重播」；A 其餘 6 頁（281/173/215/304/315/377/383/384 中未列名者）不在本輪，G1 若需全頁覆蓋應另行指派。
- 政策項（084 soldout 圖採用、Tags 省略、Label→Studio、whole-DVD Duration）屬 Controller，本輪未重做、未表態。
- 本裁決不授權 Agent F 整合或任何合併；後續依 Controller 流程。

## 7. 證據索引

`~/workspace/g1-dvd-replay/`：`capture-provenance.json`（五頁擷取 provenance 全文）、`replay-results.json`（逐欄 expected/actual，machine-readable）、`capture_cdp.py` + `replay.py`（可重現腳本）、`MANIFEST.sha256`。原始 DOM（raw/）依規範不上傳 repo，其 SHA-256 已記錄於 capture-provenance.json 與 manifest；repo 上架待 owner 指示（形狀同 Gate B：QA 分支 + 公開裁決紀錄）。
