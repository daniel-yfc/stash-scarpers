# RAW-DOM Verification Addendum (v2 — COMPLETED) — WAVE2E-A-DVD-DOM-20261102
Workstream: WS-2E-10 / Agent A
Date: 2026-11-02（Asia/Taipei）；CDP captures 2026-11-02T09:57:46–10:03:07Z
Base report: WAVE2E-A-DVD-DOM-REPORT.md（commit 075006e）
本版取代先前未提交的 BLOCKED_TOOLING 草稿：控制器已提供 CDP rendered DOM，屬性層與 XPath 驗證已完成。

## 1. 證據（CDP rendered DOM；原始檔留存於受限工作區，僅提交去敏結果）

| 頁面 | 擷取時間（Z） | SHA-256 |
| --- | --- | --- |
| /dvds/046 | 09:57:46 | 4b020e0b1f0c60633db7985b5edf5a8852d2f39284a866057b3c92dca5a8d43f |
| /dvds/281 | 09:58:13 | 5df5f18d595e05cae450440fc7b3e41a8c209d35fe6d96d32e8627163cc71d30 |
| /dvds/234 | 09:58:48 | 7bafdda8fd1d587b83e9ab28fcb95c9171cb473517afc2f6b4bda9985ed75918 |
| /dvds/084 | 09:58:54 | ade2a7f7a4b5892463790986928524a660d932fb8f58bbb2ebefe45db6e98415 |
| /dvds/999999（404） | 09:59:09 | 82bf6fd4aadd94c210bad15c9dd80e8a7650ab56ddaa76535ed2044a021311bb |
| /dvds/00（404） | 09:59:25 | b3c6ff89f016e36b0d1d298a3d1718a8d4d41561ac10538649c06b6ec9fd2107 |
| /dvds/384 | 10:02:11 | f08cc6966c4b9fb07e4a1cb3b9925e930d2ed0be13b5b5c37eb68f4162f21ce0 |
| /dvds/377 | 10:02:25 | 12739aa5987e9fdd51ff42f34d2b2f7b7d7c25156b12327c9d502ea2f0c4a449 |
| /dvds/383 | 10:02:39 | 7e569cb6a1dd8ae575c7389baa11272a37702c7320d767e649389b79b19448c6 |
| /dvds/304 | 10:02:58 | cf0f10ca13ac5c64aa1c1b14ed13a9d6e4690e9d48b82da5f7bf94bca6374c4f |
| /dvds/315 | 10:03:07 | 66c38b6da75b47b647e5074a25cb5728a4c0bcb65a064aa63afada3d8e5b6e31 |

樣本：9 個有效產品頁（發售年 2010–2026）＋2 個 404 頁。解析環境：Python + lxml（XPath 1.0，與 Stash scrapeXPath 相容）。原始 rendered HTML 含 session material，依任務規範不得提交 GitHub。

**CDP 必要性證據**：同批提供之未渲染 .html 版本（377/383/384/304/315）中 `//h2[contains(.,'品番')]` 與封面 img 均為 **0** —— 產品資料由前端渲染產生，SSR 原始回應不含產品欄位。`driver.useCDP: true` 為必要條件（非可選優化）。

## 2. 已驗證 XPath 矩陣（9 個產品頁 cardinality 均 = 1；下表列代表性值）

| 欄位 | XPath | 234 | 084 | 281 | 046 | 377 | 384 | 結論 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Title | `//h2[contains(.,'品番')]/preceding::h2[2]` | 勃起する白き花よ | 少年集団強姦 | 熊ケツ4 | ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題! | 騒乱みだれ穴５ | ナマ狂い種壺待機５ | **VERIFIED**（main 現行 selector 正確） |
| 副標（選用） | `//h2[contains(.,'品番')]/preceding::h2[1]` | Mr.Lily 編 | （空） | しゅうた参上！ | （空） | （各頁副標或空） | （同） | VERIFIED；雙標題槽固定，第二槽可為空 |
| Code | `//h2[contains(.,'品番')]/following::h2[1]` | 234 | 084 | 281 | **046** | 377 | 384 | **VERIFIED**；046 前導零保留 |
| URLs | `//link[@rel='canonical']/@href` | …/234 | …/084 | …/281 | …/046 | …/377 | …/384 | **VERIFIED**；9/9 與頁面 URL 完全一致 |
| Details | `//p[contains(@class,'font_8')]` | 367 字 | （空） | 370 字 | 482 字 | 有 | 有 | **VERIFIED**；每頁僅 1 個 p.font_8，084 為空（SOURCE_FIELD_ABSENT 自然成立） |
| Image | `//img[@alt!='' and contains(@src,'wixstatic')]/@src` | BR234 | BR-084soldout | br281jk | BR046-1 | br377jk | br384jk | **VERIFIED**（n=1；alt＝標題行1）；404 頁 n=0 |
| Date | `//h2[contains(.,'発売日')]/following::h2[1]` | 2018年8月29日 | 2012年11月17日 | 2020年7月31日 | 2010年09月30日 | 2026年5月31日 | 2026年10月22日 | **VERIFIED**；月份零填充與否混用，parse 需彈性 |
| Studio | `//h2[contains(.,'レーベル')]/preceding::h2[1]` | GAYSIAN | Lucifer | ooooPS!! | ooooPS!! | BRAVO! | BRAVO-RAW | **VERIFIED**（另含 AJITO&BRAVO! 等值） |
| Duration | `//h2[contains(.,'収録時間')]/following::h2[1]` ×60 | 110 | 140 | 120 | 260 | 110 | 100 | **VERIFIED**；整片總長（304 為 480 分 4 枚組） |
| Tags | `//meta[@name='keywords']/@content` | 與其他頁完全相同的 9 個站級標籤 | 同 | 同 | 同 | 同 | 同 | **SITE_GENERIC**：非作品專屬，不建議作為 Tags |

（383/304/315 同樣全部 cardinality=1：生熊悶、MACHO BOX 2、魔法の国のエレクチオン４；Date 2026年9月21日／2021年10月15日／2022年6月26日。）

注意：部分標籤 h2 文字含零寬空白（U+200B，如 `\u200b品番`）；`contains(.,'品番')` 仍可匹配，但取值後 postProcess 應去除 U+200B 與空白。

## 3. 負面頁面驗證（404）

`/dvds/00`、`/dvds/999999`（CDP 擷取）：
- `<title>` 與 og:title 均為 **「404 | bravo-works」** → 明確 404 分類（先前 FETCH_FAILURE 推論獲證實）。
- h2 總數 2（無 `品番`／`収録時間`／`発売日`／`レーベル`）。
- canonical 屬性存在且指向該 404 URL → **canonical 單獨不能證明有效產品頁**；有效性判斷應以 `品番` h2 存在為準。
- `//img[@alt!='' and contains(@src,'wixstatic')]` 於 404 回傳 **0** → Image selector 天然 fail-closed。
- 404 頁亦帶同一組 meta keywords → 再度佐證 site-generic。

## 4. 對原報告的更正（以 raw DOM 為準）

1. **084「無 heading」是擷取層假象**：084 與其他頁共用完全相同的 22-h2 模板（9 個產品頁 h2 總數均為 22）。原報告「三種模板變體」與「084 h2 結構未證明」降級為不成立；跨模板一致性高（2010–2026 發售年份皆一致）。
2. **Title `preceding::h2[2]` 撤回「不建議」判定**：模板在 `品番` 前固定有 4 個 h2（BRAVO-JAPAN、GO to BRAVO-CLIPS、標題行1、標題行2），`preceding::h2[2]` 恰為標題行1，9 頁皆正確。**main 現行 Title/Code selector 即為正確 selector。**
3. **Image 撤回 fail-closed 建議**：產品封面存在（唯一 alt 非空之 wixstatic img，alt＝標題行1），main 現行 Image selector 於 9 個產品頁 cardinality=1、於 404 頁=0。歷史 fixture「expectedCount 0」對應的是已不存在的舊 comp ID。**注意**：084 的封面為 `BR-084soldout.jpg`（售罄示意圖），是否採用由 Agent F/控制者決策。
4. **canonical 屬性 VERIFIED**（9/9 精確匹配，含 046 前導零）。
5. **當前 DOM 無 h1**（9 頁 h1=0）；歷史 fixture 的 h1.font_0 期望已過時。
6. **歷史 comp ID 全部消失**（comp-kbfkf16x／17h／kbflq5xd／kbfmf948 均為 0 命中）；§5 selector 均為 comp-ID-free。
7. **CDP 為必要條件**：未渲染 SSR HTML 不含任何產品欄位（見 §1）。
8. Tags：meta keywords 為站級通用標籤（9 產品頁＋404 頁完全相同），非作品專屬。

## 5. Agent F 定稿規格（最終）

- Title：`//h2[contains(.,'品番')]/preceding::h2[2]`（postProcess 去 U+200B／空白）。
- Code：`//h2[contains(.,'品番')]/following::h2[1]`（保留前導零；不得由 URL 推導）。
- URLs：`//link[@rel='canonical']/@href`。
- Details：`//p[contains(@class,'font_8')]`（084 為空字串→維持缺席，不得回補）。
- Image：`//img[@alt!='' and contains(@src,'wixstatic')]/@src`（404 天然 fail-closed；084 為 soldout 圖，是否採用請決策）。
- Date：`//h2[contains(.,'発売日')]/following::h2[1]`（parse 需同時支援 `2010年09月30日` 與 `2018年8月29日`）。
- Studio：`//h2[contains(.,'レーベル')]/preceding::h2[1]`。
- Duration：`//h2[contains(.,'収録時間')]/following::h2[1]` ×60（整片總長；多枚組亦為總長）。
- Tags：**不建議**使用 meta keywords（站級通用）；若採用需明確記錄決策。
- Performers：SOURCE_FIELD_ABSENT（描述文字人名不得結構化）。
- 有效性 gate：以 `//h2[contains(.,'品番')]` 存在作為有效產品頁判斷；404 頁 canonical 存在但無品番。
- 驅動：`driver.useCDP: true` 為必要（SSR 不含產品資料，見 §1）。
- 資料模型：DVD＝多場景合輯；Scene 承接＝整片（Duration 為總長）；不加 groupByURL。

## 6. Mandatory Handoff（更新）

```yaml
ASSIGNMENT_ID: WAVE2E-A-DVD-DOM-20261102
WORKSTREAM_ID: WS-2E-10
AGENT_ROLE: Agent A
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "4bbafca9cf7b5d67117ac41136e74a303c28e4f4"
BRANCH: research/e2e-bravo-dvd-dom
HEAD_SHA: "(本 addendum commit；見 commit 記錄)"
DELIVERABLES:
  - "WAVE2E-A-DVD-DOM-REPORT.md (commit 075006e)"
  - "RAW-DOM-VERIFICATION-ADDENDUM.md (this file)"
  - "evidence/* (commit 075006e)"
EVIDENCE:
  - "11 CDP rendered DOM captures (046/234/084/281/377/383/384/304/315 + 00/999999 404), SHA-256 in §1; raw files with session material remain in restricted workspace"
  - "5 pre-render SSR .html captures (no product data — proves CDP requirement)"
  - "XPath evaluation via lxml XPath 1.0 against all captures, 2026-11-02"
TEST_RESULTS:
  - "Title/Code/URLs/Details/Image/Date/Studio/Duration XPath: VERIFIED, cardinality=1 on all 9 product pages (2010-2026 releases)"
  - "Negative pages 00/999999: confirmed 404 (title '404 | bravo-works'), no 品番, Image selector n=0"
KNOWN_LIMITATIONS:
  - "084 cover is 'BR-084soldout.jpg' (sold-out artwork) — adoption decision for Agent F/controller"
  - "meta keywords are site-generic (identical on all pages incl. 404) — not product Tags"
  - "Wix comp IDs remain redesign-fragile; selectors in §5 are comp-ID-free"
DEPENDENCIES:
  - "Agent F: DVD implementation and integration (selector spec final; no remaining raw-DOM gaps)"
RISKS_AND_DECISIONS:
  - "CORRECTION: original report §5 'not recommended' for preceding::h2[2] retracted — verified correct on all 9 product pages"
  - "CORRECTION: 084 heading-absence was an extraction-layer artifact; template uniformity confirmed (22 h2s on every page)"
  - "FACT: CDP required — pre-render SSR HTML contains no product fields"
  - "DECISION suggestions: validity gate on 品番 presence; Tags omitted; Performers absent"
HANDOFF_STATUS: READY
```
