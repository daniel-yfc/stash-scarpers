# PR #93 DEF-01 根因隔離調查報告 R3

- Assignment：`WAVE2E-G-PR93-DEF01-TYPE-ISOLATION-20261104`
- Workstream：`WS-2E-00 / Wave 1B Clips Stabilization`，Role：Agent G
- 對照 HEAD：`d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6`（PR #93，Draft，未合併）
- 受測 Stash：`v0.31.1-182-g9e9ad972`，原始碼 commit `9e9ad972643320e737c711884f10e4285f0f3a88`
- 隔離複本：`~/workspace/review/stash-r3-isolation/stash`（僅此複本含新增測試檔，
  未推送任何 repo；使用者生產／測試 Stash 皆未動）
- 工具鏈：Go 1.25.1（依 go.mod `go 1.25.0` 就近安裝於隔離目錄）
- 報告語言：zh-TW；日期：2026-11-04

## 1. 結論

**`GATEB-DEF01-H4-TYPE-MISMATCH`：END_TO_END_REPRODUCED。**

DEF-01 的根因不是 XPath、不是 JavaScript、不是 GraphQL 序列化，而是
mapped scraper 管線缺少「字串 → int」的轉換：管線每一站都只產出字串，
而 scene Duration 的讀取點只接受 Go `int`。因此任何 mapped scraper 的
scene Duration——無論 selector 寫得多正確——在受測版本都會是 `null`。

本報告**不是** Gate B PASS、**不是** MERGE_READY。PR #93 未動，
Gate B 在新 HEAD 仍未執行；v4 `GATE_B_FAIL / DEF_01_OPEN_P1 / DEF_02_CLOSED`
為 Agent D 連結任務的裁決，歷史事實予以保留。

## 2. 四路區分（定稿）

| 層 | 結果 | 證據 |
|---|---|---|
| 1. XPath 抽取 | 正常 | Test B：三種 selector 皆抽出分鐘，mapped 值皆為 `"1800"` |
| 2. JavaScript 後處理 | 正常，且與缺陷無關 | Test C：無 JS、JS 轉換、fixed 值三路皆同樣歸零 |
| 3. Go 字串／int 轉換 | **缺失，唯一故障點** | 管線無任何轉換站；`IntPtr` 對字串斷言失敗回 `nil` |
| 4. GraphQL 序列化 | 忠實，無獨立故障 | `ScrapedScene.Duration *int`；收到 `nil` 即序列化為 `null` |

## 3. 程式碼路徑（受測 commit 實查，行號為該 commit）

```text
xpathQuery.runQuery            pkg/scraper/xpath.go:303
  → []string（htmlquery 抽出的節點文字，皆為字串）
mappedConfig.process           pkg/scraper/mapped_config.go:49
  → postProcess（:92，[]string 進、[]string 出）
  → setSingleValue(i, k, text)（mapped_result.go:86，簽名只收 string）
  → r[index][key] = value      （interface{} 內裝 string）
mappedScraper.scrapeScene      pkg/scraper/mapped.go:176
  → results[0].scrapedScene()
mappedResult.scrapedScene      pkg/scraper/mapped_result.go:171
  → Duration: r.IntPtr("Duration")（:182）
mappedResult.IntPtr            pkg/scraper/mapped_result.go:71
  → val, ok := v.(int)；字串時記錯
    "Int field Duration is string in mappedResult" 並回 nil
models.ScrapedScene.Duration   pkg/models/model_scraped_item.go:692（*int）
  → nil 序列化為 GraphQL duration: null
```

補充路徑事實：

- JS 後處理 `postProcessJavascript.Apply`（mapped_postprocessing.go:212）
  明確寫著「assume output is string」，回傳 `output.String()`（:247）。
- Fixed 值同樣走 `setSingleValue`（mapped_config.go:49 前段），故連
  fixed `"1800"` 也只能是字串。
- 空值路徑：`runQuery` 不收空字串；`cleanResults`（mapped_config.go:508）
  刪除 `""`，故缺分鐘時根本沒有 Duration 鍵，`IntPtr` 由缺鍵回 `nil`——
  與「不猜測」行為一致，不是故障。
- 唯一 `IntPtr` 呼叫點就是 scene Duration（:182）。Movie／Group 的
  Duration 走 `stringPtr`（:229、:246），不受影響。
- 既有測試的精確範圍（對指派敘述的勘誤）：上游 `TestMappedResultIntPtr`
  已明示「wrong type returns nil」（字串 `"120"` → nil），故字串→nil
  在 `IntPtr` 層是**明示行為**，不是未定義行為；上游缺的是端到端一層：
  管線只能產出字串，故 mapped scene Duration 永遠到不了 int。
  既有 `TestMappedResultScrapedScene` 只覆蓋 int 3600 與缺鍵，
  未覆蓋 scene 層的字串案——本報告 Test A 補上這一格。

## 4. 隔離重現 Test A／B／C（全數通過）

測試檔（僅存於隔離複本，未提交）：
`stash/pkg/scraper/r3_def01_type_isolation_test.go`（本報告附件之三）。
文件使用 Gate B v3 L9 實機標題順序（Code、`Clip`、30、乾淨作品TIME、min），
以 Stash 自帶的 htmlquery 引擎實跑，非 lxml／jsdom 類比。

### Test A — mappedResult 型別

- `{"Duration": 1800}`（int）→ `ScrapedScene.Duration = 1800`。
- `{"Duration": "1800"}`（string）→ `nil`。
- `{"Duration": "30"}`（string）→ `nil`。
- 靜態事實：`setSingleValue` 簽名只收 `string`，故管線無任何路徑
  能存入 Go int；int 能過只是因為測試直接構造，現實管線到不了。

### Test B — 完整管線（process → mapped value → 型別 → scrapedScene）

三種 selector，同一個 L9 文件，同一支 BRAVO JS（首位數字 × 60）：

| Selector | mapped 值 | 型別 | Title／Code | Duration |
|---|---|---|---|---|
| R2 forward（Clip 後首個數字首字非空 h2） | `"1800"` | string | 正常（284） | nil |
| v2 simple preceding（作品TIME 前 h2） | `"1800"` | string | 正常（284） | nil |
| literal（`//h2[normalize-space()='30']`） | `"1800"` | string | 正常（284） | nil |

Title 與 Code 存活、唯 Duration 歸零，證明抽取成功、丟失點在後段。
三種軸向同一結局，故 XPath 形狀與缺陷無關；第四次 XPath 替換在邏輯上
已被排除，不只是經驗上不建議。

### Test C — 後處理獨立性

| 路徑 | mapped 值 | Duration |
|---|---|---|
| C1：literal `"1800"`，無後處理 | `"1800"` string | nil |
| C2：`"30"` ＋ JS 轉換（BRAVO 形狀） | `"1800"` string | nil |
| C3：fixed `"1800"`（ bypass XPath） | `"1800"` string | nil |

JS 有無、轉換與否、甚至繞過 XPath，結局完全相同。

### 執行紀錄

- 首次執行：`go test` 因 `/tmp` 為 512M tmpfs 滿載而編譯失敗
  （`no space left on device`），與測試本身無關。
- 第二次執行（TMPDIR 改指家目錄，模組快取已暖）：

```text
=== RUN   TestR3MappedResultDurationType
--- PASS: TestR3MappedResultDurationType
=== RUN   TestR3MappedPipelineDuration
    --- PASS: .../R2_forward_from_Clip
    --- PASS: .../v2_simple_preceding_from_作品TIME
    --- PASS: .../literal_minutes_node
=== RUN   TestR3PostProcessIndependence
--- PASS: TestR3PostProcessIndependence
PASS / ok github.com/stashapp/stash/pkg/scraper
```

- 全套件迴歸：`go test ./pkg/scraper/ -count=1` → `ok`，新增測試檔
  未拖垮既有測試。

## 5. Test D — 版本比對

- 受測 commit `9e9ad972` 是 `944dd69` 的直接祖先，兩者之間僅一筆提交
  （`944dd69 Fix: Add Optional Graphql Filter (#7318)`）。
- `git diff 9e9ad972 944dd69 -- pkg/scraper/` 為空；`IntPtr`、
  `setSingleValue`、`scrapedScene` 在 develop 仍與受測版逐字相同；
  區間內無任何 Duration 相關提交。
- 結論：**上游最新受查 develop 亦無轉換修正**，不得假設換版即修復。

## 6. G-R3-02 修正選項評估

### A — 上游修正（建議首選，條件：Duration 為強制且修正版可實際部署）

修正邊界二選一（屬上游 PR 決策，本報告不代定）：

- A1：在 `IntPtr` 內做嚴格字串解析。現況唯一呼叫點是 scene
  Duration，爆炸半徑目前等於 Duration 一欄；但未來其他 int 欄位
  若共用 `IntPtr`，將一併變為字串寬容，PR 說明須載明。
- A2：在 `scrapedScene` 內為 Duration 單獨加轉換 helper，`IntPtr`
  保持嚴格。影響面最小，語意最清楚（Duration 是唯一
 「YAML 字串 → GraphQL int」的欄位）。

解析規則（與 §7 一致）：僅接受全數字字串；空、空白、非數字、
小數、負數、溢位一律回 `nil` 並記錯，不得捏造、截斷、進位；
`"0"` 必須回 `&0`（present zero），不得與缺失混為 `nil`。
部署條件：修正版必須實際部署到測試／生產環境才算數；僅合併上游
PR 但未升級部署，不構成 Gate B 重驗條件。

### B — 範圍限縮（須 Controller 明確風險接受）

BRAVO Clips 暫時省略 Duration，待上游支援後再補。必須附帶修訂版
驗收合約（Duration 從強制改為暫緩）與獨立驗證；v4 `GATE_B_FAIL`
保留為歷史事實，不得追溯改寫為通過。**本輪不執行**：PR #93
在 Controller 裁定前不動。

### C — 替代後端（僅在 A 不可行且 Duration 仍強制時考慮）

例如 script scraper 後端（其值來自解碼後的型別化資料，非 XPath
字串），理論上可回傳型別化 Duration；但須重寫 BRAVO 後端、
測試 harness、相容性與維護成本皆上升。**不得僅為繞過 bug 而採用。**

### 上游提案大綱（獨立工作流，非 PR #93 內容）

- 影響檔：`pkg/scraper/mapped_result.go`（轉換邏輯）、
  `pkg/scraper/mapped_result_test.go`（迴歸測試；本報告 Test A／B
  可作起點，惟須依上游測試慣例整理後再提交）。
- 基準修訂：`9e9ad972`；相容性：`IntPtr` 唯一呼叫點為 scene Duration，
  故 A1／A2 皆不影響其他欄位現況；Movie／Group Duration 為字串欄位，
  不在修正範圍。
- 部署意涵：修正須經上游審查、合併、發布，並實際升級測試／生產
  Stash 後，Agent D 才能以新 M0＋專屬租約重驗 284／282／283。

## 7. G-R3-03 迴歸規格（分層，不得混淆分鐘解析與最終 int 欄位）

### Runtime 層（上游測試，輸入為 mappedResult 內的字串）

| 輸入 | 修正後期望 |
|---|---|
| `"1800"` | 1800 |
| `"2700"` | 2700 |
| `""`（缺值） | nil |
| `"   "`（全空白） | nil |
| `"abc"`、`"12x"`、`"1.5"`、`"-5"` | nil，不捏造 |
| `"9999999999999999999999"`（溢位） | nil，安全拒絕 |
| `"0"` | `&0`（present zero，非 nil）|
| int `1800`（既有行為） | 1800（不退化）|

### Scraper 層（BRAVO fixture／Gate B live，輸入為分鐘）

| 輸入 | 修正後期望（須 runtime 修正先落地並部署）|
|---|---|
| `"30"` 分鐘 | 1800 秒 |
| `"45"` 分鐘 | 2700 秒 |
| 缺分鐘 | 無 Duration，不猜測 |
| 價格／spacer 負例 | 不誤取（R2 fixture 287／288／289 已覆蓋）|
| Clips 284／282／283 | 1800 秒（live 重驗，須新 M0＋租約）|

## 8. 邊界遵循聲明

- `scrapers/BRAVO.yml` 未動；Details、QueryFragment、DVD 路由與
  fixture 未動；Duration 預期未弱化；PR #93 分支內未改 Stash Core。
- 查核：PR #93 工作區 `git status` 乾淨、HEAD 仍為 `d6d6fbf`；
  隔離複本唯一變更為未追蹤的測試檔。
- 未取新 live lease、未存取 stash-test、未對 PR #93 留言或改 body。
- Agent D 連結任務（v4 審計發布、重現獨立審查、未來 live 驗證）
  屬 Agent D 授權範圍，本報告僅提供重現供其審查，不代行。

## 9. 待決事項

1. Controller 裁定：選 A（上游修正，附部署條件）或 B（限縮＋新驗收合約）。
2. 若選 A：另開上游工作流（§6 大綱），不得塞入 PR #93。
3. 若選 B：修訂驗收合約後，PR #93 的 Duration 處置與獨立驗證另行授權。
4. Agent D：獨立審查本報告 Test A／B／C 與基準修訂；僅在修正部署
   或 B 合約生效後，才取新 M0＋租約重驗。
