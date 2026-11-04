# PR #104 Independent Cross-QA Report — WAVE2E-CROSSQA-PR104-20261104

Reviewer: Muse Account ①（PR #103 作者；本審查不以 PR #103 為 oracle，裁決依據為 G0/G1 接受證據、Controller 政策與 Stash 官方行為）
Target: PR #104, branch feat/e2e-bravo-dvds-para, HEAD `86ce058a49f9d762b193f91c80cc8be867d1c341`（隔離 clone 內實測 log 確認：86ce058 + 4f598d8，parent = main ff236c9）
Baseline: main `ff236c9e91e27321e93f59d2bf12488db714dfc7`
環境：node v24.22.1、Python 3.12.3、lxml 6.1.3、jsdom ^30.0.1（repo 相依）
模式：唯讀候選、離線。候選 checkout 未被修改（所有產出寫於 output/）。

## 總裁決：CROSS_QA_PASS_WITH_NONBLOCKING_FINDINGS

無 P0。PR #104 對真實 404 模板的 fail-closed 是真實成立的改善（雙評估器實證）；殘餘風險（假 marker、Date 範圍驗證、antchfx runtime）皆為 P1/P2，且主要殘餘已由作者在 YAML 註解中自我揭露。**Gate B = NOT_RUN；本裁決不構成 merge/deploy 批准。**

## 1. P0 — Canonical predicate 實測（§4）

受測 selector（PR #104 生產 YAML 第 228 行，逐字）：
`//link[@rel='canonical'][//h2[contains(.,'品番')]]/@href`

### 1.1 雙評估器結果（完全一致）

評估器 (a) lxml 6.1.3（XPath 1.0）；(b) jsdom 30 的 `document.evaluate`（即 repo fixture runner `tools/verify-scraper-mappings.mjs` 與候選 integration test 實際使用的評估器）。16 頁 × 兩評估器，結果逐格相同（evidence: predicate-lxml-output.txt、predicate-jsdom-output.txt）。

| 頁面 | Gated URLs | Plain URLs（對照） | Title | Code |
|---|---|---|---|---|
| synthetic 234 | /dvds/234 ✓ | /dvds/234 | 勃起する白き花よ | 234 |
| synthetic 084 | /dvds/084 ✓ | /dvds/084 | 少年集団強姦 | **084**（前導零保留） |
| synthetic 046 | /dvds/046 ✓ | /dvds/046 | ゆるゆる雄太… | **046** |
| synthetic 281/377/384 | 各自 canonical ✓ | 同 | 各自標題 | 281/377/384 |
| synthetic logo-empty-alt（281 變體） | /dvds/281 ✓ | 同 | 熊ケツ4 | 281（Image=[]，alt 空資產正確排除） |
| **404-00** | **[]** ✓ | /dvds/00（plain 會洩漏） | [] | [] |
| **404-999999** | **[]** ✓ | /dvds/999999（plain 會洩漏） | [] | [] |
| cloudflare challenge | [] ✓ | [] | [] | [] |
| adv canonical-only 404（/dvds/555） | **[]** ✓ | /dvds/555 | [] | [] |
| adv 品番 在 `<p>`（非 h2） | [] ✓ | /dvds/888 | [] | [] |

結論（正面）：對真實 404 形狀（有 canonical、無 品番 h2），predicate 在兩個 XPath 1.0 評估器下都確實抑制 canonical；且 404 頁上 Title/Code/Details/Date/Image 本就全空（品番/発売日 錨定 + alt 條件），故「404 → 零欄位」在離線層級完整成立，不是只有 URLs 被擋。

### 1.2 語意分析：predicate 內 `//h2` 是絕對路徑（實證）

對抗頁 `adversarial-marker-after-canonical-position.html`：canonical 在 `<head>`、品番 h2 只存在於 body 末端深層 `<footer><div><div>` 內，與產品結構無關 — gated selector 仍回 /dvds/234（兩評估器皆然）。若 `//h2` 相對於 link 節點求值，head 內的 link 不可能匹配 body footer 的 h2。故 predicate 語意 = 「整份文件任一處存在 品番 h2」，非「該 canonical 所屬產品區塊存在 marker」。作者 YAML 註解對此語意的描述（"predicate is an absolute path, true only when the page carries a product marker"）準確。

### 1.3 對抗案例：predicate 沒強制的部分

| 案例 | 結果（雙評估器一致） | 判定 |
|---|---|---|
| (iii) 假 marker：canonical(/dvds/777) + 任意位置 品番 h2、無產品結構 | **URLs 被接受**；且 Title 誤抽為 `BRAVO-JAPAN`（preceding::h2[2]）、Code 空 | 假陽性 partial metadata 仍可能（P1-1） |
| (iv) 品番+Title 存在、Code h2 缺失 | URLs 被接受；Code 誤抽為次一 h2 `発売日` | selector 無法偵測 Code 缺失/錯位（P1-1 同源） |
| (v) 真產品結構（Code 234）但 canonical 指向 /dvds/999 | URLs=/dvds/999 被接受，與 Code 不一致 | 無法偵測 Code↔canonical mismatch（P1-1 同源） |

作者自述核對（BRAVO.yml 第 93–95 行）：作者明言完整身份契約（Code == canonical 末段、canonical == requested URL）「is a consuming-layer / Gate B check, not expressible in YAML」，並點名 template drift 風險。此自述與其實測行為一致，其測試宣稱（integration test docstring）也只宣稱「404 yields no fields」，未宣稱完整身份驗證。**無過度宣稱 finding**；殘餘屬已揭露的設計邊界。

### 1.4 Predicate 實際強制的契約（最終判定）

- 強制：文件存在至少一個含「品番」的 **h2**（元素型別限定，`<p>` 不算）→ 才放行 canonical 作為 URLs。
- 未強制：Title 非空且正確、Code 非空且正確、Code == canonical 末段、canonical == requested URL、marker 與產品區塊的結構關聯。
- Runtime 風險（未驗證）：Stash 實際使用 antchfx/xpath 求值；predicate 內嵌絕對路徑 `//` 在 XPath 1.0 規格上合法，lxml 與 jsdom 均支援，但 antchfx 對巢狀 predicate 路徑的支援未在本審查中直接驗證（repo 內無 Go 工具可跑 antchfx）。**離線通過 ≠ antchfx 通過** — Gate B 必須把 gated selector 的 live 行為列為必要驗證項（見 P1-2）。

## 2. P0 — Clips/DVD 迴歸（§5）

- 全套 pytest（tools/tests/）：**442 passed, 2 skipped, 3 xfailed，exit 0**（36.85s，pytest-full.log）。BRAVO 三套（routes+dvds+clips）111 passed；integration 27 passed。
- 結構實測（yaml 解析）：top-level 無 sceneByFragment、無 sceneByQueryFragment；sceneByURL 恰 2 條（clips→clipSceneScraper、dvds→dvdSceneScraper）；DVD 欄位恰 {Title, Code, URLs, Details, Date, Image}；Clips 欄位與 main 相同 {Title, Code, URLs, Tags, Details, Image}（無 Duration）。
- DVD 正例：234/084/046 Title/Code 如 §1.1 表；084 Details 為空字串（非缺漏）；084 Image 原始 selector 命中 soldout 圖、經生產 JS postProcess 濾除（§4 實測）；Date 兩種來源格式正規化正確。
- 路由安全：routes 測試含 www/non-www、exactly-one-route、lookalike host、foreign-host query 內嵌、query-hijack 碰撞（作者將 Stash `strings.Contains` 匹配的已知碰撞如實建模為測試案例，未宣稱已解決）。
- Duration source-only 證據保留於 C manifest expect 層（manifest 全綠，見 §3）。

## 3. P0 — Shared fixture runner（§6）

Diff 審查（verify-scraper-mappings.mjs +13 行）：`routeThrough` 在 assertion 有指定 `scraper` 時，patterns 只取該 scraper 自身 routes 的 URL；未指定時行為與舊版完全相同。getField 未變動。

對抗實測 9/9 符合預期（runner-adversarial-output.txt）：

| # | 案例 | 新版結果 |
|---|---|---|
| 1 | dvds URL 斷言 via clipSceneScraper（cross-family） | **FAIL**（修正成立） |
| 2 | dvds URL via dvdSceneScraper | PASS |
| 3 | clips URL via clipSceneScraper | PASS |
| 4 | 雙 handler 未指定 scraper（ambiguous） | FAIL（既有 guard） |
| 5 | 指定不存在的 handler | FAIL（fail-closed；錯誤訊息文案誤導，P2-1，既有問題非本 diff 引入） |
| 6 | 單 handler scraper 未指定 scraper | PASS（語意未變） |
| 7 | foreign-host canonical | FAIL |
| 8 | invalid URL canonical | FAIL |
| 9 | clip handler 在 dvd 頁抽取 | FAIL |

舊版對照（runner-old-behavior.txt）：以 main(ff236c9) 版 runner 跑案例 1 → **PASS**，證實舊缺陷真實存在、新版確實修正。全量 manifests：**20/20 PASS**，含全部非 BRAVO 站台 — 無既有驗證語意弱化或回歸的證據。判定：隔離改善成立。

## 4. P1 — Date / Image JS 實測（§7）

以候選生產 YAML 逐字抽出的 JS 用 node 執行（js-postprocess-output.txt）。

### Date（只有 javascript 一步，無 parseDate 步驟）

| 輸入 | 輸出 | 判定 |
|---|---|---|
| 2018年8月29日 / 2010年09月30日 | 2018-08-29 / 2010-09-30 | ✓ 兩種填零形式皆正規化 |
| 空字串、2018/8/29、缺「日」 | "" | ✓ fail-closed |
| **2018年13月1日** | **2018-13-01** | ✗ 無月份範圍檢查（P1-3） |
| **2018年1月32日** | **2018-01-32** | ✗ 無日範圍檢查（P1-3） |
| **2019年2月30日** | **2019-02-30** | ✗ 無日曆驗證（P1-3） |
| 內嵌文字「発売日は2018年8月29日です」 | 2018-08-29 | regex 未錨定（selector 已錨定該 h2，實務風險低） |

區分：PR #104 的 Date JS 只做**格式驗證**（\d{4}年\d{1,2}月\d{1,2}日 → 填零），不做**範圍/日曆驗證**，且 YAML 無 parseDate 步驟可作後盾。Go `time.Parse` 本身會拒絕 2/30 與 13 月 — 但本 YAML 根本不經 parseDate；Stash 對無 parseDate 的 Date 字串值如何處理（嘗試多布局解析、失敗時丟欄位或報錯）屬 runtime 未知，須 Gate B 驗證。YAML 註解「Unparseable input maps to empty, never a guessed date」對範圍外日期不準確（2018-13-01 是被「製造」出來的無效日期字串，非源數據）。來源日期由站方產生、實務上合法，故列 P1 非阻斷，建議合併前補範圍檢查或加 parseDate。

### Image

- soldout 大小寫不敏感全濾除（soldout/SoldOut/SOLDOUT ✓）；真封面原樣保留；query 參數剝除；protocol-relative 與 http 升級 https；相對路徑以 bravo-japan.com 為基底補全（在 wixstatic selector 下此分支實務上不會觸發，屬無害死碼）。
- 子字串過濾的副作用：任何檔名含 "soldout" 子字串（如 `soldoutish-cover.jpg`）也被濾除 — 方向是 fail-closed，可接受（P2-2）。
- JS 本身不驗 host；host 限制由 selector（wixstatic + alt 非空）提供，屬正確分工。

## 5. P1 — CI 完整性（§8）

- `git show 86ce058`：修復內容與 commit 訊息一致 — `test_bravo_dvd_integration.py` 的 `eval_xpath` 由硬編碼 `PATH=/usr/bin:/bin` 改為繼承父環境（`{**os.environ, "SEL": selector}`）並 import os。修復合理、最小。
- 原失敗 5 測 = `test_production_urls_selector_is_fail_closed_on_404` 的 5 個參數化案例（該檔唯一用 eval_xpath 者）。本機以 -v 重跑全檔：**27 passed、0 skipped**，5 個 URL-selector 案例逐一 PASSED — 真實執行（經 node+jsdom 子程序），非 skip 掩蓋。
- 本機全套：442 passed（見 §2）；validator `--ci` exit 0、validate-sort 0、semantics 0、session-scan 0、evidence-contract 0；format:check exit 1 的 24 檔全為 main 既有基線檔案（docs/舊 scrapers/skill-evals），無一屬 PR #104 變更檔。
- 套件重建（build_scraper_source.py + --verify-only，exit 0）：本機自算 **BRAVO.zip SHA-256 = `10fa6183cfe0d5d4cfba7451a27beb3cce0664318ae999f3c6c6bf1b841332fa`**，index version `4f598d8`（未沿用作者數字）。
- GitHub 端 checks：本審查無 connector checks 讀取工具，未獨立驗證 PR #104 在 GitHub 上的 exact-head checks 狀態 — 記為未驗證項（不影響離線裁決，父代理可用瀏覽器補查 afe… 對應 PR #104 head 86ce058 的 checks 頁）。

## 6. Findings

### P0
- 無。

### P1
- **P1-1 假 marker / 身份不一致無法偵測**：canonical + 任意位置 品番 h2 即放行 URLs，且可伴隨誤抽 Title（`BRAVO-JAPAN`）；Code 缺失時誤抽 `発売日` 為 Code；Code↔canonical mismatch（234 vs /dvds/999）不被偵測。重現：evidence 內 adversarial-fake-marker-777.html、adversarial-code-missing.html、adversarial-canonical-mismatch.html + predicate 雙評估器輸出。作者已於 YAML 註解揭露此邊界（consuming-layer/Gate B），故非過度宣稱；列為 Gate B 必測與 Controller 裁量項。
- **P1-2 antchfx runtime 未驗證**：gated predicate 的巢狀絕對路徑在 lxml/jsdom 成立，但 Stash 的 antchfx/xpath 未直接驗證；若 antchfx 不支援此 predicate 形式，live 行為可能從「fail-closed」變成「selector 錯誤/整欄位失敗」。Gate B 必測。
- **P1-3 Date 無範圍/日曆驗證且無 parseDate 後盾**：2018年13月1日 → `2018-13-01`、2019年2月30日 → `2019-02-30` 被原樣輸出（js-postprocess-output.txt）。與 YAML 註解「never a guessed date」不完全相符。建議：JS 補 month 1–12/day 1–31（至少）或加 parseDate 步驟。

### P2
- **P2-1**（既有、非本 PR 引入）getField 對「指定了但不存在的 handler」報 "Ambiguous entrypoint; specify scraper"，訊息誤導但行為 fail-closed。
- **P2-2** Image soldout 子字串過濾會誤殺檔名僅含該子字串的真封面（fail-closed 方向，可接受）；Image JS 的相對路徑補全在現行 selector 下為死碼。

## 7. 子裁決（§9）

| 面向 | 裁決 |
|---|---|
| Functional correctness | PASS_OFFLINE（442 全綠；selector 與 G1 驗證值一致；雙路由正確） |
| Product validity | PASS_WITH_FINDINGS（真實 404 完整 fail-closed；假 marker/mismatch 殘餘 = P1-1，已揭露） |
| Routing safety | PASS_OFFLINE（route 測試覆蓋 collision/lookalike/query 內嵌；Stash Contains 匹配的已知限制如實建模） |
| Fixture runner compatibility | PASS（缺陷修正經舊版對照證實；20/20 manifests；9/9 對抗案例） |
| CI integrity | PASS（env 修復屬實、5 測真跑真過；GitHub exact-head checks 經主代理補查全綠，見附錄） |
| Runtime uncertainty | OPEN（antchfx predicate、QF 移除後 live 行為、無效 Date 字串的 Stash 處理 — 皆屬 Gate B） |
| Release readiness | NOT_READY（Gate B NOT_RUN；merge/deploy 未授權） |

## 8. 與 PR #103 的事實差異（最後對照，不以 103 為 oracle）

| 面向 | PR #104（86ce058） | PR #103（afe861f） |
|---|---|---|
| DVD URLs | gated predicate（品番 存在才放行） | plain canonical（404 會洩漏 URLs-only partial） |
| Date | JS-only；無範圍檢查；無 parseDate | JS 含 month/day 範圍檢查 + parseDate `2006-01-02` 後盾 |
| Image JS | soldout 濾除 + URL 正規化（query 剝除、https 升級、相對路徑補全） | 僅 soldout 濾除 |
| Code trim | replace-regex | JS trim（功能等價） |
| 測試結構 | 新增 test_bravo_dvd_integration.py（27 測，以 node 執行生產 JS/XPath）；**修改共用 runner** routeThrough | 無 integration 檔；未動共用 runner |
| 全套 pytest（本機同環境） | 442 passed | 417 passed（其交付時數字） |

兩者皆為離線證據，不構成兩份 Gate B。

## Evidence

`~/workspace/crossqa-pr104/output/evidence/`：commands.log、predicate-lxml-output.txt、predicate-jsdom-output.txt、predicate_lxml.py、predicate_jsdom.mjs、adversarial-*.html（6 頁）、runner_adversarial.mjs、runner-adversarial-output.txt、runner-old-behavior.txt、js_postprocess_test.py、js-postprocess-output.txt、pytest-full.log、pytest-integration.log、validators.log、format-warn.txt、npm-ci.log、build.log、SHA256SUMS。

## 附錄：GitHub Exact-Head CI 補查（主代理，2026-11-04 15:17–15:19 CST）

唯讀查核 PR #104 Checks 頁，HEAD 確認為 `86ce058a49f9d762b193f91c80cc8be867d1c341`（與本報告受審 HEAD 一致）：
**10 項檢查全數完成 — 9 success + 1 skipped + 0 failure**。明細：CodeQL Analyze ×3 success、
code scanning passed、Full Test & Validation Suite success、fixture-manifests success、
pr-check success、evidence success、Build installable scraper source success；
Deploy to GitHub Pages = skipped（Draft PR 預期行為）。無進行中項目。
據此 CI_INTEGRITY 子裁決由 PASS_LOCAL 升級為 **PASS**（本機重跑 + 遠端 exact-head 雙邊一致）。
