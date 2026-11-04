# WAVE2E-C-DVD-FIXTURE-REPORT

**Assignment:** WAVE2E-C-DVD-FIXTURES-20261102 / WS-2E-40(Agent C — Fixture / Regression Engineering)
**Branch:** `test/e2e-bravo-dvd-fixtures`
**Report language:** zh-TW
**Status:** `EXPECTED_RED_PENDING_IMPLEMENTATION`(fixture 骨架完成且可交付;正式綠燈須等 Agent F 實作 `dvdSceneScraper` 與 `/dvds/` 路由)
**Spec version:** v2 — 依 Agent A `RAW-DOM-VERIFICATION-ADDENDUM.md`(WAVE2E-A-DVD-DOM-20261102)更新,取代 v1 的文字擷取假設。

---

## 1. Baseline SHA

| 項目 | 值 |
| --- | --- |
| BASE_SHA(分支基底) | `86e34a24642dad2e64ae984e7e9182605e98cbcf`(`fix/e2e-bravo-clips`,PR #93 head) |
| main(參考) | `4bbafca9cf7b5d67117ac41136e74a303c28e4f4` |
| Agent A evidence branch | `research/e2e-bravo-dvd-dom`(RAW-DOM-VERIFICATION-ADDENDUM.md + WAVE2E-A-DVD-DOM-REPORT.md + evidence/) |
| 規劃文件 PR #98 head(參考) | `0c97068c1822fe7db8f069bb0466b921761630cc` |

基底選擇理由:本任務 baseline 清單中的 `bravo-clips-fixtures.yml`、`tools/tests/test_bravo_clips.py` 與支援 `mappedExpect` 的 fixture runner 只存在於 PR #93 分支;PR #93 的 Gate A offline 記錄(19/19 fixture manifests PASS、`pytest tools/tests/` 312 passed、evidence contract 17 records / 0 failures)是可引用的已驗證基準。若 PR #93 在整合前變更,Agent F 必須 rebase 本分支並重跑受影響測試。

## 2. Fixture Architecture

新增 `tests/fixtures/bravo/bravo-dvds-fixtures.yml`(10 cases),完全隔離於:

- 歷史 `bravo-fixtures.yml`(byte-for-byte 保存,SHA-256 `be1885d2…39b2` 不變;其舊版 Wix comp-ID / h1 selector 已失效,但檔案本身依 evidence contract 不可修改);
- Wave 1B `bravo-clips-fixtures.yml`(未觸碰;case 名稱零重疊,不引用任何 `clip-*.html`)。

### v2 規格更新(取代 v1 假設)

| v1 假設(已撤回) | v2 事實(Agent A raw-DOM addendum) |
| --- | --- |
| 084 無 heading、結構未證明 | 084 與其他 8 頁共用同一 22-h2 模板;「無 heading」是擷取層假象 |
| 046 Title selector(`preceding::h2[2]`)不可靠 | 9/9 頁 cardinality=1,`preceding::h2[2]` 恰為標題行1,selector 正確 |
| DVD 頁有 h1、comp-kbfkf16x 等節點 | 現行 DOM h1=0、歷史 comp ID 全部消失;依賴兩者的 selector 皆已過時 |
| Image 建議 fail-closed(無封面) | 產品封面存在(`img[@alt!='' and contains(@src,'wixstatic')]`,n=1);084 封面為 soldout 示意圖,採用與否為明示決策 |
| (v1 未涵蓋) | CDP 為必要條件:未渲染 SSR HTML 不含任何產品欄位 |

### 共用 runner 語意(未修改任何 runner)

- `classification`:completed 頁面含失敗標記即 FAIL;failure 頁面必須含失敗標記。
- `expect`:每條 XPath 同時驗證命中數量(min/max)與代表性值(values)—— 不只測「找得到」。
- `optionalField`:必須 `expectedCount: 0`,斷言欄位在頁面上不存在。
- `mappedExpect` + manifest `scraper`:以 production YAML 真實 selector 對 fixture DOM 求值;多路由下每條 entry 明確 `scraper: dvdSceneScraper`。明確指定 scraper **不代表**證明 Stash 執行時選中該 handler —— 有效路由由 Agent B 測試與 Gate B 驗證。

EXPECTED_RED 設計:基底分支的 `scrapers/BRAVO.yml` 只有 `clipSceneScraper` 路由;`mappedExpect` 的 `scraper: dvdSceneScraper` 令 runner 以 `Ambiguous entrypoint; specify scraper for sceneByURL` 失敗。此失敗模式被 `test_dvd_manifest_execution_state` 明確斷言(未實作 → 要求此失敗;實作後 → 要求全綠),因此本分支不得在 Agent F 完成前併入正式綠燈基準。

## 3. Positive Test Matrix(C-02:9 頁覆蓋矩陣)

Agent A 已驗證 9 個產品頁(046/234/084/281/377/383/384/304/315,2010–2026 發售)。本 manifest 以其中 6 頁的已驗證代表性值建立 positive cases;383/304/315 的完整欄位值(addendum 僅提供 Title/Date 摘要)待 Agent A 補充後即可用同一模板加入。

| Case | HTML(SYNTHETIC_REGRESSION) | Title | Code | URLs | Date | Studio | Duration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-P01 | dvd-synthetic-234.html | 勃起する白き花よ | 234 | …/dvds/234 | 2018年8月29日 | GAYSIAN | 6600s(110min) |
| C-P02 | dvd-synthetic-084.html | 少年集団強姦 | 084 | …/dvds/084 | 2012年11月17日 | Lucifer | 8400s(140min) |
| C-P03 | dvd-synthetic-281.html | 熊ケツ4 | 281 | …/dvds/281 | 2020年7月31日 | ooooPS!! | 7200s(120min) |
| C-P04 | dvd-synthetic-046.html | ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題! | **046**(前導零保留) | …/dvds/046 | 2010年09月30日 | ooooPS!! | 15600s(260min) |
| C-P05 | dvd-synthetic-377.html | 騒乱みだれ穴５ | 377 | …/dvds/377 | 2026年5月31日 | BRAVO! | 6600s(110min) |
| C-P06 | dvd-synthetic-384.html | ナマ狂い種壺待機５ | 384 | …/dvds/384 | 2026年10月22日 | BRAVO-RAW | 6000s(100min) |

Fixture 政策:每個 `dvd-synthetic-*.html` 是依 Agent A 驗證的 CDP rendered-DOM 模板(22-h2 版面、含 U+200B 的標籤 h2、`p.font_8` 說明、`wixstatic` 且 alt 非空的產品圖)所做的**去敏重組**,僅保留 XPath 所需節點與屬性;不含 session material、不含原始 DOM。Title/Code/URLs/Date/Studio/Duration 值為 Agent A 已驗證值;Details 文字(084 除外)為 fixture-local 控制文字,真實文案留在受限工作區。

## 4. Negative Test Matrix(C-03/C-05/C-06/C-07)

| Case | 檔案 | 驗證內容 |
| --- | --- | --- |
| C-N01 `/dvds/00` 404 | dvd-synthetic-404-00.html | 真實 404 結構(title/og:title =「404 | bravo-works」、僅 2 個 h2、無品番);Title/Code/Details/Image 全部空值(fail-closed);canonical 存在但指向 404 URL —— canonical 單獨不得視為有效產品頁 |
| C-N02 `/dvds/999999` 404 | dvd-synthetic-404-999999.html | 同上 |
| C-N03 084 空 Details | dvd-synthetic-084.html(positive case 內) | `p.font_8` 存在但為空;mappedExpect Details=`[""]`,不得回填預設內容 |
| C-N04 084 soldout 封面 | dvd-synthetic-084.html(positive case 內) | soldout 圖存在(cardinality 1,expect 控制)但 Image 不做 mappedExpect;若未來採用,production YAML 必須明示 soldout 決策(pytest 條件守衛) |
| C-N05 site-generic keywords | 所有 fixture | meta keywords 在 9 產品頁與 404 頁完全相同(站級通用);所有 case 均不宣告 Tags mappedExpect;pytest 條件守衛:若 `dvdSceneScraper` 實作 Tags,其 selector 不得引用 `meta[@name='keywords']` |
| C-N06 Cloudflare challenge | failure-cloudflare.html(真實 archived) | classification=failure,不得產出 metadata |

## 5. Field Assertions(C-04 cardinality 矩陣)

每個 positive case 的 `expect` 對以下欄位做 **cardinality=1 + 代表值** 雙重斷言:

| 欄位 | XPath(Agent A 定稿) | mappedExpect |
| --- | --- | --- |
| Title | `//h2[contains(.,'品番')]/preceding::h2[2]` | ✓(6 頁已驗證值) |
| Code | `//h2[contains(.,'品番')]/following::h2[1]` | ✓(046 前導零 `"046"`) |
| URLs(canonical) | `//link[@rel='canonical']/@href` | ✓ + `routeThrough: sceneByURL` |
| Details | `//p[contains(@class,'font_8')]` | 084=`[""]`;其他=fixture-local 控制文字 |
| Image | `//img[@alt!='' and contains(@src,'wixstatic')]/@src` | cardinality 斷言;exact URL 不映射(待決策) |
| Date | `//h2[contains(.,'発売日')]/following::h2[1]` | cardinality+原始值斷言;不做 mappedExpect(offline runner 僅支援 `parseDate: 2006.01.02`,日文日期格式無法離線驗證 —— 已記錄限制) |
| Studio/Label | `//h2[contains(.,'レーベル')]/preceding::h2[1]` | ✓ |
| Duration | `//h2[contains(.,'収録時間')]/following::h2[1]`(×60) | ✓(秒) |
| 有效性 gate | `//h2[contains(.,'品番')]` 存在 | positive=1、404=0 |

特殊守衛:

- `046` 不得轉為 `46`:expect 與 mappedExpect 均為加引號字串 `"046"`;mutation 測試證明 `["46"]` 會 FAIL。
- Title 不得來自網站品牌:模板的 BRAVO-JAPAN / GO to BRAVO-CLIPS h2 存在,但 Title selector 為 `品番` 前第 2 個 h2(標題行1);`test_dvd_manifest_does_not_reuse_stale_h1_selectors` 另禁止 `//h1` 回流。
- 標籤 h2 含 U+200B(如 `\u200b品番`):fixture 保留此真實 hazard;selector 必須用 `contains()`(exact match 會 FAIL),取值後 postProcess 須去除 U+200B。
- 無資料欄位保留空值:404 四核心欄位、084 Details、logo-empty-alt Image。

## 6. Mutation / Failure Detection Results

`tools/tests/test_bravo_dvds.py` 內建 1 個 control + 4 個 mutation 測試。Mutation harness(`dvd-mutation-harness.html`,標示 `SYNTHETIC_REGRESSION / MUTATION_HARNESS_ONLY`)重現 Wave 1B Clips rendered-DOM 標題順序,使 `mappedExpect` 機制對基底分支上實際存在的 `clipSceneScraper` production selector 執行 —— 證明未來驗證 `dvdSceneScraper` 的同一程式碼路徑會拒絕錯誤期望值。

| Mutation | 預期結果 | 對應要求 |
| --- | --- | --- |
| harness control(未變異) | PASS(2 cases verified) | 自我健全性 |
| Code `["46"]`(前導零丟失) | FAIL:`expected ["46"] but got ["046"]` | Code 錯誤 FAIL |
| Image 期望 logo URL | FAIL:values mismatch | 圖片選到 Logo FAIL |
| Title 期望 `[]` 但實際有值 | FAIL:values mismatch | 應為空值卻回傳值 FAIL |
| URLs routeThrough 指向 /dvds/(clips 路由) | FAIL:`does not match sceneByURL` | URL 指向其他作品 FAIL |

本 agent 連線僅透過 GitHub connector(無本地 checkout / node 環境),C-07 指令**尚未在 repo 環境執行**;上表已在本機沙箱以 lxml 對 `verify-scraper-fixtures.mjs` / `verify-scraper-mappings.mjs` 的邏輯做等價模擬:9 個 synthetic cases 全 PASS(含 084 Details=`[""]`、logo-empty-alt Image=[]、404 fail-closed),harness control PASS,4 個 mappedExpect mutations 均如預期 FAIL。正式執行由 Agent F / controller 在整合分支 exact HEAD 補齊。

## 7. Evidence Contract Preservation

- `tests/fixtures/bravo/bravo-fixtures.yml` 未修改(byte-for-byte 等於 main);SHA-256 `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2` 由 `test_historical_fixture_manifest_digest_unchanged` 獨立固定(artifact / sha256 / captured_at 三重比對)。
- `docs/archive/evidence/status/bravo.yml` 與所有 archived evidence 未觸碰。
- `scrapers/BRAVO.yml`、`tools/tests/test_bravo_clips.py`、`tools/run_fixture_manifests.py`、`tools/verify-scraper-fixtures.mjs`、`tools/verify-scraper-mappings.mjs` 皆未修改。
- 新增檔案全部為獨立新檔;唯一共用既有資產是唯讀參考 `failure-cloudflare.html`。
- Agent A 的原始 rendered DOM(含 session material)留在受限工作區,本分支僅提交去敏重組 fixture。

## 8. Unresolved Dependencies

1. **Agent A(WS-2E-10)**:383/304/315 的完整欄位值(目前 addendum 僅提供 Title/Date 摘要);234/281/046/377/384 的 Details 實際文案與 Image 完整 URL(留在受限工作區)。
2. **Agent F / controller 決策**:084 soldout 封面(BR-084soldout.jpg)是否採用為 Image;若採用,須在 production YAML 明示並補 mappedExpect。
3. **Agent F(WS-2E-30)**:`dvdSceneScraper` 與 `/dvds/` `sceneByURL` 路由實作;實作後本 manifest 必須轉綠。
4. **Agent B(WS-2E-20)**:有效路由選擇(`strings.Contains` first-match 風險)與 QueryFragment 安全測試。
5. **PR #93 接受狀態**:本分支以 PR #93 head 為基底;PR #93 變更需 rebase / 重驗。

## 9. Agent F Integration Instructions

1. Cherry-pick 本分支 commit,記錄來源 commit SHA。
2. 在 `scrapers/BRAVO.yml` 加入 `/dvds/` `sceneByURL` 路由與 `dvdSceneScraper`,selector 依 Agent A addendum §5 定稿規格(Title/Code/URLs/Details/Image/Date/Studio/Duration;postProcess 須去除 U+200B 與空白;Date parse 須同時支援 `2010年09月30日` 與 `2018年8月29日`)。
3. 執行(整合分支 exact HEAD):

```bash
python tools/run_fixture_manifests.py
python -m pytest tools/tests/test_bravo_dvds.py -v
python tools/check_evidence_contract.py
python tools/scan_session_material.py
```

4. 判讀:
   - 整合前:manifest runner 對 `bravo-dvds-fixtures.yml` FAIL(`Ambiguous entrypoint`)為預期;`test_bravo_dvds.py` 全綠。
   - 整合後:`bravo-dvds-fixtures.yml` 必須 PASS;`test_dvd_manifest_execution_state` 自動翻轉為要求全綠。任何中間狀態視為 FAIL;不得修改 fixture expected values 湊綠。
5. 條件守衛(實作後自動生效):不得使用 `//h1` 或 `comp-kbfkf16x` 等 stale selector;Tags 不得映射 meta keywords;`driver.useCDP: true` 必須保留。
6. Runner 改善建議(不自行修改):`routeThrough` 目前無法表達「此 URL 應由 dvdSceneScraper 而非 clipSceneScraper 路由」;如需 per-scraper 路由斷言,另立 reviewed PR 擴充。

## 10. Mandatory Handoff

```yaml
ASSIGNMENT_ID: WAVE2E-C-DVD-FIXTURES-20261102
WORKSTREAM_ID: WS-2E-40
AGENT_ROLE: Agent C
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "86e34a24642dad2e64ae984e7e9182605e98cbcf"
BRANCH: test/e2e-bravo-dvd-fixtures
HEAD_SHA: "(見 branch commit;本報告與檔案同 commit)"
CHANGED_FILES:
  - tests/fixtures/bravo/bravo-dvds-fixtures.yml
  - tests/fixtures/bravo/dvd-synthetic-234.html
  - tests/fixtures/bravo/dvd-synthetic-084.html
  - tests/fixtures/bravo/dvd-synthetic-281.html
  - tests/fixtures/bravo/dvd-synthetic-046.html
  - tests/fixtures/bravo/dvd-synthetic-377.html
  - tests/fixtures/bravo/dvd-synthetic-384.html
  - tests/fixtures/bravo/dvd-synthetic-404-00.html
  - tests/fixtures/bravo/dvd-synthetic-404-999999.html
  - tests/fixtures/bravo/dvd-synthetic-logo-empty-alt.html
  - tests/fixtures/bravo/dvd-mutation-harness.html
  - tools/tests/test_bravo_dvds.py
  - WAVE2E-C-DVD-FIXTURE-REPORT.md
DELIVERABLES:
  - "DVD fixture manifest v2(10 cases:6 Agent A verified positive、2 realistic 404 fail-closed、1 logo-empty-alt guard、1 Cloudflare failure)"
  - "tools/tests/test_bravo_dvds.py(結構/Agent A 矩陣/404/084/keywords/CDP/stale-selector 守衛 + execution-state + 1 control + 4 mutations)"
  - "本報告"
EVIDENCE:
  - "Agent A RAW-DOM-VERIFICATION-ADDENDUM.md(9 產品頁 + 2 404 頁,cardinality=1,CDP 必要)"
  - "archived evidence digest be1885d2…39b2(歷史 manifest,未修改)"
  - "PR #93 Gate A offline 記錄(19/19 manifests、312 pytest、evidence contract 0 failures)"
  - "本 agent 沙箱 lxml 等價模擬:9 synthetic cases PASS、harness control PASS、4 mutations 如預期 FAIL"
TEST_RESULTS:
  - "python tools/run_fixture_manifests.py: NOT_RUN_IN_AGENT_SESSION(EXPECTED_RED_PENDING_IMPLEMENTATION)"
  - "python -m pytest tools/tests/test_bravo_dvds.py -v: NOT_RUN_IN_AGENT_SESSION(程式已交付;沙箱靜態+lxml 模擬全綠)"
  - "python tools/check_evidence_contract.py: NOT_RUN_IN_AGENT_SESSION(未觸碰任何 evidence 檔)"
  - "python tools/scan_session_material.py: NOT_RUN_IN_AGENT_SESSION(新增檔案僅含 example.invalid 控制值)"
KNOWN_LIMITATIONS:
  - "dvdSceneScraper 未實作;整體 Fixture Gate 非 PASS"
  - "383/304/315 尚未入 manifest(待 Agent A 補完整欄位值)"
  - "Image/Date 無 mappedExpect:Image 待 soldout 決策;Date 受 offline runner parseDate 限制"
  - "Details 文案(084 除外)為 fixture-local 控制文字;真實文案在受限工作區"
DEPENDENCIES:
  - "Agent A: 383/304/315 完整欄位值;Details/Image 完整值(部分)"
  - "Agent F: dvdSceneScraper implementation + soldout 決策"
  - "Agent B: effective routing tests (Gate B)"
  - "PR #93 acceptance (baseline stability)"
RISKS_AND_DECISIONS:
  - "084 soldout 封面採用與否 = Agent F/controller 明示決策;pytest 條件守衛已備"
  - "Tags 不映射 meta keywords(站級通用);若未來要映射需新證據"
  - "基底綁定 PR #93 head;PR #93 變更需 rebase"
HANDOFF_STATUS: READY
```
