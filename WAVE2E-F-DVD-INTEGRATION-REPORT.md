# WAVE2E-F-DVD-INTEGRATION-REPORT

Assignment: WAVE2E-F-DVD-INTEGRATION-20261104-R3 / WS-2E-30、WS-2E-50、WS-2E-70
角色：Agent F（BRAVO YAML 唯一正式寫入者／整合者）
報告語言：zh-TW
日期：2026-11-04（Asia/Taipei）
狀態：本地實作完成並本地 commit；**未推送、未開 PR**（推送由主代理整批處理）

## 1. 摘要

- 基線：`main@ff236c9e91e27321e93f59d2bf12488db714dfc7`（PR #93 已合併，G0 ACCEPTED_CLOSED）。
- 本地分支：`feat/e2e-bravo-dvds`，自 `origin/main` 建立。
- 受測候選 HEAD（實作＋測試）：`84f7a2cda4f70938d6f4c2de54ff6763c3dbc535`
  （feat commit `eaec398` ＋ test 整合 commit `84f7a2c`；本報告/handoff 為其後的 docs commit，僅新增本報告兩檔，不含程式變更）。
- 完成：`dvdSceneScraper` 正式實作、`/dvds/` 路由、QueryFragment 移除（WS-2E-QF-001）、Agent B/C 選擇性整合、Gate A 離線全跑。
- **Gate B：NOT_RUN；Gate C：NOT_RUN。** 無任何 Stash 實例操作、無 live 測試、無合併、無部署。
- F-03 誠實分類：殘餘風險 **`BLOCKED_UNSAFE_PARTIAL_METADATA`**（詳 §5）。本報告不宣稱 YAML 層已強制 fail-closed。

## 2. F-00 整合 Inventory

| Source       | Accepted SHA                                                                                                    | Files Required                                                                                                                     | Import Method                   | Conflicts                                                                                                                 |
| ------------ | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| G0 main      | `ff236c9e91e27321e93f59d2bf12488db714dfc7`                                                                      | 全部基線（BRAVO.yml、Clips manifest/tests、歷史 manifest）                                                                         | 自 origin/main 建立分支         | 無（開始前已核對 HEAD 與主代理提供值一致）                                                                                |
| Agent A      | `b2f41e179984049940a1e3b1d0754d8c25b0b0da`                                                                      | `docs/research/wave2e/**`（19 檔）                                                                                                 | 唯讀參考，未匯入任何檔案        | 無                                                                                                                        |
| Agent B      | `1f147f1059f0a183216a9d7c90f118f872690dbf`                                                                      | 僅 `tools/tests/test_bravo_dvd_routes.py`                                                                                          | 選擇性 checkout ＋ F 適配（§6） | B 分支相對 main 帶 15 路徑（含合併前基線差異）；其 BRAVO.yml、Clips fixtures/tests 版本已被 PR #93 合併版取代，**未匯入** |
| Agent C      | `8c9daf2ddfbdd06877c850608ee3f8b366b0e8f5`                                                                      | `bravo-dvds-fixtures.yml`、`dvd-synthetic-*.html`（10）、`dvd-mutation-harness.html`、`tools/tests/test_bravo_dvds.py`（共 13 檔） | 選擇性 checkout ＋ F 適配（§6） | C 的兩份報告文件（repo 根與 docs/research）未匯入，provenance 於本報告交代；harness 前提衝突 3 處（§6）                   |
| Agent D / G1 | QA `37ea85192aa31da83e39c52d5c0649561523b77d`；Controller acceptance `d7429e92dd0ccc7eea0ab361014ff49c8b18c4f2` | QA 證據                                                                                                                            | 唯讀參考                        | 無                                                                                                                        |

歷史 fixture 完整性（SOURCE-INTEGRITY）：`tests/fixtures/bravo/bravo-fixtures.yml`
SHA-256 = `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`，與證據紀錄一致，整合前後未變。

重疊檔案：`scrapers/BRAVO.yml`（F 單一寫入者，自 main 版修改）、
`tests/fixtures/bravo/bravo-clips-fixtures.yml`（F 加 scraper 命名，§6-1）、
`tools/tests/test_bravo_clips.py`（F 更新路由/QF 契約並新增 DVD 結構斷言）。

## 3. QF 相容性稽核（WS-2E-QF-001 前置）

搜尋範圍（於 main 基線全 repo）：`sceneByQueryFragment` / `QueryFragment` 字串，涵蓋
`*.py`、`*.yml`、`*.yaml`、`*.md`、`*.mjs`、`*.js`、`*.sh`、`*.json`；另查 `.github/workflows/`、
GraphQL 相關工具（`tools/*.py`）與 BRAVO 專屬引用。

發現：

- BRAVO 本身：`scrapers/BRAVO.yml` 的 entry 與註解（移除對象）。
- BRAVO 專屬測試：`tools/tests/test_bravo_clips.py::test_query_fragment_preserves_url`
  （舊契約斷言，由 F 改為移除斷言）。Agent B 的 reproduction/readiness 測試（已整合，現斷言移除完成）。
- 通用檢查（皆為「存在時才驗證」邏輯，缺席不構成要求）：
  `tools/tests/test_scrapers.py`、`tools/scraper-quality-gate.sh`、
  `validator/index.mjs`（僅在 `sceneByName` 存在時要求 QF）、
  `tools/check_metadata_feed.py`（同上，僅 sceneByName 觸發）。
- 政策文件：`docs/21-quality-gate-rules.md` 的 QF 規則是「與 sceneByName 搭配」的通用規格；
  BRAVO **無 sceneByName、無站內搜尋流程**，不存在 Scene Edit query dropdown 的進入點，
  該 entry 因此是 orphan。`docs/66` 的 WS-2E-QF-001 決策為本檔案的專屬裁定，優先於通用規格。
- `docs/qa/PR93-DURATION-DEFERRED-SPEC.md` 僅歷史脈絡提及，非消費者。

未發現：任何 GraphQL 腳本、workflow、或 repo 內直接呼叫 BRAVO QueryFragment 的消費者。
無法查核：repo 外部的 Stash 使用紀錄（例如使用者在 Stash UI 內以 QueryFragment 模式手動
套用 BRAVO 的紀錄）不在本 repo 可見範圍；此限制已由 docs/66 決策接受。

**結論：`ORPHAN_CONFIRMED`，無不可或缺的直接消費者，未觸發 DECISION_EXCEPTION，依決策移除。**
移除後行為（離線層級）：QF-234／QF-084／QF-284 在設定層為「無 handler」；
live 層究竟是乾淨的 unsupported 還是 upstream panic（issue #97），**只能由 Gate B 判定**，
本報告不預先標 PASS 或 FAIL_UPSTREAM_BLOCKED（無 live 證據）。

## 4. F-01／F-02 實作（scrapers/BRAVO.yml）

路由（`sceneByURL`，宣告順序即比對順序）：

| URL                                                    | Handler                                            |
| ------------------------------------------------------ | -------------------------------------------------- |
| `bravo-japan.com/clips/`、`www.bravo-japan.com/clips/` | `clipSceneScraper`（與 main 解析後完全相同，未動） |
| `bravo-japan.com/dvds/`、`www.bravo-japan.com/dvds/`   | `dvdSceneScraper`（新增）                          |

Clips 區塊經程式比對：`clipSceneScraper` 與 `driver` 的解析結果與 main **完全相同**；
`driver.useCDP: true` 維持。`sceneByFragment` 保持不存在；`sceneByQueryFragment` 整段移除。

dvdSceneScraper 生產欄位（XPath 一律採用 Agent A 已驗證證據，無自創 selector）：

| 欄位    | Selector                                                                                     | A 證據來源                                                                                                                                                                                               |
| ------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Title   | `//h2[contains(.,'品番')]/preceding::h2[2]`                                                  | RAW-DOM-VERIFICATION-ADDENDUM §2/§5（9 頁 cardinality=1）；G1 excerpts 234/084/046 標題行1；D 獨立 replay PASS                                                                                           |
| Code    | `//h2[contains(.,'品番')]/following::h2[1]`                                                  | 同上；046/084 前導零於來源原樣保留（字串，不由 URL 推導）                                                                                                                                                |
| URLs    | `//link[@rel='canonical']/@href`                                                             | 同上（9/9 與頁面 URL 一致）                                                                                                                                                                              |
| Details | `//p[contains(@class,'font_8')]`                                                             | 同上（每頁恰 1 個；084 為空，維持空，不借鄰近文字）                                                                                                                                                      |
| Date    | `//h2[contains(.,'発売日')]/following::h2[1]` ＋ JS 驗證/正規化 ＋ `parseDate: "2006-01-02"` | A §2：來源值為日文格式且零填充混用（`2018年8月29日`／`2010年09月30日`）。JS 僅接受 `YYYY年M月D日` 形狀並轉 ISO，否則回空（fail-closed）；離線實證 4 正例轉換正確、1 反例回空（§7）                       |
| Image   | `//img[@alt!='' and contains(@src,'wixstatic')]/@src` ＋ JS soldout 拒絕                     | A §2/§5（產品頁 cardinality=1、404 頁 0、alt=標題行1）；084 封面為 `BR-084soldout.jpg` 售罄圖（A §2 註記、C synthetic fixture 同名），非核准封面，故 postProcess 對含 `soldout`（不分大小寫）的 src 回空 |

禁止映射（已由結構測試斷言缺席）：`Duration`、`Studio`、`Tags`、`Performers`。
未加入任何未支援 key（無 `enabled: false` 類）。

Duration 還原準備（source 層級，不進生產 YAML）：

| 項目                     | 內容                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Source XPath             | `//h2[contains(.,'収録時間')]/following::h2[1]`（A §2 VERIFIED）                                             |
| 來源值（分鐘，整片總長） | 234→110、084→140、281→120、046→260、377→110、384→100                                                         |
| 換算秒數                 | ×60：6600／8400／7200／15600／6600／6000                                                                     |
| Provenance 保存位置      | C manifest 各正例 `expect` 區塊（值＋cardinality=1）、`tools/tests/test_bravo_dvds.py` 的 `AGENT_A_VERIFIED` |
| 未來啟用前提             | Controller 核准「整片 DVD ＝ 單一 Scene」模型 ＋ Stash 型別轉換能力（比照 Clips DEF-01 defer 的還原規格）    |

Studio 同理：來源 Label（レーベル）值僅存於 C manifest `expect`（GAYSIAN／Lucifer／ooooPS!! 等），
無已發布的 Controller Label→Studio 決策，故不映射。

BRAVO.test.yaml：重新列入 G1 驗收的三個 DVD URL（234/084/046），Clips 三 URL 不變。

## 5. F-03 產品有效性與 fail-closed 誠實分類

身份契約（測試層）：品番 marker 存在 ＋ Title 非空 ＋ Code 非空（字串、保留前導零）＋
canonical 與請求 URL 一致。此 gate 已在離線 harness 實作並通過：
Agent B `TestRouteVersusProductValidity`（含 canonical-alone-insufficient 反例）與
Agent C manifest 的 404 cases（Title/Code/Details/Image mappedExpect 皆為 `[]` 且全綠）。

selector 層的天然 fail-closed 範圍：Title/Code/Details/Image 皆錨定品番或產品節點，
404 頁（00/999999，無品番 h2）抽不到這些欄位——已由 C synthetic 404 fixtures 實證。

**殘餘風險（不得粉飾）：`BLOCKED_UNSAFE_PARTIAL_METADATA`**
Stash 的 XPath 欄位彼此獨立填充。404 頁仍有 canonical，`URLs` 欄位在 404 頁會被填入
該 404 URL（最小重現：B 的 `test_404_routes_by_shape_but_is_not_a_product` 斷言
404 model 上 `URLs == [url]` 而 validity gate 拒絕之；C 的 404 expect 亦記錄 canonical 存在）。
YAML 層沒有跨欄位 guard 能抑制這個部分結果，因此**不能宣稱 Stash runtime 已 fail-closed**。
緩解現況：(1) 錯誤路由（QF）已移除，消除跨模式假 metadata 的主要來源；
(2) Title/Code 錨定使「看似完整的假產品」無法成立，只剩孤立的 URLs；
(3) 是否接受此殘餘風險、或需在消費層（如 metadata feed payload 檢查）加 gate，
屬 Controller／Gate B 裁定事項。本分類同時寫入 BRAVO.yml 檔頭註解與 handoff。

其他已知限制：

- 路由比對為 Stash `strings.Contains` 全字串子字串比對：lookalike host
  （`notbravo-japan.com`）、query 內嵌完整外來家族 URL 可碰撞，由宣告順序決定。
  B 的 3 個 `KNOWN_UPSTREAM_LIMITATION` strict xfail 即此證據；YAML 層無法修復，非 release blocker 的定性待 Controller。
- Date 的 parseDate 前置 JS 對「空值」的 Stash 誤差路徑未驗證（已驗證頁面 9/9 皆符合日文格式，
  此為假設性邊界）；Gate B 應涵蓋。
- 084 soldout 拒絕是「檔名含 soldout」層級的 guard，依據 A 記錄的檔名
  （`BR-084soldout.jpg`）與 C synthetic fixture；live 084 的實際 src 形式須由 Gate B 確認。

## 6. B／C 整合與衝突解決

整合原則：選擇性匯入，不整分支 merge；不重複匯入 PR #93 已合併的修正。

Agent B（`test_bravo_dvd_routes.py`）：

- 退役 5 處 `EXPECTED_RED`（DVD route 數量、route 總數、dvdSceneScraper 存在、
  DVD URL handler 選擇、QF 已移除）——其等待的實作已落地，strict xfail 若保留將以 XPASS 形式失敗。
- `candidate_config()` 改為冪等：production 已有 DVD route 時不再重複附加 sketch route 與 stub handler。
- 舊契約測試（`TestQueryFragmentContract`）於 QF 缺席時依原設計 skip（2 skipped 的來源）。
- 保留：`KNOWN_UPSTREAM_LIMITATION` 3 個 strict xfail、QF 假 metadata 歷史重現測試、
  404 validity 測試、Clips 回歸契約（含 Duration 未映射斷言；未恢復任何舊 Duration 斷言）。

Agent C（DVD manifest v2.3 ＋ 11 個 fixture 檔 ＋ `test_bravo_dvds.py`，24 個 DVD fixture tests 全數保留）：

- PR #99 原本因缺 `dvdSceneScraper` 而紅的 manifest，實作後轉綠：`10 cases verified`（§7）。
- F 整合適配 3 處（皆為 C 分支基線前提被 G0 合併改變，非弱化期望；每處均在檔內註明）：
  1. mutation harness 的 `Duration` mappedExpect（引用 PR #93 已移除的 Clips 欄位）
     → 同 index 改為 `URLs`（harness 自身 canonical）。mutation 的 index 語意（[0]Title／[1]Code／[4]Image）不變。
  2. mutation harness 的 `Details` 期望（依賴 PR #93 DEF-02 已取代的舊 selector）
     → 同 index 改為 `Tags.Name`（harness 頁面帶 keywords meta）。
  3. cross-family routeThrough mutation 原以 `/dvds/` URL 為「不匹配 URL」；
     DVD route 合法化後前提消失 → 改以 foreign-host canonical 觸發同一條 routeThrough 拒絕。
- 未改動 C 的任何 DVD manifest 期望值（mappedExpect／expect／policy 皆原樣）。

F 側連帶修正 2 處：

- 雙路由使 Clips manifest 的 mappedExpect 觸發 runner 的「Ambiguous entrypoint」，
  比照 C 的作法為 59 個 entry 補上 `scraper: clipSceneScraper`（不改任何期望值），
  Clips manifest 恢復 `11 cases verified`。
- BRAVO.yml 註解一度含 `sceneByQueryFragment:` 字面觸發通用文字掃描測試
  （`test_scrapers.py`），已改寫註解措辭；全域測試轉綠。

**沒有任何 test 或 fixture 被 disable 以求綠。**

## 7. Gate A 結果（離線，於受測候選 HEAD 84f7a2c 執行）

環境：Python venv（pytest 8.x／pyyaml／jsonschema）、Node 24、`npm ci` exit 0。
注意：並行執行會使 fixture runner 的 JS vm 250ms timeout 誤報失敗；下列結果皆為串行重跑的最終值。

| 指令                                                 | Exit | 結果                                                                                                        |
| ---------------------------------------------------- | ---- | ----------------------------------------------------------------------------------------------------------- |
| `node validator/index.mjs -a --ci`                   | 0    | Validation passed                                                                                           |
| `npm run validate-sort`                              | 0    | Validation passed（URL 陣列排序含新 DVD route）                                                             |
| `bash tools/validate-all.sh`                         | 0    | 24/24 PASS，含 `[PASS] scrapers/BRAVO.yml`                                                                  |
| `python -m pytest tools/tests/ -v`（以 -q 取得計數） | 0    | **417 passed, 2 skipped, 3 xfailed**                                                                        |
| `python tools/run_fixture_manifests.py`              | 0    | 20 manifests 全 PASS；BRAVO：clips 11 cases、dvds 10 cases、historical 3 cases                              |
| `python tools/check_evidence_contract.py`            | 0    | 17 records, 0 failures                                                                                      |
| `python tools/check_docs_index.py`                   | 0    | 51 documents OK（本報告依 B 報告先例置於 repo 根目錄，未觸發 index 要求）                                   |
| `python tools/check_scraper_semantics.py`            | 0    | passed（含新 parseDate 格式檢查）                                                                           |
| `python tools/scan_session_material.py`              | 0    | 369 tracked files passed                                                                                    |
| `npm run format:check`                               | 1    | **基線同樣失敗**：main 原生 tree 亦為 exit 1（24 檔既有格式問題）；本次變更檔案無一在警告清單內，非本次引入 |

補充（repo AGENTS.md 典範指令）：`parse_committed_yaml.py`（24 檔，exit 0）、fixture-runner `--self-test`（exit 0）、`check_evidence_labels.py`（exit 0）、`check_scraper_docs.py`（exit 0）、`check_docs_official.py`（exit 0）、`scraper-quality-gate.sh scrapers/BRAVO.yml`（exit 0）。

補充實證（非 repo 既有指令，F 自備）：以 fixture runner 相同的 vm 執行方式，
對實際 YAML 的 Date／Image／Title／Code postProcess 跑 A 已驗證值 9 例，全 PASS
（Date：`2018年8月29日`→`2018-08-29`、`2010年09月30日`→`2010-09-30`、亂值→空；
Image：真圖保留、soldout→空；Code `046` 前導零保留）。

Gate A 結論：**PASS（附 format:check 基線既有失敗之註記）**。離線 PASS 不代表 Gate B。

## 8. Scraper Source 套件 Provenance

- 指令：`python tools/build_scraper_source.py --output <dir>`（exit 0，22 個公開套件）
  與同目錄 `--verify-only`（exit 0，`Stash source integrity OK`）。
- BRAVO.zip SHA-256：`815f49928a9ee4d4445983c810c664ecffca5f7cd3adb2d992f09dd69e7bd283`；index.yml 記錄 version `eaec398`（feat commit）。
- `scrapers/BRAVO.yml` SHA-256：`33f324b541fdacc59c8d7b4403aef0c4997f68683c56ac58784958c7540814be`。
- GitHub Actions／CodeQL：**NOT_RUN**（本任務不推送；待主代理推送後須於 exact HEAD 查核，不得以本地結果代替）。

## 9. 迴歸矩陣對應

| ID                     | 結果（離線）                            | 證據                                                                                                              |
| ---------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| CLIP-284／282／283     | PASS                                    | Clips manifest 11 cases verified；B production routing tests                                                      |
| CLIP-DURATION          | PASS（absent）                          | `test_bravo_clips` omission 斷言 ＋ B `test_production_duration_is_not_mapped`；manifest 無 Duration mappedExpect |
| DVD-234／084／046／281 | PASS                                    | DVD manifest 正例（另含 377／384）；084 Code `084`、Details `[""]`                                                |
| DVD-00／999999         | PASS（測試層 not accepted）             | C 404 cases mappedExpect 全空 ＋ B validity gate 拒絕；runtime 分類見 §5                                          |
| DVD-DURATION／STUDIO   | PASS（absent）                          | 結構測試 `test_dvd_scraper_production_policy` ＋ C policy test                                                    |
| DVD-TAGS               | PASS（not mapped）                      | 同上（dvd 無 Tags 鍵）＋ C `test_site_generic_keywords_are_not_product_tags`                                      |
| QF-234／084／284       | 設定層 PASS（無 handler）；live NOT_RUN | QF 移除斷言（clips tests ＋ B readiness）；panic 與否待 Gate B，不得離線宣稱                                      |
| FRAGMENT               | PASS（unsupported 設定層）              | `sceneByFragment` 缺席斷言（兩套測試）                                                                            |
| URL-COLLISION          | 已知限制（非 PASS）                     | B collision 測試記錄 runtime 實際行為 ＋ 3 strict xfail                                                           |
| SOURCE-INTEGRITY       | PASS                                    | 歷史 manifest SHA-256 前後一致（§2）                                                                              |

BRAVO 三套測試合計：113 passed、2 skipped（QF 舊契約測試於移除後依設計 skip）、3 xfailed（上游限制）。

## 10. Gate B／Gate C 與下一步

- Gate B：`NOT_RUN`。F 不自我認證。獨立 QA 需先取得：Controller 授權、M0 preflight、
  stash-test 專屬 lease、安裝包 SHA 核對（`815f4992…`，推送後重算）、Stash 版本、
  回滾程序、無未控管的持久 Scene 寫入。驗證範圍至少：Clips 284/282/283、DVD 234/084/046、
  DVD 00/999999、QF 234/084/284（判定 clean unsupported vs panic #97）、084 圖像政策、
  Date 實值、Duration/Studio 缺席、環境復原，並保存實際 GraphQL 回應。
- Gate C：`NOT_RUN`（待 Gate B PASS 後由 Controller 審查；合併觸發公開 scraper source
  發布，須另行授權）。
- 回滾計畫：本分支未合併前，main 不受影響；合併後回滾 = revert 本分支三個 commit
  並重新發布 scraper source；BRAVO.yml 單檔 revert 即可恢復 Clips-only 行為
  （QF 恢復與否依 WS-2E-QF-001 決策，不得逕行恢復）。

## 11. 變更檔案清單（相對 main，共 20 檔）

實作：`scrapers/BRAVO.yml`、`scrapers/BRAVO.test.yaml`、
`tools/tests/test_bravo_clips.py`（更新）、`tests/fixtures/bravo/bravo-clips-fixtures.yml`（加 scraper 命名）。
整合：`tools/tests/test_bravo_dvd_routes.py`（B）、`tools/tests/test_bravo_dvds.py`（C＋F 適配）、
`tests/fixtures/bravo/bravo-dvds-fixtures.yml`（C）、
`tests/fixtures/bravo/dvd-synthetic-*.html`（10，C）、`tests/fixtures/bravo/dvd-mutation-harness.html`（C）。
文件：本報告 ＋ `WAVE2E-F-DVD-INTEGRATION-HANDOFF.yaml`。
未動：歷史 manifest、Clips fixture HTML、任何其他 scraper、Stash 實例。

## 12. 交付紀錄（主代理推送後補記）

- 推送：單一 snapshot commit `71cd3773a119ae29df2afe5e51e92a60ce3bc633`
  （parent = main `ff236c9`），遠端 tree `23e680d4…` 與本地已驗證 tree 逐一相同。
- Draft PR：[#103](https://github.com/daniel-yfc/stash-scarpers/pull/103)（Draft，未合併）。
- Exact-head CI/CodeQL：connector 無 checks 讀取工具，記為 NOT_VERIFIED（以 PR 頁面為準），
  不以離線 Gate A 結果替代。
- 本節與 handoff 的 PR 欄位更新為 docs-only 後續 commit，不含程式變更；受測候選
  HEAD 維持 `84f7a2c`。
