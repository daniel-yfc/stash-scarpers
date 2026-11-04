# Wave 2E Agent B — Routing Safety Report

- Assignment: `WAVE2E-B-ROUTING-20261102` / Workstream: `WS-2E-20`
- Role: Agent B（Routing / Test Engineering）
- 交付物：`tools/tests/test_bravo_dvd_routes.py`（新檔）+ 本報告
- 結論先行：路由測試套件已建立並可執行；QueryFragment 跨模式誤擷取風險經離線證據確認存在，標記 `RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA`，`HANDOFF_STATUS=CHANGES_REQUESTED`。本結論不是對 production YAML 的修改要求由 B 執行，而是要求 Controller 在 Agent F 整合前先做決策（見 §7）。
- **Addendum 回應（`docs/63-wave2e-agent-b-assignment-addendum.md`，PR #98 @ `989e05e`）：見 §11（2026-11-03 補充）。**
- **Readiness 更新（Assignment `WAVE2E-B-ROUTING-QF-READINESS-20261104`，Reference HEAD `16bf5a1`）：見 §12（2026-11-04 補充）——狀態 `ROUTING_AND_QF_TEST_HANDOFF_READY`。**

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
- Clips Title / Code / URLs / Duration 的 fixture 期望值（`bravo-clips-fixtures.yml`：284、282、missing-title、no-cover、extra-headings 共 5 個 completed + 1 failure）不變。**（2026-11-04 更正：Duration 部分已被 PR #93 自身的暫緩政策 supersede——production mappedExpect.Duration 已由 PR #93 移除、改以來源層獨立保存；見 §13。本行其餘欄位不變。）**
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

## 11. Addendum 回應 — B-08 / B-09 / B-10（docs/63，2026-11-03 補充）

依據文件：`docs/63-wave2e-agent-b-assignment-addendum.md`（PR #98 HEAD `989e05e1256e321705b1ebfe7a9642c9a8c1f6c8` 已核對）。本節補充（不取代）§1–§10；權限邊界不變：不改 `scrapers/BRAVO.yml`、不改 `test_bravo_clips.py`、不操作 stash-test。

證據狀態紀律（依 addendum 要求雙軌記錄，不升級）：Agent A raw-DOM 報告（commit `16224b4`）為 `AUTHOR_HANDOFF=READY`；獨立審查（commit `0160f66`）為 `INDEPENDENT_EVIDENCE_ACCEPTANCE=CHANGES_REQUESTED`（原始 DOM 與逐頁機器可讀評估結果不在 repo 內）。故 §11 的產品有效性 oracle 採 A 的規格（marker / Title / Code XPath 與有效性 gate 定義），但 B 的可執行斷言只建立在 repo 內可複核的材料上：歷史 DVD fixtures（離線）＋依 A §3 文件化特徵建模的 synthetic 404 控制頁（明示為建模，非 A 的原始證據）。一項部分佐證：歷史 fixture `dvd-046`/`dvd-281` 以 A 規格 selector 擷出的 Title/Code（`ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題!`/`046`、`熊ケツ4`/`281`）與 A 報告矩陣完全一致——這是對 A 兩個頁面欄位值的獨立離線複現，不構成 G1 整體接受。

### 11.1 B-08 — 路由選擇 ≠ 產品有效性（雙軸矩陣）

測試：`TestRouteVersusProductValidity`（新增 11 項，全數通過）。有效性 gate（fail-closed）：`品番` marker 存在 ∧ Title 非空 ∧ Code 為非空**字串**且與 canonical 最後段完全相等 ∧ canonical 與請求 URL 相等；任一不成立即拒絕，並回傳理由清單。

| Case | (1) Handler（candidate config） | (2) 產品有效性 | 關鍵 oracle |
|---|---|---|---|
| `/dvds/234` | `dvdSceneScraper` | 有效（A 矩陣：Title/Code 234/canonical 一致；B 離線 fixture 未含 234，以 A 規格為準、待 F/Gate B 複核） | A §2 |
| `/dvds/084` | `dvdSceneScraper` | 有效產品；Details 可為空（`SOURCE_FIELD_ABSENT`，不得回補）；Image 為 soldout 圖属政策案（見 11.2） | A §2/§5 |
| `/dvds/046` | `dvdSceneScraper` | 有效；Code = 字串 `"046"`（測試斷言型別與值，禁止 int 46） | 歷史 fixture 實跑 + A §2 互相佐證 |
| `/dvds/281`、`/dvds/173`、`/dvds/215` | `dvdSceneScraper` | 有效（Title/Code/canonical 三者一致） | 歷史 fixture 實跑 |
| `/dvds/00`（404） | `dvdSceneScraper`（依 URL 形狀） | **拒絕**：marker 不存在、Title/Code 空；canonical 仍被填入（= 被 pin 住的危害） | synthetic 404（依 A §3 建模）+ A §3 |
| `/dvds/999999`（404） | `dvdSceneScraper`（依 URL 形狀） | **拒絕**：同上；且經 Clips selector 集擷取時同樣呈現「canonical 已填、核心欄位空」的部分 metadata，validity 同樣拒絕 | synthetic 404 + A §3 |
| `/clips/284`、`/clips/282` | `clipSceneScraper` | Clips 契約不變（§8），不經 DVD handler | §3/§8 |
| `example.com` 未匹配控制 | 無 handler | 不適用；其後 Stash 行為屬 upstream issue #97，獨立追蹤、本套件不斷言 | §2 |

雙軸獨立性另有專項測試：同一批 URL 中 `/dvds/046`（handler=DVD, valid=True）與 `/dvds/00`（handler=DVD, valid=False）並列，證明 (1) 不能推論 (2)、(2) 也不能推論 (1)。

### 11.2 B-09 — 404 fail-closed：機制評估與建議

事實前提：Stash declarative XPath 欄位彼此獨立（Wave 1B 已就 Clips Title-less 案例記錄同一限制），**沒有任何 YAML 機制能讓單一欄位的條件自動守護其他欄位**。404 頁上 Title/Code（marker 相鄰 selector）天然為空，但 URLs（canonical selector 與 marker 無關）仍會被填入——這正是必須被偵測並拒絕的 wrong-but-plausible 部分 metadata。可行機制（皆為評估，未由 B 實作）：

| 機制 | 內容 | 證據/可行性 | 代價與風險 |
|---|---|---|---|
| (i) 逐欄位 XPath 自守護 | 對與 marker 無內建關聯的欄位（URLs、Tags 等），把 selector 改為以 marker 存在為條件的 XPath 1.0 形式，例如於 predicate 中引用文件全域節點集（`boolean(//h2[contains(.,'品番')])`） | XPath 1.0 語法層成立；Stash 使用 `antchfx/xpath`（XPath 1.0 相容實作），但全域節點集 predicate 在該實作與 Stash `getXPathQuery` 下的實際行為**未驗證**，需 F 在整合時以 fixture + Gate B 實證 | selector 可讀性下降；每個欄位都要個別處理；若實作不支援，會以「永遠空」或「永遠有值」的形狀靜默失敗，比現況更難察覺 |
| (ii) Consumer validity gate（文件化驗收門） | 在 QA/消費者層明文規定：結果須通過 11.1 的 gate（marker/Title/Code/canonical 身份一致）才可接受為成功 scrape；Stash 回傳的部分物件不自動視為成功 | 與 Wave 1B 對 Title-less 結果的既有處置（「must NOT be accepted as a successful scrape in Gate B」）同一模式，已有先例 | 不阻止 runtime 產生部分物件；依賴消費者紀律，自動化管線（如 Identify 批次）若未實作 gate 仍會吃入部分 metadata |
| (iii) 不做 YAML 層防護、僅文件記錄 | 記錄 404 canonical 危害與已知限制 | 成本最低 | 部分 metadata 會被誤認為成功，違反 addendum 的 fail-closed 要求，不建議單獨採用 |

**B 的建議**：(ii) 為必要底線（Gate B 驗收與任何自動消費者都必須實作 11.1 gate，本套件的 `product_validity` 可直接作為參考實作）；(i) 由 F 在整合時以專項 fixture 驗證 `antchfx` 支援度後再決定是否採用於 URLs/Tags，若採用，(ii) 仍須保留作為第二層。Image 方面：A 規格的 Image selector（alt 非空 ∧ wixstatic）在建模 404 上回傳空（已 pin 為測試），天然 fail-closed，不需額外機制；`/dvds/084` 的 soldout 圖是「有圖但政策上是否採用」的決策案，不得被引用為「無圖頁面會 fallback」的證據，亦不得因此引入更廣的 fallback selector。

### 11.3 B-10 — QueryFragment 與 harness 獨立性（確認）

- QueryFragment：維持 §7 決策 `FALSE_METADATA_RISK_CONFIRMED` + `RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA` 不變；addendum 的要求（不得假設 `sceneByURL` 會在 QF 模式被諮詢、標記 blocker、提最小緩解、待 Controller 決策）與 §7 內容一致，無新增動作。11.1 的 404×Clips-selector 測試另補強了 QF 風險面：即使是 404 DVD 頁，經 Clips 集擷取仍會產生「canonical 已填」的部分結果。
- Harness 獨立性：維持 §6 結論與作法——effective-routing 測試（本套件）與 field 測試（fixture runner）分離；`mappedExpect.scraper` 明示指定只證明欄位層。未改 production YAML、未刪共用 Clips 測試的單路由斷言（其雙路由修訂仍依 §9 由 F 執行）。

### 11.4 更新後測試結果

| 指令 | 結果 |
|---|---|
| `python -m pytest tools/tests/test_bravo_dvd_routes.py tools/tests/test_bravo_clips.py -q` | 69 passed, 9 xfailed（新增 11 項產品有效性測試全數通過；xfail 組成不變） |

### 11.5 更新後 Handoff 補充（取代 §10 後的狀態認知，不改 HANDOFF_STATUS）

- `HANDOFF_STATUS` 維持 `CHANGES_REQUESTED`（理由不變：QueryFragment blocker 待 Controller 決策；本 addendum 工作本身已完成）。
- 新增交付：B-08 雙軸矩陣（11.1）、B-09 機制評估與建議（11.2）、`TestRouteVersusProductValidity` 11 項測試（含 `product_validity` 參考實作，供 F/Gate B 採用）。
- 給 F 的新增輸入：整合 `dvdSceneScraper` 時，URLs/Tags 欄位是否採 (i) 逐欄位自守護，須先以 fixture 驗證 `antchfx` 對全域節點集 predicate 的支援；Gate B 案例表新增 `/dvds/00`、`/dvds/999999` 兩個 404 負例（期望：validity gate 拒絕，而非「有回傳物件」）。

## 12. Readiness 更新 — WAVE2E-B-ROUTING-QF-READINESS-20261104（2026-11-04）

Assignment：`WAVE2E-B-ROUTING-QF-READINESS-20261104`（P1）；Reference HEAD：`16bf5a1f8602f1d47edd9e19690f3d5479819962`（本 branch v2，已核對為本節工作的起點）。
Exit 狀態：**`ROUTING_AND_QF_TEST_HANDOFF_READY`**（僅就 B 的測試準備範圍；見 12.4 的邊界聲明）。

### 12.1 決策前提（已核對原文）

Controller 裁決 `WS-2E-QF-001`（`docs/66-wave2e-queryfragment-decision.md`，PR #98 HEAD `1eda3fada04d3c042234a9aef2edec53520271a0`，2026-11-03）：選定 `REMOVE_ORPHAN_QUERY_FRAGMENT_IN_WAVE2E`——Wave 2E 候選版移除整個 `sceneByQueryFragment`、`sceneByFragment` 保持不存在；狀態 `DESIGN_SELECTED / IMPLEMENTATION_NOT_STARTED / LIVE_UNVERIFIED`；實作 owner 為 Agent F；不適用於 PR #93（不得回溯修改）。此裁決取代本報告 §7 的選項 (a) 與 §9 中「QF 決策為移除時才改寫測試」的條件句：方向已定，B 本節即依裁決預備測試契約。docs/66 §3.4 明文要求：「Update Agent B's isolated QF tests to assert the new contract without hiding the original risk reproduction. Retire strict EXPECTED_RED only when the DVD feature is present; keep independent KNOWN_UPSTREAM_LIMITATION cases.」本節工作即此項的執行。

### 12.2 任務對照表（Assignment Tasks → 測試覆蓋）

| Assignment 任務 | 覆蓋位置 | 狀態 |
|---|---|---|
| Preserve URL matching and effective handler-selection tests | `TestCandidatePositiveRouting`、`TestCandidateNegativeAndCollision`、`TestRouteOrderDependence`、`TestProductionRoutingContract`（§2–§5） | 保留，未動 |
| Preserve product-validity checks independently of URL matching | `TestRouteVersusProductValidity` 雙軸設計（§11.1） | 保留，未動 |
| Maintain 404 canonical false-positive tests | 404 雙案（`/dvds/00`、`/dvds/999999`）× DVD/Clips 兩組 selector + canonical 已填入危害 pin（§11.1） | 保留，未動 |
| Keep historical QueryFragment false-metadata reproduction | `TestQueryFragmentOfflineExtraction`（四份歷史 DVD fixture × production Clips selector：核心欄位空、canonical 已填、Tags 四頁相同）——不依賴 QF 設定是否存在，F 移除 QF 後仍持續複現危害 | 保留，未動 |
| Prepare tests for removal of orphaned QueryFragment in Wave 2E | 新增 `TestWave2EQFRemovalReadiness`（5 項，見 12.3） | **本節新增** |
| Retain Clips URL regression coverage | `TestClipsRegressionContract` + production Clips 選路斷言 + 既有 `test_bravo_clips.py`（§8） | 保留，未動 |
| Ensure invalid DVD pages cannot be accepted as valid products solely because canonical URLs exist | `product_validity` gate（§11.1）+ 新增專項 `test_canonical_alone_is_never_sufficient`：即使是真實產品 URL（/dvds/234），擷取結果若只有 canonical 有值仍被拒絕並列明三項理由（marker/Title/Code） | **本節新增專項** |

### 12.3 QF 移除就緒測試（`TestWave2EQFRemovalReadiness`）

設計原則：synthetic 層現在就綠、production 層以 `EXPECTED_RED` 等待 F 落地、歷史事實層以條件式保存而不說謊。

1. `test_synthetic_wave2e_candidate_has_no_fragment_entries`（通過）：記憶體內的 Wave 2E 目標候選（雙路由 + 依 WS-2E-QF-001 移除 QF）中 `sceneByQueryFragment` 與 `sceneByFragment` 皆不存在。
2. `test_synthetic_wave2e_candidate_routing_survives_qf_removal`（通過）：移除 QF 不改變 URL 選路——clips 284/282 → Clips、dvds 234/084/046 → DVD（對應 docs/66 的「URL scraping does not depend on the QueryFragment setting」與 Gate B QF-01–QF-04 的離線前置）。
3. `test_synthetic_wave2e_candidate_has_no_fragment_handler`（通過，config 層）：候選設定下 fragment 入口無 handler 可用。**明示邊界**：這只證明設定層無 handler；移除後直接呼叫 fragment 的實際 runtime 結果（乾淨的 unsupported 或 upstream panic）只能由獨立 Gate B 的 QF-05/06/07 判定，panic 屬 `FAIL/UPSTREAM_BLOCKED` 而非可接受的 unsupported——本套件不斷言 runtime 已安全。
4. `test_production_candidate_has_query_fragment_removed`（`EXPECTED_RED`，strict xfail）：production 候選的目標契約。在 PR #93 基線（QF 仍在）上預期失敗；F 於 `feat/e2e-bravo-dvds` 落地移除後必須依 docs/66 §3.4 退役此標記（連同 §3 的 6 項 DVD 路由 `EXPECTED_RED`）；`KNOWN_UPSTREAM_LIMITATION` 3 項依裁決保留不動。
5. `test_production_scene_by_fragment_stays_absent`（通過）：`sceneByFragment` 基線上已不存在且移除後須保持不存在（QF-08 的離線前置）。

同時改造既有 `TestQueryFragmentContract` 兩項基線事實測試為**條件式**：QF 存在時（PR #93 基線）照原斷言執行；QF 被移除後以明示理由 skip 並指向本節就緒契約——避免 F 整合後基線事實測試以假失敗污染套件，也避免靜默刪除歷史紀錄。`TestQueryFragmentOfflineExtraction` 不加條件：危害複現與設定存廢無關，永久保留。

### 12.4 給 Agent F 的遷移清單（更新版，取代 §9 的 QF 相關指示）

1. 於 `feat/e2e-bravo-dvds` 移除整個 `sceneByQueryFragment`；`sceneByFragment` 保持不存在；Clips XPath 不得被順手改寫（docs/66 §3.3）。
2. `tools/tests/test_bravo_clips.py::test_query_fragment_preserves_url` 依 docs/66 §3.4 改為 QF-absent 斷言，建議實作：

```python
def test_query_fragment_removed_in_wave2e():
    # WS-2E-QF-001 (docs/66): the orphaned sceneByQueryFragment is
    # removed in the Wave 2E candidate; sceneByFragment stays absent.
    data = load()
    assert "sceneByQueryFragment" not in data
    assert "sceneByFragment" not in data
```

3. 退役本套件全部 7 項 `EXPECTED_RED`（6 項 DVD 路由 + 1 項 QF 移除）；保留 3 項 `KNOWN_UPSTREAM_LIMITATION`；`TestQueryFragmentContract` 的 skip 分支屆時自然生效，不需再改。
4. 執行 docs/66 §3.1 的 caller preflight（repo workflows/tests/GraphQL 整合與已知實例用法）並記錄範圍；若發現不可或缺的直接 QF caller，觸發 `DECISION_EXCEPTION=REQUIRED_QUERY_FRAGMENT_CONSUMER_FOUND` 停下回報 Controller，不得靜默恢復原 handler。此為 F 的整合前置，不屬 B 的測試範圍。
5. Gate B 依 docs/66 矩陣執行 QF-01–QF-08（exact-head、已安裝候選）；QF-05/06/07 必須回報實際 GraphQL 操作、回應與錯誤，panic 不得記為 PASS。

### 12.5 邊界聲明（依 Assignment Boundaries）

- 未編輯正式 `scrapers/BRAVO.yml`；未對 PR #93 移除 QueryFragment（本 branch 的 production 斷言維持以 PR #93 基線為對象）。
- 本節交付的是**測試就緒**，不是緩解已實作：QF 移除由 F 執行、runtime 安全由獨立 QA 驗證，二者完成前 `RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA` 的實質風險狀態不變。
- 本 branch 其餘交付（§1–§11）不變；`HANDOFF_STATUS=CHANGES_REQUESTED` 的原始理由（QF 待決策）已由 WS-2E-QF-001 回應，本 assignment 的 Exit 以 `ROUTING_AND_QF_TEST_HANDOFF_READY` 申報，二者不互相取代：前者是 Wave 2E 發布閘門狀態，後者是 B 的測試準備完成狀態。

### 12.6 更新後測試結果

| 指令 | 結果 |
|---|---|
| `python -m pytest tools/tests/test_bravo_dvd_routes.py tools/tests/test_bravo_clips.py -q -rxX` | 74 passed, 10 xfailed（新增：就緒測試 4 通過 + 1 EXPECTED_RED、canonical-only 專項 1 通過；xfail 組成 = 7 EXPECTED_RED + 3 KNOWN_UPSTREAM_LIMITATION） |

## 13. 整合衝突修正 — Clips Duration 暫緩政策（2026-11-04）

### 13.1 衝突內容（已重現）

PR #93 基線已前進：`86e34a2` → `88d27a5764c30fec1ab8bb5a325382e72a2ef09e`。其中 Controller 裁決 `WS-2E-DEF01-DEFER-20261104`（commit `f4be5cf`）移除了 `clipSceneScraper` 的 production Duration 對映（根因 R3 H4：Stash `scrapedScene()` 的 `IntPtr` 只接受 Go int，XPath 對映產生的字串值必然被棄；還原規格於 `docs/qa/PR93-DURATION-DEFERRED-SPEC.md`），且 Agent D 已於修訂範圍下判 `GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE`；v4 的 `GATE_B_FAIL` 裁決保留於紀錄、未被覆寫。

本套件（以舊基線撰寫）與新基線有兩處不相容，先以新基線 tree 實跑重現（10 failed）後才修正：

1. **Duration 契約衝突（本次指派事項）**：`TestClipsRegressionContract` 舊斷言要求 `作品TIME` 存在於 `clip["Duration"]["selector"]`，且迴圈把 Duration 列為 Clips 必須存在的欄位——新基線根本沒有該欄位（KeyError），且斷言方向與已核准的暫緩政策相反。
2. **Details selector 漂移（同批基線前進的連帶項）**：DEF-02 修正（commit `ce7ef6c`）把 Details 改為 `$desc` 容器內的 rich-text span selector 並新增 `common: $desc`；本套件的離線擷取器既不解析 `$common` 變數、也不支援新 selector 形狀，QF 歷史複現測試因此失敗。此項不是政策衝突，而是基線事實更新，B 作為自己擷取器的維護者一併吸收。

### 13.2 修正方式（依指派：驗證正式 Duration 不映射、來源測試獨立保留）

- **正式契約改向**：`test_clip_selectors_unchanged` 移除 Duration 必存要求與迴圈中的 Duration；新增 `test_production_duration_is_not_mapped`——斷言 `"Duration" not in clipSceneScraper.scene`，並 pin 住 YAML 內文的裁決 ID `WS-2E-DEF01-DEFER-20261104` 作為 provenance。與 PR #93 自身測試（`test_bravo_clips.py` 的 `"Duration" not in clip`）方向一致、不重複其實作細節。
- **來源層獨立保留**：新增 `test_duration_source_evidence_preserved_independently`——斷言 (i) 還原規格文件 `docs/qa/PR93-DURATION-DEFERRED-SPEC.md` 存在且含裁決 ID；(ii) 來源案例 fixture `clip-missing-duration.html` 存在；(iii) production fixture manifest 的所有 `mappedExpect` 均不含 Duration 欄位（production 層已移除、來源層另存的結構證據）。延遲 selector 的實際求值屬 PR #93 自身的 `DEFERRED_DURATION_CASES` 測試，B 只做 provenance 層引用，不複製其實作，避免兩份來源測試日後漂移。
- **QF 擷取語義對齊**：`test_dvd_dom_yields_no_core_fields` 的 Duration 斷言改為 `out.get("Duration", []) == []`——暫緩後「未對映」與「擷取為空」在此同義；歷史危害的形狀結論（核心欄位空、canonical/Tags 有值）不變，且已以新 Details selector 在四份 DVD fixture 上重跑確認 Details 仍為空（新 selector 於 DVD DOM 無命中，與 lxml 預檢一致）。
- **擷取器升級**：`clip_extract_on` 新增 `$common` 變數解析（與 fixture runner 的 `resolveSelector` 同語義：字面 replaceAll、長 key 優先）；evaluator 新增 DEF-02 新 Details selector 形狀的支援（容器內第一個去 U+200B 後非空的 rich-text span）。

### 13.3 基線移動與驗證

- 本 branch 已 rebase 至 PR #93 最新 HEAD `88d27a5`（B 的 3 個 commit 乾淨重放，無衝突；commit SHA 因此更新，內容譜系不變）。此後 B 的 production 斷言對象即為已核准的新基線；§1 的 BASE_SHA 記錄為原始交付當時值，本節為準。
- 驗證（rebase 後、修正後）：`pytest tools/tests/test_bravo_dvd_routes.py tools/tests/test_bravo_clips.py` = 82 passed, 10 xfailed；全套件 = 386 passed, 10 xfailed, 0 failed；fixture manifests：clips 11 cases、historical 3 cases verified。
- 對 F 的影響：整合時 production 契約以本節為準——Clips 回歸不得再要求 Duration 對映存在；Wave 2E 的 `dvdSceneScraper` 本來就依 C-FIX-4 不含 Duration（Controller 2026-11-02 裁決 Duration 為 GROUP-only），與本次暫緩方向一致。§12 的 Exit（`ROUTING_AND_QF_TEST_HANDOFF_READY`）不受影響；`EXPECTED_RED` 數量不變（7）。
