# PR #103 獨立 Cross-QA 報告（WAVE2E-CROSSQA-PR103-20261104）

**審查者：** Muse Account ②（PR #104 作者，以獨立審查者身分執行）
**目標：** PR #103（Muse Account ①）— `feat/e2e-bravo-dvds` → main
**目標 HEAD：** `afe861ff2a1406139f3a67953528b8665d0dcbcb`（查核時仍為最新 HEAD，未變動）
**基線：** `main@ff236c9e91e27321e93f59d2bf12488db714dfc7`
**審查方式：** 離線唯讀。隔離檢出（detached HEAD，已驗證 SHA），未修改目標分支、
未修改 PR #104，未執行 Stash live testing、merge 或 production deployment。
**結論：** `CROSS_QA_BLOCKED` — 本候選版不得直接發布；P0 發現有明確的窄幅修復規格，
修復並重驗後可再審。

## 1. 判定表（§9）

| 準則 | 結論 |
|---|---|
| Core DVD mapping | PASS |
| G0 Clips regression | PASS |
| 404 product validity | FAIL |
| Partial metadata exposure | BLOCKING |
| QueryFragment removal | OFFLINE PASS |
| Date and Image | NOT_RUNTIME_VERIFIED |
| Agent B/C test integrity | PASS |
| Exact-head CI | PASS（11 項：10 通過、1 略過、0 失敗） |
| Independent Gate B | NOT_RUN |

建議處置：**拒絕現候選版 as-is，並套用 §6 的窄幅修正**（而非另建 consuming-layer
gate——repo 內今日不存在此類 gate，無法作為本候選版的補救）。

## 2. 獨立性與方法

- 本報告所有數據皆於 #103 隔離檢出上重跑取得，未複製 PR #104 的測試結果。
  唯一例外是方法學上的重用（jsdom 評估、edge 矩陣設計），輸入皆為 #103 的
  production YAML 與 fixture。
- 審查順序：先獨立審 #103，再與 #104 比較。#104 僅在 §6 補救規格中被提及
  （因其 selector 形式恰為一種可行修法），不作為 #103 錯誤的預設立場。
- #103 頁首已誠實揭露部分 metadata 風險並自評
  `BLOCKED_UNSAFE_PARTIAL_METADATA`；本審查驗證該揭露屬實，而非推翻它。
- 未驗證事項一律標 NOT_RUN／NOT_VERIFIED，不以離線證據冒充 runtime 證據。

## 3. P0 發現

### P0-01 — DVD 404 頁產出 URLs-only 部分結果，YAML 層無 guard（BLOCKING）

- **Severity：** P0 / release-blocking。
- **Actual behavior：** production `dvdSceneScraper.URLs` selector
  `//link[@rel='canonical']/@href`（`scrapers/BRAVO.yml:265`）無產品 marker 條件。
  對無 品番 marker 的無效頁，Title／Code／Details／Date／Image 全空，
  但 URLs 照樣輸出 canonical。Stash 依欄位獨立填值，部署物本身即產出部分結果。
- **Expected behavior：** 無效產品頁產出零欄位（fail-closed），或至少 URLs
  須與 Title＋Code＋marker 同時成立才輸出。
- **File and line：** `scrapers/BRAVO.yml:265`（URLs selector）；
  路由 `scrapers/BRAVO.yml:149-159`（`/dvds/` → dvdSceneScraper）。
- **Reproduction：** 隔離檢出內以 node＋jsdom 評估 production YAML selector
  與 postProcess（腳本與完整矩陣見 `docs/qa/evidence/pr103-crossqa-20261104/`）：

| 輸入 | Title | Code | URLs | 其餘欄位 |
|---|---|---|---|---|
| fixture 404-00（`/dvds/00`） | [] | [] | [`https://www.bravo-japan.com/dvds/00`] | 全空 |
| fixture 404-999999 | [] | [] | [`https://www.bravo-japan.com/dvds/999999`] | 全空 |
| 自寫 sitewide-only（僅 canonical＋站級 keywords，無產品 marker） | [] | [] | [`https://www.bravo-japan.com/dvds/`] | 全空 |
| 自寫 ssr-unhydrated（僅 canonical，未水合） | [] | [] | [`https://www.bravo-japan.com/dvds/503`] | 全空 |
| 自寫 missing-title（有 Code，無 Title） | [] | [`501`] | [`.../dvds/501`] | Details／Image 有值 |
| 自寫 wrong-canonical（Code 502，canonical 指 999） | [`Real Title`] | [`502`] | [`.../dvds/999`] | 其餘皆有值，身分不符 |
| fixture cloudflare-challenge（無 canonical） | [] | [] | [] | 全空（唯一全空的無效形狀） |
| 對照：fixture 234／084／046／281／377／384 | 正確 | 正確（含前導零） | 與 Code 一致 | 084 Details 空、Image 空（soldout 過濾生效） |

- **Evidence：** `docs/qa/evidence/pr103-crossqa-20261104/p0-production-selector-matrix.json`
  （production selector＋postProcess 逐案輸出）；`production-dvd-scene-block.json`
  （自 candidate YAML 抽出的 scene block）。
- **Impact：** 任何 /dvds/ 無效網址（404、未水合、站級頁）被 scrape 時，
  部署物即交出一個看似可用的 URL。Stash 是否將 URLs-only 結果存成 scene，
  屬 runtime 未知（Gate B 須以 live 404 實測判定），但「部署物產出部分結果」
  本身已證實，不因 runtime 未知而降級。
- **為何離線測試未擋下：**
  1. 404 兩案的 `mappedExpect`（`tests/fixtures/bravo/bravo-dvds-fixtures.yml`
     404 條目）只斷言 Title／Code／Details／Image 為空，**沒有 URLs 條目**；
     runner 只檢查列出的條目（`tools/verify-scraper-mappings.mjs:98-102`），
     故 manifest 對 URLs 沉默——此為 Agent C v2.3 繼承設計，非 #103 刪減
     （#103 的 manifest 與 C 分支除註解外位元組一致，見 §5）。
  2. `tools/tests/test_bravo_dvd_routes.py::test_404_routes_by_shape_but_is_not_a_product`
     明確釘選 `extract["URLs"] == [url]`，再以 Python 層 `product_validity()`
     （同檔 :797）判無效。該 gate 只存在於測試 harness，Stash 執行期不跑。
  3. 故「測試全過」與「部署物安全」在此脫鉤；不得以測試通過主張已處理。
- **Proposed correction（最小規格，見 §6）。**
- **Retest condition：** §6 矩陣中全部無效輸入的 URLs 為 []，產品頁六案值不變；
  404 兩案新增 URLs=[] 的 mappedExpect；Gate A＋exact-head CI 全過；
  Gate B 以 live 404 驗證零欄位。

## 4. P1 發現

### P1-01 — Date JS 只驗形狀與範圍，不驗真實曆法；parseDate 的 runtime 行為未驗證

- **Actual：** `scrapers/BRAVO.yml:281-290`。JS 以
  `(\d{4})年(\d{1,2})月(\d{1,2})日` 擷取，僅檢查月 1–12、日 1–31。
  實測（production JS 直接執行，完整矩陣見 evidence）：

| 輸入 | JS 輸出 |
|---|---|
| `2018年8月29日`／`2010年09月30日` | `2018-08-29`／`2010-09-30`（正確） |
| 空、`2018年13月1日`、`2018年8月32日`、全形數字、`2018/8/29` | `""`（fail-closed，正確） |
| 前後空白、前後綴文字 | 擷取日期（unanchored regex 行為） |
| `2026年2月30日`／`2026年4月31日`／`2023年2月29日` | `2026-02-30`／`2026-04-31`／`2023-02-29`（**不存在的日期通過 JS**） |
| `12018年8月29日` | `2018-08-29`（5 位年被截為 4 位，邊緣觀察） |

- **Expected：** 不存在的曆法日期應在 YAML 層即 fail-closed 為空，
  而非依賴後續 parseDate 的未驗證行為。
- **Runner divergence（已證實）：** 離線 runner（`tools/verify-scraper-mappings.mjs:57-60`）
  的 parseDate 模擬只接受 layout `2006.01.02`，且其模擬本身會驗真實曆法；
  #103 用的是 `2006-01-02`，runner 會拒此 layout——但 Date 沒有 mappedExpect，
  故 runner 從未執行 #103 的 Date 鏈（JS＋parseDate）。Manifest 亦明載 Date 為
  source-only。#103 自己的測試亦無任何一處執行 production Date JS
  （僅出現來源字串 `2018年8月29日` 作為測試資料）。
- **Impact：** 實務影響有限——G1 已驗證的真實發售日皆為合法日期；
  風險只在模板漂移／異常輸入時，不可能日期抵達 parseDate，而 parseDate 失敗時
  Stash 是清空欄位、報錯整筆，抑或存入錯誤日期，**未經 runtime 驗證，不得斷言**。
  本項列 P1 而非 P0。
- **Proposed correction：** JS 補上月份天數＋閏年檢查，不可能日期回 `""`；
  並補 in-repo 測試直接執行 production Date JS（含上表邊緣案）。
- **Retest condition：** 上表不可能日期全數回 `""`，合法日期不變；
  Gate B 以 live 頁驗證 Date 寫入。

## 5. P2 觀察（非阻擋）

- **P2-01 — DVD Image 不正規化相對 URL。** `scrapers/BRAVO.yml:303` 的 soldout
  過濾已驗證生效，但不像 Clips Image 會補 `https://www.bravo-japan.com` 前綴。
  已驗證封面皆為絕對 wixstatic URL，故無實證失敗；僅在封面 src 改為相對路徑時
  才有影響。建議順手補齊或記錄為已知限制。
- **P2-02 — Manifest runner 的 routeThrough 仍為寬鬆語義。** #103 未動
  `tools/verify-scraper-mappings.mjs`；其 routeThrough 以**任一** sceneByURL
  pattern 為準（:108-113），非 asserted scraper 自身 routes，故無法偵測
  cross-family 路由混淆。此為 main 繼承行為，非 #103 引入；Python 層路由測試
  另行覆蓋路由，風險已部分緩解。
- **P2-03 — Mutation-harness 控制欄位替換。** 相對 Agent C，`test_bravo_dvds.py`
  的 harness 控制將 Duration 條目改為 URLs、Details 條目改為 Tags.Name
  （因 DEF01 移除 Duration、DEF-02 改變 Details selector，harness 頁未建模新結構），
  並將 cross-family mutation 的 canonical 改為外站 host（因 /dvds/ 現為合法路由）。
  變更皆有行內說明且 mutation 目的保留（routeThrough 仍為失敗檢查點），
  但控制覆蓋的欄位集合縮小，屬記錄事項。
- **P2-04 — `EXPECTED_RED` 定義殘留。** 5 處標記皆已退役（`@EXPECTED_RED` 使用
  殘留 0 處），定義本身（`test_bravo_dvd_routes.py:119`）未刪，屬瑣碎清理。
- **P2-05 — 標籤鄰接 selector 的漂移脆性。** 自寫 short-page 顯示：若 品番 前
  h2 不足，`preceding::h2[2]` 會取到導覽列文字（如 `GO to BRAVO-CLIPS`）當 Title。
  此形狀非真實 BRAVO 模板（G1 驗證為固定 4-h2 前導），故列為觀察；
  fixture 迴歸覆蓋已知形狀，未知漂移仍須 Gate B／重驗守門。
- **Pattern 層碰撞（已知上游限制，非 #103 缺陷）：** 以 substring 模型重現
  Stash `strings.Contains` 路由：lookalike host（`evil-bravo-japan.com/dvds/234`）
  與 query 內嵌完整 DVD URL 皆命中 `bravo-japan.com/dvds/` pattern，
  無關 host 則不命中。對應 3 項 strict `KNOWN_LIMITATION` xfail 仍有效，
  與 #103 頁首記載一致。

## 6. 最小補救規格（P0-01）

不更動其他欄位、路由或測試架構：

1. `scrapers/BRAVO.yml:265` 的 URLs selector 改為 marker-gated 形式：
   `//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href`
   （predicate 為絕對路徑，僅當頁面帶有產品 marker 才為真；404／站級／未水合頁
   回傳空，與現有 Title／Code 錨點同一證據基礎）。
2. `tests/fixtures/bravo/bravo-dvds-fixtures.yml` 的 404 兩案各補一條
   mappedExpect：`field: URLs, scraper: dvdSceneScraper, values: []`。
3. 路由測試補一案：以 production YAML selector 對 404 fixture 斷言 URLs 為空
   （取代現行釘選 `URLs == [url]` 的寫法；`product_validity()` 保留作第二道防線，
   不再是唯一防線）。
4. 重跑 §3 矩陣（無效輸入 URLs 全空、產品頁不變）＋ Gate A ＋ exact-head CI；
   Gate B 再以 live 404 驗證零欄位後，方可重審。

替代方案（不建議作為本候選版補救）：consuming-layer validity gate——
須先有一個實際存在且被執行的 gate（Stash 端或匯入端規則），今日 repo 內無此物，
故不能以「未來會有 gate」放行。

## 7. 通過確認（公平性記錄）

- **Core DVD mapping：** 六張產品 fixture 全欄位正確；Code 前導零保留
  （084／046）；084 Details 空、Image 空；Date 兩種零填充皆正規化為 ISO；
  未映射 Duration／Studio／Tags／Performers（scene block 僅 6 欄）。
- **G0 Clips regression：** `clipSceneScraper` selector 零變動（diff 僅頁首註解、
  DVD route、QF 移除）；欄位仍為 Title／Code／URLs／Tags／Details／Image，
  無 Duration、無 dvds 參照；Clips manifest 僅補 `scraper: clipSceneScraper`
  標註，值未動；`BRAVO.test.yaml` 僅列 G1 已驗證的 234／084／046。
- **QueryFragment removal：** `sceneByQueryFragment` 與 `sceneByFragment` 皆缺席
  （YAML 讀值確認）；QF 測試已遷移為缺席斷言；歷史 QF 負向測試保留且通過。
  移除後的 live 行為（clean unsupported vs upstream panic #97）正確列為 NOT_RUN，
  本報告不代為宣稱。
- **Agent B/C integrity：**
  - B：diff 僅註解＋`candidate_config()` idempotent 化＋5 處 EXPECTED_RED 退役；
    退役合理（路由、scraper、QF 移除皆已實裝，皆經本審查獨立驗證）；
    `@EXPECTED_RED` 殘留 0 處；3 處 `@KNOWN_LIMITATION` 仍對應已知限制。
  - C：DVD manifest 與 C v2.3 除註解外位元組一致；10 張 synthetic HTML
    與 mutation harness HTML 皆一致；`test_bravo_dvds.py` 變更皆為基線調適
    （見 P2-03），無 DVD manifest 期待值變更。
  - DVD manifest 通過是因為 DVD 支援已實裝，非因斷言被刪（404 URLs 除外，
    該缺口為 C 原設計，見 §3）。
- **Independent Gate A（隔離檢出重跑，node v24.22.1／python 3.12.3）：**
  validator PASS、validate-sort PASS、validate-all 24/24 PASS、
  pytest 417 passed／2 skipped／3 xfailed、manifests 20/20 PASS
  （DVD 10、Clips 11、歷史 3）、evidence 17／0、docs index 51 OK、
  semantics PASS、session scan 371 檔 PASS、scraper-source 12 passed、
  CI-only 十步全 PASS、format:check 24 警告皆為未動檔案（與基線一致）。
- **Package SHA：** 獨立重建 BRAVO.zip（確定性 zip，僅取決於 BRAVO.yml 位元組），
  SHA-256 `815f49928a9ee4d4445983c810c664ecffca5f7cd3adb2d992f09dd69e7bd283`，
  與 #103 申報值完全一致；index version `71cd377`（實作 commit）。
- **Exact-head CI：** #103 @ afe861f，11 項檢查：10 通過、1 略過
  （Deploy to GitHub Pages）、0 失敗，含 CodeQL 三語言與 Full Test &
  Validation Suite。CI 綠不改變 P0 判定——CI 跑的是同一套未覆蓋 404 URLs
  的測試，故綠色與 P0 並存。

## 8. 限制

- 本審查未執行 Stash runtime：Stash 對 URLs-only 結果的實際處理、
  parseDate 失敗行為、QF 移除後的 live 行為、Date／Image 的 live 值，
  皆為 Gate B 待驗，不得由本報告推定。
- 邊界頁（missing-code／missing-title／wrong-canonical／sitewide-only／
  ssr-unhydrated）為審查者自寫合成頁，用於證明 selector 語義，非真實 BRAVO
  頁面；真實 404 形狀以 Agent C fixture 為準，兩者結論一致。
- 本報告不修改、不合併目標分支；補救規格僅供作者／Controller 採用。
