# Wave 2E Agent B — Routing Safety Report

- Assignment: `WAVE2E-B-ROUTING-20261102` / Workstream: `WS-2E-20`
- Role: Agent B（Routing / Test Engineering）
- 交付物：`tools/tests/test_bravo_dvd_routes.py`（新檔）+ 本報告
- 結論先行：路由測試套件已建立並可執行；QueryFragment 跨模式誤擷取風險經離線證據確認存在，標記 `RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA`，`HANDOFF_STATUS=CHANGES_REQUESTED`。本結論不是對 production YAML 的修改要求由 B 執行，而是要求 Controller 在 Agent F 整合前先做決策（見 §7）。

## 1. Baseline

| 項目 | 已核對值 |
|---|---|
| Repository | `daniel-yfc/stash-scarpers` |
| `main` HEAD | `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`（Merge PR #90） |
| 本任務 BASE_SHA | `86e34a24642dad2e64ae984e7e9182605e98cbcf`（PR #93 `fix/e2e-bravo-clips` HEAD；以 `refs/pull/93/head` 與遠端 branch 雙重核對一致） |
| PR #93 狀態 | 未合併（`main` 上不存在 `tools/tests/test_bravo_clips.py`，亦無 `clipSceneScraper`）。本 branch 即以 PR #93 HEAD 為基底，未假設其已合併 |
| PR #98 / 規劃文件 | HEAD `0c97068c1822fe7db8f069bb0466b921761630cc`，含 `docs/61-bravo-dvd-wave-2e.md`（`PLANNED / NOT_IMPLEMENTED`） |
| 本 branch | `test/e2e-bravo-dvd-routing`（自 PR #93 HEAD 建立） |
| `scrapers/BRAVO.yml`（PR #93 版） | SHA-256 `5eb954050bf37e017eb2fee2114ce80265d067de17fdc705c3dca53daa35a11b`；現況：`sceneByURL` 恰 1 條（→ `clipSceneScraper`）、`sceneByQueryFragment` → `clipSceneScraper`、`sceneByFragment` 不存在、無 `dvdSceneScraper` |
| `scrapers/BRAVO.test.yaml`（PR #93 版） | 僅 clips/284、282、283；7 條 dvds URL 已於 Wave 1B 移除，保留給 Wave 2E |
| 歷史 fixture manifest | `tests/fixtures/bravo/bravo-fixtures.yml` SHA-256 = `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`（與 archived evidence 一致，未變動） |
| 目標 Stash build | `v0.31.1-182-g9e9ad972` = upstream commit `9e9ad972643320e737c711884f10e4285f0f3a88`（stash-test 實測版本，見 M0 / panic repro 報告）；本報告所有 runtime 語義均以此 commit 原始碼核對 |

## 2. Actual Stash Routing Semantics（B-01）

原始碼位置（upstream `stashapp/stash` @ `9e9ad972`）：

1. **URL matching**：`pkg/scraper/definition.go:163` `ByURLDefinition.matchesURL` — 對該 route 的每個 pattern 執行 Go `strings.Contains(url, pattern)`，任一命中即 true。不是 hostname/path 驗證、不是 regex、大小寫敏感。
2. **單一 YAML 內路由選擇**：`pkg/scraper/defined_scraper.go:108` `viaURL` — 依 `sceneByURL` **宣告順序**逐條檢查，第一個 `matchesURL` 為 true 的 route 先執行。細節：若該次 scrape 回傳 nil 且無 error，`viaURL` 會繼續嘗試下一個匹配 route；回傳非 nil 結果時（常態）即由第一匹配決定。因此「第一匹配優先」是常態契約，「nil 才落到下一條」是邊界行為。
3. **全域 scraper 選擇**：`pkg/scraper/cache.go:312` `Cache.ScrapeURL` — 依 scraper cache 載入順序，選第一個 `supportsURL(url, ty)` 為 true 的 **scraper 檔案**；與單一檔案內的 route 選擇是不同層次。全部不匹配時回傳 `(nil, nil)`（其後續空結果處理即 issue #97 的 upstream panic，屬 WS-D，不是路由行為，本報告不將其列為路由 PASS/FAIL）。
4. **QueryFragment 入口**：`pkg/scraper/definition.go:41` `SceneByQueryFragment` 型別為單一 `*ByFragmentDefinition`（非陣列）；`pkg/scraper/defined_scraper.go:46` `viaFragment` 對 Scene input 直接取用該單一定義的 scraper 執行，**不經過 `viaURL` 重選**（見 §7）。

由此導出的關鍵性質（皆已寫入測試並通過）：

- pattern 是「host + path 前綴」的**連續子字串**。嵌入另一 family 時，必須連 host 一起嵌入才會碰撞；query 中的裸 `/clips/284` 不命中任何 pattern。
- 前綴型相似 host（`notbravo-japan.com`）會命中；後綴型（`bravo-japan.com.evil.example`）因 `.evil.example` 打斷連續 pattern 而**不**命中。此點修正了任務初期「所有相似 host 皆誤匹配」的假設——誤匹配面是真實的，但形狀由連續子字串決定，測試矩陣已按實測形狀撰寫。

## 3. Positive Routing Matrix（B-02，synthetic candidate configuration）

候選雙路由 config 由測試在記憶體中以 production YAML 深拷貝 + `docs/61` 設計草圖的 DVD route 構成；不寫入任何檔案。

| Test | URL | Expected | Observed（model） | 結果 |
|---|---|---|---|---|
| B-P01 | `https://www.bravo-japan.com/clips/284` | `clipSceneScraper` | `clipSceneScraper` | PASS |
| B-P02 | `https://www.bravo-japan.com/clips/282` | `clipSceneScraper` | `clipSceneScraper` | PASS |
| B-P03 | `https://www.bravo-japan.com/dvds/234` | `dvdSceneScraper` | `dvdSceneScraper` | PASS |
| B-P04 | `https://www.bravo-japan.com/dvds/084` | `dvdSceneScraper` | `dvdSceneScraper` | PASS |
| B-P05 | `https://www.bravo-japan.com/dvds/046` | `dvdSceneScraper` | `dvdSceneScraper` | PASS |
| B-P06 | www / non-www × clips / dvds 共 4 型 | 對應 family handler | 全部正確；注意 non-www pattern 本身即為 www URL 的子字串，www 型態會同時命中同 route 內兩個 pattern，但 handler 不歧義 | PASS |

另驗證：5 條正例 URL 各自僅命中恰好一條 route。

**Production 現況（分開回報）**：同一批 DVD 正例對 production YAML 執行時 handler 為 `None`（無 DVD route）——已以 `EXPECTED_RED`（xfail, strict）標記 6 項 production-contract assertions（DVD route 恰一條、總 route 數 = 2、`dvdSceneScraper` 存在、3 條 DVD URL 選路）。Agent F 整合後必須移除標記；strict xfail 會在整合完成而未移除標記時以 XPASS 形式讓套件失敗，避免標記殘留。

## 4. Negative Routing Matrix（B-03）

分類：`EXPECTED_SAFE` / `OBSERVED_RUNTIME_MATCH` / `UNSAFE_MATCH` / `KNOWN_UPSTREAM_LIMITATION`。所有列均為 runtime model 實測結果（通過的「實測行為」測試），不是期望值。

| # | URL 形狀 | Observed handler | 分類 | 說明 |
|---|---|---|---|---|
| N01 | `https://example.com/clips/284`、`/dvds/234` | 無 | EXPECTED_SAFE | pattern 字串完全不出現 |
| N02 | `https://www.bravo-japan.com/dvds`（無尾斜線）、`/clips` | 無 | EXPECTED_SAFE | pattern 以 `/dvds/` 結尾，裸路徑不含 |
| N03 | `https://www.bravo-japan.com/dvds/`（無作品 ID） | `dvdSceneScraper` | OBSERVED_RUNTIME_MATCH | 路由層命中；無 ID 可抓是 scrape 層問題，路由測試不宣稱其安全 |
| N04 | `https://www.bravo-japan.com/CLIPS/284`（大寫） | 無 | OBSERVED_RUNTIME_MATCH | `strings.Contains` 大小寫敏感 |
| N05 | `https://bravo-japan.com.evil.example/clips/284` | 無 | EXPECTED_SAFE | 連續 pattern 被 `.evil.example` 打斷（修正初期假設，見 §2） |
| N06 | `https://notbravo-japan.com/clips/284` | `clipSceneScraper` | UNSAFE_MATCH / KNOWN_UPSTREAM_LIMITATION | 前綴附加仍是 pattern 的 superstring |
| N07 | `https://evil.example/bravo-japan.com/clips/284` | `clipSceneScraper` | UNSAFE_MATCH / KNOWN_UPSTREAM_LIMITATION | pattern 出現在他站 path |
| N08 | `https://example.com/?u=bravo-japan.com/dvds/234` | `dvdSceneScraper` | UNSAFE_MATCH / KNOWN_UPSTREAM_LIMITATION | pattern 出現在他站 query |
| N09 | clips URL + `?next=/dvds/234`（裸路徑） | `clipSceneScraper`（僅一條命中） | EXPECTED_SAFE | 裸路徑不含 host，不碰撞 |
| N10 | DVD URL + `?ref=/clips/284`、`#/clips/284` | `dvdSceneScraper`（僅一條命中） | EXPECTED_SAFE | 同上 |
| N11 | clips URL + `?next=` + 完整 DVD URL | `clipSceneScraper`（兩條命中，宣告在先者勝） | OBSERVED_RUNTIME_MATCH | 結果恰為 path 本 family，但碰撞存在 |
| N12 | DVD URL + `?ref=` + 完整 clips URL；DVD URL + `#` + 完整 clips URL | `clipSceneScraper`（兩條命中） | UNSAFE_MATCH | **query/fragment 劫持**：DVD URL 被導向 Clips handler，純粹由宣告順序決定 |
| N13 | `https://www.bravo-japan.com/clips/284/dvds/234`（雙 family path） | `clipSceneScraper`（僅一條命中） | OBSERVED_RUNTIME_MATCH | 後段 `/dvds/234` 前無 host，不命中 DVD pattern；與順序無關 |

安全期望（safe router 應有的行為）另以 3 項 `KNOWN_UPSTREAM_LIMITATION`（xfail, strict）測試保存：N06、N08 應為無 handler、N12 應為 `dvdSceneScraper`——三項在目前 runtime 語義下皆不成立。**未修改 matcher model 來讓它們通過**；它們是給 Controller 的可重現失敗證據：YAML pattern 無法提供 host-boundary 保證，此限制只能由 upstream matcher 改變或由 Controller 明示接受。

## 5. Route Priority Findings

1. 選擇是**宣告順序制**，不是 specificity 制：反轉候選 config 的 route 順序後，N11/N12 類碰撞結果全部翻轉（已寫入 `TestRouteOrderDependence` 並通過）；乾淨 URL（單一命中）不受順序影響。
2. 因此 Agent F 整合時 route 順序本身即是契約的一部分：Clips 在先意味著「雙命中時 Clips 勝」。若 Controller 希望 DVD 優先，必須明示改序並重跑本套件——不得預設任一順序為顯然正確。
3. 邊界行為：第一匹配的 scrape 若回傳 nil（無 error），`viaURL` 會落到下一個匹配 route。此行為可能掩蓋「第一 handler 擷取為空」的失敗，使結果來源 handler 與預期不同；Gate B 實機驗證時應記錄實際回傳內容，而非僅記錄「有回傳」。
4. 全域層（哪個 scraper 檔案先被選）與檔案內層（哪條 route）必須分開驗證：BRAVO 檔案內部正確，不保證全域沒有其他 scraper 先以子字串命中同一 URL；此屬 Gate B inventory 檢查範圍，本任務未實機執行。

## 6. Fixture Runner Limitations（B-05）

對象：`tools/verify-scraper-mappings.mjs`（BASE_SHA 版本）。

1. **是否驗證第一個匹配的 handler？否。** `getField`（第 12–15 行）：assertion 指定 `scraper` 時以 `routes.find(c => c.scraper === assertion.scraper)` 按名稱直選該 route 的欄位定義，完全不檢查 URL、不檢查順序、不檢查是否有其他 route 先命中。未指定且 route 數 > 1 時直接 fail（`Ambiguous entrypoint; specify scraper`）——即多路由下工具**強制**使用者繞過路由選擇。
2. **是否只確認 URL 匹配任一 pattern？是，且語義還與 runtime 不同。** `routeThrough`（第 108–125 行）：將所有 route 的 pattern 攤平（`flatMap`）後，只要抽出的欄位值（實務上是 canonical URL）對任一 pattern `startsWith` 即通過。它檢查的是「輸出值」而非「輸入 URL 的實際選路」，比對方式是 `startsWith(host + pathname + search)`（pattern 先剝除 scheme），與 runtime 的 `strings.Contains(whole URL, pattern)` 語義不同：query 劫持、path 中段嵌入等 runtime 會命中的形狀，`routeThrough` 不會命中；反之亦然。兩者不可互相替代。
3. **是否可能指定 `dvdSceneScraper` 後略過真實路由問題？是。** DVD `mappedExpect` 若寫 `scraper: dvdSceneScraper`，即使 production 的 DVD route pattern 寫錯、順序錯誤、或根本不存在對應 route（只要同名 xPathScraper 存在且欄位對），欄位斷言仍會通過。這正是 `docs/61` §5 WS-2E-20 已記錄的已知限制，本次以原始碼行號獨立複核一致。
4. **是否需要獨立 route-selection tests？是**——即本任務交付的 `test_bravo_dvd_routes.py`。不建議大幅重構共用 fixture runner：其欄位對照功能本身正確，缺的是選路層；以專用測試補上選路層，風險與影響面最小。若未來要改 runner，屬共用工具變更，需另行設計決策與批准（本任務未修改它）。

本次實跑：`node tools/verify-scraper-fixtures.mjs tests/fixtures/bravo/bravo-clips-fixtures.yml tests/fixtures/bravo/bravo-fixtures.yml` → clips 6 cases、historical 3 cases 均 verified（僅證明欄位層與既有契約未壞，不證明選路）。

## 7. QueryFragment Risk Assessment（B-06）— 決策紀錄

**決策：`FALSE_METADATA_RISK_CONFIRMED`（離線證據層級）**
**標記：`RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA`**
**未決部分：目前 live（改版後）DVD DOM 上的實際擷取範圍 — `BLOCKED_NEEDS_LIVE_QA`（需授權 + 獨占租約的 Gate B NEG-03 案例；本任務未進入 stash-test）**

逐問回答：

1. **Stash 是否直接執行 `clipSceneScraper`？是。** `viaFragment`（`defined_scraper.go:46-63`）對 Scene input 直接使用 `SceneByQueryFragment` 單一定義，其 `scraper: clipSceneScraper`、`queryURL: "{url}"`；`{url}` 由 scene 的 URL 代入後載入該頁，執行 Clips XPath set。
2. **是否會重新選取 `sceneByURL` 的 DVD handler？不會。** Fragment 路徑中不存在任何 `viaURL` / `matchesURL` 呼叫；新增 DVD `sceneByURL` route 對 QueryFragment 行為零影響。schema 層亦無第二個 QueryFragment 槽位（單一 `*ByFragmentDefinition`），「再加一個 DVD QueryFragment handler」不是合法的 YAML 選項，本任務未實作、亦不建議嘗試。
3. **是否可能由 Clips XPath 擷取 DVD DOM？是，已離線重現。** 以 production `clipSceneScraper` 的原始 selector 對四份歷史 DVD DOM fixture（`dvd-046/281/173/215.html`，真實頁面擷取）執行，結果一致：

   | 欄位 | 四份 DVD fixture 結果 |
   |---|---|
   | Title / Code / Duration / Details / Image | 全部為空 |
   | URLs | 各頁自身 canonical（`https://www.bravo-japan.com/dvds/046` 等）——外觀正確 |
   | Tags | 非空，且**四份不同作品回傳完全相同的關鍵字清單** |

4. **是否可能產生部分正確、核心欄位錯誤的 metadata？是，且形狀比「全錯」更危險。** 結果不是乾淨的失敗：它帶有正確外觀的 canonical URL 與一組看似合理的 Tags，但核心欄位（Title/Code）為空，而 Tags 經四頁比對證明是站台/分類層級的共用關鍵字、非作品專屬——將其套用到 DVD scene 即是把錯誤的 Tags 寫入資料庫，且 URL 正確會讓結果更難被人工察覺。此即「看似合理但錯誤」的跨模式擷取，離線層級確認成立。
5. **安全且符合官方 schema 的可行修正方向？YAML 層不存在 per-URL 分派的合法手段。** 最小可行選項（皆需 Controller 決策，B 不自行變更正式 scraper）：
   - (a) **明示重新界定範圍**：決議 QueryFragment 僅支援 Clips，DVD URL 不得經 Fragment 入口使用，並在文件與 Gate B NEG-03 留下實機證據與已知限制聲明。成本最低，但 runtime 無法強制，使用者誤用風險仍在。
   - (b) **移除 `sceneByQueryFragment`**：徹底消除跨模式擷取，但同時廢除 Wave 1B 已驗收的 Clips QueryFragment 契約，並與 repo 既有政策（`"{url}"` 保留）衝突；影響面最大，需 Controller 明示推翻先前決策。
   - (c) **接受風險並以 Gate B 實機證據界定範圍**：先取得 live 改版後 DVD DOM 的實際 QF 擷取結果（可能與歷史 DOM 不同），再於 (a)/(b) 間決策。在取得該證據前不得宣稱安全。
   - 建議路徑：(c) → (a)；若 live 證據顯示改版後 DOM 會擷出非空 Title/Code（即錯值而非空值），升級為 (b) 或要求 upstream 支援多 handler 前不得發布 Wave 2E。

## 8. Clips Regression Contract（B-07）

Wave 2E 整合後以下必須全數維持（本套件 `TestClipsRegressionContract` + 既有 `test_bravo_clips.py` 雙重覆蓋，BASE_SHA 下全部通過）：

- clips/284、clips/282 路由至 `clipSceneScraper`（含 www/non-www）。
- `clipSceneScraper` XPath 契約不變：Title `//h1[1]`、Code 含 `Clip` 標籤相鄰、Duration 含 `作品TIME` 標籤相鄰、四個核心 selector 均不含 `品番`、無 Date/Studio 欄位。
- Clips Title / Code / URLs / Duration 的 fixture 期望值（`bravo-clips-fixtures.yml`：284、282、missing-title、no-cover、extra-headings 共 5 個 completed + 1 failure）不變。
- Image 維持 poster-only（`//video/@poster`，無 `<img>` fallback）。
- 缺 Title 案例行為不變（Title 為空、其餘頁面衍生值仍在——已知限制，不因 DVD 工作而改變宣稱）。
- `sceneByFragment` 不得重新引入。
- 歷史 fixture evidence contract：`bravo-fixtures.yml` 位元組不變，SHA-256 維持 `be1885d2…39b2`。

## 9. Proposed Test Changes for Agent F（B-04）

`tools/tests/test_bravo_clips.py` 由 Agent F 於整合階段修改，B 不直接動它。現行 `test_clips_route_uses_clip_scraper_only` 中的 `assert len(routes) == 1` 必須以「恰好兩 family 的完整路由契約」取代，不得刪除斷言了事。建議完整替換如下（其餘測試函式原封不動，含歷史 digest 與 poster-only 測試）：

```python
def test_dual_route_contract():
    data = load()
    routes = data["sceneByURL"]
    assert len(routes) == 2
    by_scraper = {route["scraper"]: route for route in routes}
    assert set(by_scraper) == {"clipSceneScraper", "dvdSceneScraper"}

    clips = by_scraper["clipSceneScraper"]["url"]
    assert clips == sorted(clips)
    assert all("/clips/" in p for p in clips)
    assert not any("/dvds/" in p for p in clips)

    dvds = by_scraper["dvdSceneScraper"]["url"]
    assert dvds == sorted(dvds)
    assert all("/dvds/" in p for p in dvds)
    assert not any("/clips/" in p for p in dvds)

    assert "clipSceneScraper" in data["xPathScrapers"]
    assert "dvdSceneScraper" in data["xPathScrapers"]


def test_no_direct_scene_by_fragment():
    data = load()
    assert "sceneByFragment" not in data
```

同時 F 必須：

- 移除 `test_bravo_dvd_routes.py` 中 6 項 `EXPECTED_RED` 標記（strict xfail 未移除會以 XPASS 失敗，屬預期提醒機制，不是測試壞掉）。
- 保留 3 項 `KNOWN_UPSTREAM_LIMITATION` 標記原樣（它們描述 upstream matcher，不隨 YAML 整合而改變）。
- QueryFragment 測試（`test_query_fragment_preserves_url`）在 Controller 對 §7 做出決策前原樣保留；若決策為 (b) 移除 QF，F 須同步改寫該測試並在 PR 說明中引用決策紀錄。
- 整合後重跑：`python -m pytest tools/tests/ -v`、`node tools/verify-scraper-fixtures.mjs tests/fixtures/bravo/bravo-clips-fixtures.yml tests/fixtures/bravo/bravo-fixtures.yml`、官方 validator 與 `npm run validate-sort`（route pattern 陣列排序由 repo 規則與上述斷言雙重把關）。

## 10. Integration Recommendations

1. **整合順序**：先有 Controller 對 §7 QueryFragment 的決策，再整合 YAML；路由本身（§3/§4）不阻塞 F 的 YAML 撰寫，但 Wave 2E 不得在 QF 決策未定時宣稱可發布。
2. **route 順序即契約**：F 在 YAML 註解中記錄所選宣告順序與其碰撞含義（雙命中時誰勝），並讓本套件的 order-dependence 測試對該順序保持綠燈。
3. **DVD fixture 的 `mappedExpect`**：依 §6，指定 `scraper: dvdSceneScraper` 只能證明欄位層；每個 DVD case 必須同時被本套件的 production 選路斷言覆蓋，兩層缺一不可。
4. **Gate B 必測案例**（獨立 QA、需租約）：DVD URL 正例（234/084）、Clips 回歸（284/282）、QF-DVD 負例（NEG-03，驗證 §7 的 live 範圍）、N12 劫持 URL 的實機行為（確認 model 與 runtime 一致）、無匹配 URL 的行為僅記錄並歸 WS-D（issue #97），不作為 Wave 2E 路由 PASS/FAIL。
5. **不得放寬既有 Clips 防護**：poster-only、無 `sceneByFragment`、歷史 digest 三條紅線不因 DVD 整合而調整；若 DVD Image 證據不足，DVD 側比照 Clips 原則 fail-closed（留空），不引入廣域 `<img>` selector。

## Test Results（本 branch，執行於 BASE_SHA + 本任務新增檔案）

| 指令 | 結果 |
|---|---|
| `python -m pytest tools/tests/test_bravo_dvd_routes.py tools/tests/test_bravo_clips.py -q -rxX` | 58 passed, 9 xfailed（3 × KNOWN_UPSTREAM_LIMITATION + 6 × EXPECTED_RED） |
| `python -m pytest tools/tests/ -q`（先行 `npm ci` 後） | 362 passed, 9 xfailed，0 failed |
| `node tools/verify-scraper-fixtures.mjs tests/fixtures/bravo/bravo-clips-fixtures.yml tests/fixtures/bravo/bravo-fixtures.yml` | clips 6 cases verified；historical 3 cases verified |
| 未修改檔案核對 | `git status`：僅新增 `tools/tests/test_bravo_dvd_routes.py` 與本報告；`scrapers/BRAVO.yml`、`tools/tests/test_bravo_clips.py`、所有 fixtures 位元組未變（digest 見 §1） |

備註：未執行 `npm ci` 的乾淨環境下，全套件有 8 項失敗（validator / scrutiny / fixture self-test 需 node 相依），已以 `git stash` 在無本任務檔案的 BASE_SHA 上複現相同 8 項，屬環境相依、非本任務回歸；`npm ci` 後全數消失。
