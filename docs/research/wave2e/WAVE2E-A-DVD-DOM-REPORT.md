# WAVE2E-A-DVD-DOM-REPORT.md
Assignment: WAVE2E-A-DVD-DOM-20261102 / WS-2E-10 / Agent A（DVD DOM Research）
Report language: zh-TW
BASE_SHA: 4bbafca9cf7b5d67117ac41136e74a303c28e4f4
Captured/verified: 2026-11-02（Asia/Taipei, 04:14–04:20 session）

---

## 1. Executive Findings

1. **兩個 Primary DVD 頁面均取得可信的 completed 內容擷取。** `/dvds/234`、`/dvds/084`、`/dvds/281`、`/dvds/046` 四頁皆在本次 session 以匿名唯讀方式成功取得完成渲染後的文字內容，無 Cloudflare／驗證頁。`/dvds/084` 進行兩次獨立擷取，結果位元級一致（可重現性證據：`dvd-084-recapture.sanitized.txt` SHA 3e3697d7…）。
2. **Code 是最強欄位。** 四個模板上 `品番` 標籤後第一個元素即為作品編號（234／084／281／046），與 URL 數字、`<title>` 一致；**046 的前導零在來源文字中原樣保留（"046" 而非 "46"）**。
3. **Title 是最弱欄位（AMBIGUOUS_SOURCE）。** 標題 h2 數量跨模板不一致：234 與 281 有 2 個標題 h2（主標＋副標），046 只有 1 個，且 046 在標題前另有 `GO to BRAVO-CLIPS` heading。main 上現行的 `preceding::h2[2]`（宣稱於 dvds/376、347、372 驗證）**在 046 樣式上會誤抓導覽連結**，不得沿用。
4. **084 展現第三種模板變體。** 其標籤／值（品番、収録時間、発売日、定価、レーベル、備考）在擷取層完全沒有 heading 標記，且**沒有描述區塊（Details 為 SOURCE_FIELD_ABSENT）**、含「戻る」與購買按鈕。h2 錨點式 selector 在 084 上未被證明成立。
5. **Image 在 DVD 頁面上沒有任何正面證據。** 歷史 fixture（dvd-281）對產品 comp 的圖片斷言為 expectedCount 0；本次文字擷取亦無任何封面節點可觀察。PR #93 已證明 clips 頁面唯一的 wixstatic 圖片是共享 logo GIF——DVD Image 應 fail-closed。
6. **DVD = 多場景合輯（multi-scene compilation），非單一 Scene。** 234「発情エロ3編」、281「４編収録」、046 為 260 分鐘 2 枚組多 Part 作品。依任務限制，不建議 groupByURL，但必須記錄資料模型限制：以 Stash Scene 承接時，Duration 是**整片總長**，Details 含多段描述。
7. **本次證據為去敏文字層擷取（post-render text extraction），非原始 DOM。** 因此所有 XPath 均為「候選」， XPath 層級 cardinality 未經 live DOM evaluation——Agent F 定稿前必須對原始 rendered DOM 重新驗證（見 §9）。

## 2. Environment / Baseline

| 項目 | 值 | 來源 / 驗證時間 |
| --- | --- | --- |
| main HEAD | `4bbafca9cf7b5d67117ac41136e74a303c28e4f4` | GitHub API，2026-11-02；最後 commit 2026-10-31（merge PR #90） |
| PR #93 | OPEN／DRAFT／**未合併**；head `86e34a2`（fix/e2e-bravo-clips） | GitHub API，2026-11-02；scope 僅 Clips，DVD 保留給 Wave 2E；bravo-fixtures.yml 已還原至 main digest `be1885d2…` |
| PR #98（規劃文件） | OPEN／DRAFT／未合併；head `0c97068`；`docs/61-bravo-dvd-wave-2e.md` 已讀取 | GitHub API，2026-11-02 |
| 歷史 DVD fixtures | dvd-281.html（40ff15e…）、dvd-046.html（8d129e0…）、dvd-173.html（9030729…）、dvd-215.html（73628ce…）；bravo-fixtures.yml（f38a38e…，3 cases：dvd 281／046／Cloudflare） | repo tree @ main，2026-11-02。**歷史 fixture ≠ 當前網站運作證據** |
| BRAVO 網頁渲染模式 | Wix 動態頁；本次 6 次匿名擷取均取得完成渲染內容（無 challenge） | live fetch，2026-11-02 04:14–04:20 +08:00 |
| CDP 需求 | 無法由文字擷取判定；正式 BRAVO.yml 採 `driver.useCDP: true`（Wix warmup-data 水合）。歷史 header 註解指出匿名 fetch 可取得 SSR 內容 | live session + repo BRAVO.yml @ main |
| main BRAVO.yml 現況 | `sceneByURL` 僅匹配 `/clips/`；但 scene scraper 內含標註「2026-10-17 redesign、於 dvds/376、347、372 驗證」的 `品番` 相鄰 h2 selector（Title=`preceding::h2[2]`、Code=`following::h2[1]`、Image=`img[@alt!='' wixstatic]`） | repo @ main。注意：這些宣稱未隨附本次可追溯證據，且 046／084 模板上不成立或未證明 |

## 3. Source Page Classification

| URL | 分類 | 依據 |
| --- | --- | --- |
| /dvds/234 | **COMPLETED**（內容層） | 完整產品資料（標題、品番、片長、發售日、定價、レーベル GAYSIAN、描述）；`<title>`="234" 與 URL 一致 |
| /dvds/084 | **COMPLETED**（內容層）；模板變體 | 完整產品資料（少年集団強姦、品番 084、140min、2012-11-17、Lucifer、備考=廃盤）；**無描述區塊、無 heading 標記**；兩次擷取一致 |
| /dvds/281 | COMPLETED（內容層）；與歷史 fixture 交叉一致 | 內容與 bravo-fixtures.yml 的 dvd-281 案例（h1="281"、canonical）方向一致；品番 281、120min、2020-07-31、ooooPS!! |
| /dvds/046 | COMPLETED（內容層）；含導覽風險 | 品番 046（前導零保留）、260min 2枚組、2010-09-30、ooooPS!!；頁面含 `GO to BRAVO-CLIPS` heading 與レーベル導覽文字 |
| /dvds/999999 | **FETCH_FAILURE / NOT_FOUND_LIKELY** | 擷取失敗；HTTP 狀態不可直接觀察，不得當作 completed DOM |
| /dvds/00 | FETCH_FAILURE / NOT_FOUND_LIKELY | 同上 |
| Challenge／Cloudflare | **NOT_OBSERVED**（本次 session） | 6 次成功擷取皆無 challenge；歷史證據僅 failure-cloudflare.html（154 bytes，歷史） |

## 4. DVD Field Mapping Matrix

「節點」欄為文字層觀察的元素序列（`##` = 擷取層回報的 heading）；XPath 層 cardinality 未驗證。

| 欄位 | 來源節點（文字層） | 234 實際值 | 084 | 281 | 046 | 分類 | 跨模板一致性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Title | `品番` 之前的標題 heading 序列 | 勃起する白き花よ／Mr.Lily 編（2 個） | 少年集団強姦（無 heading） | 熊ケツ4／しゅうた参上！（2 個） | ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!（1 個，前面有 GO to BRAVO-CLIPS heading） | **AMBIGUOUS_SOURCE** | 不一致（1–2 個；084 結構未知） |
| Code | `品番` 後第 1 個元素 | 234 | 084 | 281 | **046（前導零保留）** | **VERIFIED**（文字層；XPath 層 UNVERIFIED） | 一致（4/4） |
| URLs | `<title>`＝URL 數字（4/4）；canonical 屬性 live 未觀察 | — | — | 歷史 fixture VERIFIED（`//link[@rel='canonical']/@href` = /dvds/281） | 歷史 fixture VERIFIED（/dvds/046） | **UNVERIFIED**（live 屬性層）；歷史 fixture 支援 | 一致（間接） |
| Details | `備考` 後的描述區塊 | 有長描述（3 Part） | **無（SOURCE_FIELD_ABSENT）** | 有（4 PART） | 有（多 Part） | 234/281/046 VERIFIED；084 SOURCE_FIELD_ABSENT | 不一致 |
| Image | 無任何可觀察節點 | NOT_OBSERVED | NOT_OBSERVED | 歷史 fixture：產品 comp 圖片 expectedCount **0** | NOT_OBSERVED | **UNVERIFIED**（傾向 SOURCE_FIELD_ABSENT） | 無正面證據 |
| Date | `発売日` 後的元素 | 2018年8月29日 | 2012年11月17日 | 2020年7月31日 | 2010年09月30日 | **VERIFIED**（文字層） | 一致；注意月份格式混用（`8月` vs `09月`，需彈性 parse） |
| Studio | `レーベル` 前第 1 個元素 | GAYSIAN | Lucifer | ooooPS!! | ooooPS!! | **VERIFIED**（文字層；XPath 層 UNVERIFIED） | 一致；046 導覽列亦含「ooooPS!!」文字（誤抓風險） |
| Duration | `収録時間` 後的元素（`min` 為獨立後續元素） | 110 | 140 | 120 | 260 | **VERIFIED**（文字層） | 一致；此為**整片（枚組）總長**，非單一場景長度 |
| Tags | `meta[name=keywords]` | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | **UNVERIFIED**（clips 歷史驗證過，DVD 未驗證） | 未知 |
| Performers | 無結構化欄位（僅存在於描述自由文字：LILY、しゅうた、雄太…） | — | — | — | — | **SOURCE_FIELD_ABSENT** | 一致（4/4 皆無） |

補充觀察：`BR -` 元素在四頁皆出現於 Code 之後、`収録時間` 之前。語意未知（可能是「BR-」品牌前綴的拆分顯示），**不得**作為 Code 或 Title 來源。

## 5. Candidate XPath（候選；均未經 live DOM evaluation）

### 建議候選（待 Agent F 以原始 DOM 驗證）
| 用途 | 候選 XPath | 理由 | 已知失效條件 |
| --- | --- | --- | --- |
| Code | `//h2[contains(.,'品番')]/following::h2[1]` | 四模板文字序列一致；前導零原樣保留；錨點局部化、步距 1 | 084 的 h2 結構未證明；若標籤非 h2 則失效 |
| Duration | `//h2[contains(.,'収録時間')]/following::h2[1]`（取數字 ×60） | 四模板一致；`min` 為獨立元素不會混入 | 同上 |
| Date | `//h2[contains(.,'発売日')]/following::h2[1]` | 四模板一致；需支援 `2010年09月30日` 與 `2018年8月29日` 兩種零填充 | 同上 |
| Studio | `//h2[contains(.,'レーベル')]/preceding::h2[1]` | 值緊鄰 レーベル 標籤之前（四模板一致） | 若 046 導覽的レーベル名亦為 heading 會誤抓；084 未證明 |
| URLs | `//link[@rel='canonical']/@href` | 歷史 fixture 驗證過（281、046）；屬性值非渲染文字 | 需 live 屬性層確認 |
| Image | （無候選——fail-closed） | 無任何產品封面證據；歷史 fixture 期望 0 | — |

### 不建議使用
| XPath | 原因 |
| --- | --- |
| `//h2[contains(.,'品番')]/preceding::h2[2]`（main 現行 Title） | 046 上標題僅 1 個 h2 且前方有 `GO to BRAVO-CLIPS` heading，此 selector 會誤抓導覽連結；只在「恰好 2 個標題 h2」模板（234/281）正確 |
| 任何 `comp-kbf…` Wix component ID 路徑（如 `//div[@id='comp-kbfkf16x']`） | 歷史 fixture 依賴的 comp ID 已因 2026-10-17 redesign 改版；模板綁定脆弱 |
| `//img[@alt!='' and contains(@src,'wixstatic')]/@src`（main 現行 Image） | logo／無關 wixstatic 圖片誤抓風險（PR #93 clips 證據：myfans logo GIF）；DVD 無封面正面證據 |
| 全域 `//h1` | 歷史 fixture 證明 h1.font_0 = DVD 編號（"281"），非標題 |
| 任何由 URL 數字推導 Title/Code | 違反任務禁令；046 前導零會丟失 |

## 6. Cross-page Comparison（模板變異摘要）

| 特徵 | 234 | 084 | 281 | 046 |
| --- | --- | --- | --- | --- |
| 標題 h2 數 | 2 | 未知（無 heading） | 2 | 1（＋1 個導覽 heading） |
| `品番` 值緊鄰 | ✓ | ✓（無 heading） | ✓ | ✓ |
| 描述區塊 | ✓ | ✗ | ✓ | ✓ |
| 導覽文字混入 | 無 | 「戻る」＋購買按鈕 | 無 | レーベル導覽＋GO to BRAVO-CLIPS |
| 枚組 | 1 | 1 | 1 | **2** |
| 月份格式 | 8月 | 11月 | 7月 | **09月（零填充）** |

結論：至少存在 3 種呈現變體（234/281 型、046 型、084 型）。任何 selector 必須以「錨點標籤 + 步距 1」的局部化形式撰寫，並在 046 與 084 上驗證，不得只在 234 型上驗證。

## 7. Negative Cases

1. **缺少可選欄位的有效頁面**：`/dvds/084`——有效產品頁，但無描述區塊（Details SOURCE_FIELD_ABSENT）。擷取器必須容忍缺失而非補值。
2. **不存在的 DVD URL**：`/dvds/999999`、`/dvds/00`——擷取失敗（HTTP 狀態不可觀察）。分類 FETCH_FAILURE／NOT_FOUND_LIKELY，不得視為 completed DOM。
3. **Challenge／存取受阻**：本次 session NOT_OBSERVED（6/6 擷取成功、無 challenge）。歷史證據僅 failure-cloudflare.html（154 bytes）＋bravo-fixtures.yml 的 Cloudflare 案例——**僅為歷史證據**。
4. **誤抓 Logo／其他圖片**：DVD 頁 NOT_OBSERVED（文字擷取無圖片節點）。相鄰證據（PR #93 clips）：唯一驗證過的 wixstatic 圖片為共享 myfans logo GIF。Image 應 fail-closed。

## 8. Known Limitations

- **證據層級為去敏文字擷取，非原始 DOM。** 本 session 工具無法執行 CDP 或取得原始 HTML；無 HTTP 狀態碼、headers、屬性層（canonical、og:、meta keywords）與圖片節點的直接觀察。所有 XPath 為候選，**XPath cardinality 未經 live DOM evaluation**。
- **Title 無法定稿**：跨模板標題節點數不一致（AMBIGUOUS_SOURCE）。需原始 DOM 才能判斷標題是單一多行節點或多個 h2、以及 `GO to BRAVO-CLIPS` 的實際元素層級。
- **084 模板結構未知**：無 heading 標記的觀察可能是模板差異，也可能是擷取層差異；兩次擷取一致但無法排除後者。
- 234/281/046 描述於去敏副本中節錄（欄位值逐字保留；完整原文在受限私有工作區）。
- `BR -` 元素語意未知。
- 未使用 stash-test（未申請 lease；公開唯讀研究獨立進行，符合任務限制）。
- main BRAVO.yml 內「於 dvds/376、347、372 驗證」的宣稱本次無法追溯，不應作為定稿依據。

## 9. Recommendations to Agent F

1. **定稿任何 selector 前，先以 CDP／curl 取得 234、084、046 的原始 rendered DOM**，並將本報告 §5 候選 XPath 對三個模板逐一 evaluate（含 cardinality）。本報告的文字序列證據是結構假說，不是最終 DOM 證明。
2. Code 儙先採 `品番` 錨點 + `following::h2[1]`；必須在 046 上斷言字串 `"046"`（前導零）。
3. Title：不得沿用 `preceding::h2[2]`。需先判斷標題節點真實結構；若為多個 h2，考慮取 `品番` 前所有 heading 中排除導覽（GO to BRAVO-CLIPS、レーベル導覽）後的第一個，並以負面測試固定。Title 未定稿前，寧可空值也不要猜。
4. Image：fail-closed（無 img fallback），除非在原始 DOM 上驗證出產品專屬封面。歷史 fixture 對 281 的產品圖期望為 0。
5. Details：084 無描述——missing field 必須優雅缺席，不得回補（如把「廃盤」當描述）。
6. Duration：明確記錄其為整片總長（枚組）；046 為 2 枚組 260 分鐘。
7. Tags：先驗證 DVD 頁是否存在 meta keywords，再決定是否納入；不得沿用 clips 假設。
8. Performers：維持 SOURCE_FIELD_ABSENT，描述文字中的人名不得轉為結構化 performer。
9. 資料模型：DVD 頁為多場景合輯。依任務指示不加入 groupByURL／Group scraping，但請在 YAML 註解與文件記錄「Scene 承接 = 整片」的語意限制。
10. 路由：`/dvds/` 必須路由至 dvdSceneScraper（Stash `strings.Contains` 匹配風險由 Agent B/F 測試），QueryFragment 對 DVD 輸入不得落到 clipSceneScraper。

## 10. Mandatory Handoff

```yaml
ASSIGNMENT_ID: WAVE2E-A-DVD-DOM-20261102
WORKSTREAM_ID: WS-2E-10
AGENT_ROLE: Agent A
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "4bbafca9cf7b5d67117ac41136e74a303c28e4f4"
BRANCH: research/e2e-bravo-dvd-dom
HEAD_SHA: "NOT_COMMITTED"
CHANGED_FILES: []
DELIVERABLES:
  - "WAVE2E-A-DVD-DOM-REPORT.md (this report)"
  - "evidence/dvd-234.sanitized.txt"
  - "evidence/dvd-084.sanitized.txt"
  - "evidence/dvd-084-recapture.sanitized.txt"
  - "evidence/dvd-281.sanitized.txt"
  - "evidence/dvd-046.sanitized.txt"
  - "evidence/negative-cases.sanitized.txt"
  - "evidence/manifest.json"
  - "evidence/SHA256SUMS.txt"
EVIDENCE:
  - "dvd-234.sanitized.txt sha256=de5677bbe64deff727bec013783e0f7dbbcc1e7f362536cf4c09d98986178408 captured_at=2026-11-02T04:14-04:20+08:00 provenance=anonymous read-only fetch, post-render text extraction privacy=sanitized-no-session-material"
  - "dvd-084.sanitized.txt sha256=2c3929fd84640bf7e64c6ef722f95a26903d095a42f23ae4625d70d20758872c captured_at=2026-11-02T04:14-04:20+08:00 provenance=same privacy=sanitized"
  - "dvd-084-recapture.sanitized.txt sha256=3e3697d7f34bcf63153a9628a0441ecf152c4698203ffe7f20fa38bfdcab28ea (independent recapture, byte-identical content) provenance=same privacy=sanitized"
  - "dvd-281.sanitized.txt sha256=bf6eb0c8bfebf0cf7d8681a3e8b7f467b9851ac78f202161d5b410d2133f89f6 provenance=same privacy=sanitized (description excerpted; field values verbatim)"
  - "dvd-046.sanitized.txt sha256=7b25621aa3e8aeda56b40f5bf8699daff517a1c0eb1624ebf6149f72a10b7b4f provenance=same privacy=sanitized (description excerpted; field values verbatim)"
  - "negative-cases.sanitized.txt sha256=7366f9f69180f1e98a244f818f1ecfc9b1fb375fb66195afda00d959931f64e5"
  - "baseline: main HEAD / PR #93 / PR #98 verified via GitHub API 2026-11-02"
TEST_RESULTS:
  - "live URL capture (4 DVD pages + 2 negative URLs + 084 recapture): COMPLETED 2026-11-02 session, no challenge"
  - "XPath evaluation against live rendered DOM: NOT_RUN (tooling cannot access raw DOM; candidates only)"
KNOWN_LIMITATIONS:
  - "evidence is sanitized text extraction, NOT raw DOM; no HTTP status/headers/attributes observed"
  - "Title = AMBIGUOUS_SOURCE (heading count varies across templates; nav heading interference on 046)"
  - "084 template structure unverified at DOM level (no heading markers in extraction; no Details block)"
  - "Image/Tags/URLs attribute-level live verification NOT_RUN"
DEPENDENCIES:
  - "Agent F: DVD implementation and integration (must capture raw DOM before finalizing any XPath, especially Title)"
RISKS_AND_DECISIONS:
  - "FACT: both primary DVDs returned completed content; Code values (234/084/281/046) match URL and preserve leading zero on 046"
  - "FACT: main BRAVO.yml current Title selector (preceding::h2[2]) conflicts with the 046 template shape observed live"
  - "INFERENCE: at least 3 presentation variants exist (234/281-type, 046-type, 084-type)"
  - "DECISION: Image fail-closed; no img fallback; no URL-derived Title/Code; no groupByURL"
HANDOFF_STATUS: READY
```
