# Prefix Metadata Suite — Task 5 Source Enrich 規格書

- 狀態：V2.5 最終定稿。本檔是開工基線。
- 版號：V2.5-task5
- 日期：2026-10-13
- 取代：V2.0、V2.1、V2.2、V2.3、V2.4，以及同日所有對照稿。
- 關鍵字：MUST 必須、MUST NOT 禁止。未標註的敘述是定案規則。
- 實作者不得再回查舊版補規則。舊版與本檔衝突時，以本檔為準。

## 0. 定案

1. 第一版只做 Phase A、prefix/group 的 Phase B、Phase C dry-run。不 mutation。
2. 有非空 Code 才外部查詢。查詢鍵是 Code，不是 Title。
3. 來源順序只決定 CSV 排序，以及正規化後值相同時採用哪一個原始字串。不得在不同值之間自動選邊。
4. 信心分數只用設定值。來源自填分數不得參與比較。比較使用十進位，不用二進位浮點。
5. `min_auto_confidence` 預設 0.8。等於門檻可以過。低於門檻不可套用。
6. 已採用的 `code_exact` 只要正規化後的值不同，該欄就不可套用。低於門檻的反對證據也算。
7. 只有完整呼叫成功且零筆 `code_exact`，而且該次允許當查無，才是查無。Mode Y 且該站不在 `trusted_miss_sites` 時，零筆不是查無。後續來源可列出，但 MUST NOT 可套用。
8. 第一個實際查詢的來源是 primary。primary 失敗或空結果不可信時，後續來源不得晉升，也不可套用。此判定看呼叫模式，不看它是 prefix 還是 group。
9. 別名學習關閉。設為 true 即批次失敗。未命中不得寫候選。
10. GVDB、設定頁、live apply、重寫既有 scraper，都不在第一版。

## 1. 目標與非目標

### 1.1 目標

對「有 Code，且至少一個第一版開啟欄位為空」的 scene，用 prefix 對應站與同集團站的 Code 精確命中，產出可抽查的變更計畫。別名正規化只用於比對，不合併人物。

### 1.2 第一版做

- 讀取既有 `alias-table.json`。不改寫。
- 依人工簽入的 `site_modes`，以 Mode S 或 Mode Y 呼叫 prefix 與 group。
- Mode Y 的可信查無只來自人工簽入的 `trusted_miss_sites`。
- 產出變更計畫 CSV、稽核 JSONL、manifest、checkpoint。
- 啟動前驗證 `plugin.yml`。

### 1.3 第一版不做

Task 5 MUST NOT：

- 覆寫非空欄位，或向已有 performer 追加名字。
- 建立 performer，或自動合併 performer。
- 用 Title 相似度查詢、比對或建議合併 scene。
- 寫入未確認別名，或建立 `learned-candidates.json`。
- 執行 Stash mutation，或寫入 Scene customFields。
- 猜測站點對照、Code 前綴、和曆或時區。
- 為了取得 HTTP 狀態碼而重寫既有 YAML scraper。
- 從 YAML 是否含 `sceneByName` 或 `action: script` 推定呼叫模式。
- 讀取探針 JSON，或由探針、測試腳本寫入 `plugin.yml`。

### 1.4 後續版本

不阻塞第一版，也不排入第一版日程：GVDB、其他站 Title 查詢、別名候選、設定頁、live apply、多值欄位追加、把 Mode Y 站改寫成 Mode S。

## 2. 架構

Task 5 是 `prefix-metadata-suite` 的第五個 task，與前四個 task 共用 `plugin.yml`。不得拆成第二個 plugin。

Scraper YAML 只描述單站擷取。來源編排、等待放棄、合併與 dry-run 屬於 plugin task。Stash 沒有 `sceneByCode`。把品番放進 `sceneByName` 再過濾，不算已具備 Code 查詢能力；能力只依附錄 A 的實測。

```
符合 selector 的 Scene
  │
  ▼
啟動驗證。不合法則批次失敗，零網路查詢
  │
  ▼
Phase A  本地別名正規化
  │
  ▼
Phase B  每來源每 scene 一次 Code 查詢
  │
  ▼
Phase C  只寫 CSV 與稽核。不 mutation
```

### 2.1 套件

```
tasks/source_enrich/
├── __init__.py
├── config.py
├── normalize.py
├── phase_a_alias.py
├── phase_b_query.py
├── phase_c_plan.py
└── adapters/
    ├── prefix_site.py
    └── group_site.py
```

不得把 phase 檔畫成單一 `source_enrich.py` 的子檔案。

### 2.2 站點對照

`resolve_sites(scene)` 沿用 Phase 0–4 已存在的對照。本規格不定義哪個 Code 屬於哪個站，也不新增 `group_map`。

回傳：

- `prefix`：零或一個站。
- `group`：零或多個站，已排序。

沒有對照時，該 scene 為 `scene_skipped`，理由 `no_site_mapping`。MUST NOT 猜站。對照介面不存在時，整批失敗。

查詢中若解析出的站不在 `site_modes`，整批失敗。不得把該 scene 悄悄跳過。

### 2.3 失敗語意

| 層級 | 定義 | 動作 |
|---|---|---|
| 單源失敗，Mode S | 看到 429、5xx、連線失敗、解析失敗、分頁未完成、robots 不允許 | `source_skipped`，使用對應細分理由 |
| 單源失敗，Mode Y | Stash 回傳錯誤 | `source_skipped`，理由 `stash_opaque`。不得記查無，不得記成 429、5xx 或分頁未完成 |
| 呼叫端放棄等待 | 任一種模式，等待超過 `timeout_seconds` | `source_skipped`，理由 `caller_timeout`。不代表伺服器逾時 |
| 單源查無，Mode S | 呼叫完整成功且零筆 `code_exact` | `source_miss` |
| 單源查無，Mode Y 白名單 | 同上，且該站在 `trusted_miss_sites` | `source_miss` |
| 單源零筆，Mode Y 非白名單 | 零筆，且該站不在白名單 | `source_untrusted_empty`。不得記 `source_miss`。Phase C 用 `primary_opaque_miss` |
| 單 scene 失敗 | scene 已消失，或該 scene 輸出無法寫入 | `scene_failed`，繼續下一個 scene |
| scene 跳過 | 無 Code，或無站點對照 | `scene_skipped`，繼續 |
| 批次失敗 | 設定不合法、別名表損壞、lock 衝突、輸出不可寫、checkpoint 與 CSV 不一致 | 停止。manifest 不得為 `complete`。零 mutation |

零 scene，或全部 scene 失敗，只要輸出完整寫入，狀態仍可為 `complete`。

A、B、C 是同一個 task 的三個階段，不是三個會自動互啟的 task。

### 2.4 呼叫模式

模式看 Task 5 自己看不看得到傳輸結果，不看檔案副檔名。

- Mode S：Task 5 自己發 HTTP，或自己以 stdin/stdout 執行 script。完整失敗分類只在此模式適用。robots 檢查只在此模式、由 plugin 發請求時執行。
- Mode Y：Task 5 透過 Stash 呼叫 scraper，只拿回 fragment 或一段不透明錯誤。Stash 代跑的 script 仍是 Mode Y。plugin 不做 robots 預檢，沿用 Stash 行為。

D1 只產生候選，不寫設定。對 script 檔嘗試一次直接 stdin/stdout 呼叫；成功才是 Mode S 候選。失敗，或不是可直接執行的 script，就是 Mode Y 候選。

不得因為探針經 Stash 查過就把該站記成 Mode Y。不得因為 YAML 寫著 `action: script` 就記成 Mode S。不得寫成「依該站 mode 決定怎麼查」。

操作者把候選抄進 `site_modes`。只有使用者指名可以丟棄某些站的 YAML 邏輯時，才為那些站另寫直接 HTTP。第一版預設不另寫。

## 3. 資料模型

### 3.1 別名正式表

沿用 Task 3 的實際 `alias-table.json`。驗收不得只靠自造測試檔。Task 5 只讀。

```json
{
  "version": "2026-10-13",
  "decided_by": "user",
  "canonical": {
    "山田太郎": ["やまだたろう", "Yamada Taro"]
  }
}
```

範例必須是人物別名。不得用廠牌或系列名，例如 JUSTICE、KO COMPANY。

- 鍵是 `canonical_name`，不是 Stash performer ID。不得使用 `canonical_id`。
- 鍵本身也是可查詢寫法。
- 碰撞判定使用 §4.2 的完整文字正規化，不只 casefold。
- 一個正規化寫法只能對到一個 `canonical_name`。否則整表損壞。
- 同一鍵下的重複寫法忽略，不失敗。
- 空鍵、空寫法、檔案不存在、無法解析、UTF-8 失敗：整表損壞。
- 合法 JSON 且 `canonical` 是空物件：空表。全部未命中，不失敗。
- 實際檔案若含廠牌或系列名，先拆檔再跑 Phase A。第一版不做 schema migration。

不得建立或追加 `learned-candidates.json`。

### 3.2 查詢結果

被比對的 Code 只限遠端 scene 的 code 欄位。出現在標題、說明、tag 或推薦區的 Code 不是命中。

- `source_type` 第一版只允許 `official`、`group`。
- `match_type` 只允許 `code_exact`。
- 缺 `match_type`、缺 `source`、缺 `field`，或 `value` 為空：丟棄該欄結果。
- 結果內的 `confidence` 一律忽略。
- `source_url` 可空，不因此降級。

### 3.3 分數

| 來源類型 | 設定鍵 | 預設 |
|---|---|---|
| official | `confidence.official` | 0.9 |
| group | `confidence.group` | 0.8 |

設定值不在 0 到 1 的閉區間，批次失敗。0.8 過門檻，0.79 不過。

## 4. 正規化

所有比對前都先做 Unicode NFKC。

### 4.1 Code

順序固定：NFKC、刪除 `Cf` 與 `Cc`、casefold、刪除所有空白（`Zs`）與所有破折號（`Pd`）。

- `KO-123`、`KO123`、`ko 123`、`ＫＯ－１２３` 是同一個 `code_key`。
- `KO-123` 與 `123` 不是同一個。MUST NOT 去除站點前綴。
- 刪完後是空字串，視為無 Code。

### 4.2 文字

順序固定：NFKC、刪除 `Cf` 與 `Cc`、trim、連續空白壓成一個空格、casefold。不刪破折號。

因此 `KO-Company` 與 `KO Company` 是衝突。`KO  Company` 與 `KO Company` 在別名載入時就是同一寫法。

### 4.3 日期

只接受剛好 `YYYY-MM-DD`，且是有效格里曆日期。

- `2024-02-29` 可比較。
- `2023-02-29`、`2024-13-01`、`2024-02`、任何帶時間或時區的字串：該欄無值。
- MUST NOT 換時區，也不得拿無值製造衝突。

### 4.4 空值

`null`、`""`、純空白、全形空白，都算空。文字正規化後為空，也算空。

## 5. 查詢流程

### 5.1 Selector

預設且第一版唯一合法值是 `missing_fields_with_code`。同時成立才選入：

1. Code 正規化後不是空字串。
2. 第一版開啟欄位中，至少一個為空。

只有 Title、只有 performer、或開啟欄位都已有值：不選入，不查詢。

### 5.2 Phase A

1. 不做網路請求。
2. 取 performer 名稱。空字串忽略。沒有 performer 不是失敗。
3. 命中則比對鍵改用 `canonical_name`，記 `alias_resolved`。
4. 未命中保留原名，記 `alias_miss`，不阻擋查詢，不寫候選。
5. 別名表損壞是批次失敗，發生在任何 scene 查詢之前。

### 5.3 Phase B

每個來源對每個 scene 至多一次 Code 查詢，回傳整份 scene fragment。欄位萃取在 Phase C。缺三個欄位不是查三次。`ambiguous_hit` 作廢的是這一次查詢。

primary 是這條鏈上第一個實際發出的來源。

1. 有 prefix 就先查 prefix。它是 primary。
2. prefix 與某個 group 解析到同一站：不查第二次。
3. prefix 有唯一 `code_exact`：其餘尚未查過的 group 站仍可各查一次。Phase C 只萃取仍空的開啟欄位。
4. prefix 是可信查無：group 的唯一達標結果可以套用。
5. prefix 失敗：group 可列出，`apply_eligible=false`，理由 `primary_unavailable`。
6. prefix 空結果不可信：依 §0.7。group 可列出，不可套用，理由 `primary_opaque_miss`。
7. 沒有 prefix 時，第一個實際查詢的 group 成為 primary。它失敗時，後續 group 可列出但不可套用，理由 `primary_unavailable`。它是未入白名單的 Mode Y 且零筆時，後續同樣不可套用，理由 `primary_opaque_miss`。MUST NOT 把下一個來源晉升為 primary。
8. 無 prefix 也無 group：`scene_skipped`，理由 `no_site_mapping`。

同一次查詢：

- 零筆 `code_exact`，且該次允許當查無：查無。
- 剛好一筆 `code_exact`：採用。
- 兩筆以上 `code_exact`：整次作廢，理由 `ambiguous_hit`。不得取第一筆。
- 搜尋結果有多筆，但只有一筆的 scene code 是 `code_exact`：採用該筆。

筆數以 §4.1 的 `code_key` 計算。同一鍵、原始字串不同，算兩筆。回傳五筆，其中 `KO-123` 與 `ＫＯ－１２３` 各一筆，整次作廢。

第一版序列執行。每源只試一次，不重試。`batch_size` 只代表 checkpoint 粒度，不是並行度。

Mode S 的單一 source 逾時預設 30 秒，包含該次呼叫的全部分頁。分頁未完成不得把已讀頁面的零筆當成查無。同一 host 的請求間隔預設 1 秒；既有 scraper 更嚴則從嚴。robots 不允許時不發送請求，記 `robots_disallow`。

Mode Y 不做 robots 預檢。外層等待超過 `timeout_seconds` 就放棄，記 `caller_timeout`。

### 5.4 Phase C

第一版只寫計畫，不呼叫 mutation。

| 情況 | `apply_eligible` | `reason` | `action` |
|---|---|---|---|
| 欄位非空 | 不產生列 | — | — |
| 唯一達標結果，且通過 §5.5 | true | `fill_empty` | 見 §5.5 |
| 多個達標結果，正規化後一致 | true | `fill_empty` | 見 §5.5 |
| 已採用的 `code_exact` 值不一致 | false | `conflict` | 空 |
| 達標結果同分且值不一致 | false | `tie` | 空 |
| 低於門檻 | false | `below_threshold` | 空 |
| primary 失敗後的後續結果 | false | `primary_unavailable` | 空 |
| primary 空結果不可信，後續有結果 | false | `primary_opaque_miss` | 空 |
| 同一次查詢兩筆以上 `code_exact` | false | `ambiguous_hit` | 空 |
| performer 對不到唯一既有人物 | false | `unresolved_performer` 或 `ambiguous_performer` | 空 |
| studio 對到多個既有 studio | false | `ambiguous_studio` | 空 |

低於門檻的 `code_exact` 若與達標結果衝突，仍然使該欄不可套用。門檻不能拿來忽略反對證據。

`new_value` 用勝出來源的原始字串，不用正規化字串。勝出順序是分數較高者；分數相同才用 `source_order`。來源順序只影響 CSV 排序與這個原始字串的選擇。

無 prefix、第一個 group 失敗、第二個 group 唯一達標時：列出第二個 group，`apply_eligible=false`，理由 `primary_unavailable`。

### 5.5 實體動作

比對 performer 時先做 §4.2，再查別名表。studio 只做 §4.2。

| 欄位 | 第一版動作 |
|---|---|
| title | `fill`。長度超過 2000 或含 NUL：丟棄該值 |
| date | `fill`。只接受 §4.3 |
| studio，對到唯一既有 studio | `link` |
| studio，對不到 | `create`。可套用，但第一版不執行 |
| performer，欄位為空，且對到唯一既有 performer | `link` |
| performer，對不到或對到多個 | 不可套用。MUST NOT 建立人物 |
| performer 已有任一非空名稱 | 不產生列 |

## 6. 輸出

### 6.1 檔案

一次執行使用一個 UUIDv4 `run_id`。時間戳使用 `Asia/Taipei` 的 ISO 8601，含 `+08:00`。

- `reports/source-enrich.lock`
- `reports/source-enrich-{run_id}.manifest.json`
- `reports/source-enrich-{run_id}.csv`
- `reports/audit-source-enrich-{run_id}.jsonl`
- `reports/source-enrich-{run_id}.checkpoint.json`

manifest 至少包含 `run_id`、`spec_version`、`status`、`started_at`、`finished_at`、`selector`，以及三個輸出路徑。`status` 只允許 `running`、`complete`、`failed`。`spec_version` 固定為 `V2.5-task5`。

### 6.2 lock

```json
{"run_id": "uuid", "started_at": "2026-10-14T09:00:00+08:00", "pid": 0}
```

以 exclusive create 建立。建立失敗代表已有執行個體，新執行批次失敗，不得寫入對方的檔案。

`pid` 只供人讀，不是存活證明。續跑保留原 `run_id`，把 `pid` 更新為新行程，不重建 lock。crash 後不依時間自動解鎖。放棄執行只能由操作者刪除 lock。

`enabled: false` 不取 lock。寫一筆 `task_disabled`，狀態為 `complete`。

### 6.3 CSV

欄位固定，順序固定：

`scene_id,field,old_value,new_value,source,source_type,match_type,confidence,apply_eligible,reason,action`

`old_value` 只供人工抽查，MUST NOT 參與比對。可套用列的 `old_value` 依規則應為空。

使用 UTF-8 與 RFC 4180 quoting。以 `=`、`+`、`-`、`@` 開頭的儲存格，寫出前加單引號。

零筆資料列時仍寫表頭。這可以是合法的 `complete`。

該 scene 的 CSV 列與稽核列都落地後，才可把 `scene_id` 寫入 checkpoint。checkpoint 以暫存檔加 rename 寫入。checkpoint 有 scene 但 CSV 沒有對應處理紀錄時，批次失敗，不得標 `complete`。

### 6.4 稽核

每列至少有 `ts,run_id,scene_id,phase,event,source,reason`。

`event` 只使用：`alias_resolved`、`alias_miss`、`source_hit`、`source_miss`、`source_untrusted_empty`、`source_skipped`、`scene_failed`、`scene_skipped`、`batch_failed`、`task_disabled`、`checkpoint_written`。

`source_skipped` 的 `reason` 只使用：

- Mode S：`http_429`、`http_5xx`、`connection_error`、`parse_error`、`incomplete_pagination`、`robots_disallow`。
- 兩種模式：`caller_timeout`。
- Mode Y：`stash_opaque`。

Mode Y 不得使用 Mode S 的狀態碼理由。`caller_timeout` 不得併入 `stash_opaque`。`primary_opaque_miss` 只出現在 CSV 的 `reason`，不得作為 `source_skipped` 的理由，也不得把該次零筆記成 `source_miss`。

## 7. 設定

```yaml
task5_source_enrich:
  enabled: false
  dry_run: true
  allow_live_apply: false
  source_order:
    - prefix_site
    - group_site
  enabled_sources:
    - prefix_site
    - group_site
  site_modes: {}                  # 站名: S 或 Y。操作者依 D1 觀察手寫
  trusted_miss_sites: []          # Mode Y 白名單。D4 兩次測試通過後人工簽入
  fields:
    title: true
    code: false
    date: true
    studio: true
    performer: true
    tag: false
    image: false
    details: false
  confidence:
    official: 0.9
    group: 0.8
    database: 0.6
    third_party: 0.5
  min_auto_confidence: 0.8
  gvdb:
    enabled: false
    rate_limit_seconds: 2
  alias_learning: false
  batch_size: 50
  timeout_seconds: 30
  request_interval_seconds: 1
  scene_selector: missing_fields_with_code
```

`trusted_miss_sites` 旁應有註解，寫明對應的探針檔名。plugin 不讀該檔。

下列任一項成立就批次失敗，並且零網路查詢：

- `dry_run` 不是 true，或 `allow_live_apply` 不是 false。
- `gvdb.enabled` 或 `alias_learning` 為 true。
- `fields.code`、`tag`、`image`、`details` 任一為 true。
- 開啟欄位全為 false。
- `enabled_sources` 不是恰好 prefix 與 group，或為空。
- `batch_size` 或 `timeout_seconds` 小於 1。
- `request_interval_seconds` 小於 0。
- 分數不在 0 到 1，或 selector 不是 `missing_fields_with_code`。
- `site_modes` 的值不是 `S` 或 `Y`。
- `site_modes` 的站名不存在於 `resolve_sites` 對照。
- `trusted_miss_sites` 的站名不在 `site_modes`，或該站不是 Mode Y。
- 查詢中遇到不在 `site_modes` 的站。

空的 `site_modes` 在尚未有 scene 需要查詢時不單獨構成錯誤。一旦 selector 選出的 scene 解析到站，該站就必須已在表內，否則批次失敗。空的 `trusted_miss_sites` 合法，表示沒有任何 Mode Y 查無可信。

## 8. 續跑

- 必須由操作者指定同一 `run_id`。
- manifest 必須是 `running`，lock 的 `run_id` 必須相同。
- 續跑更新 lock 的 `pid`，不重建 lock，不改 `run_id`。
- checkpoint 內的 scene 不重查、不重寫。
- 不得建立第二份 CSV。
- 不得把 `failed` 或中斷的執行改標 `complete`。

## 9. 極端輸入契約

| 輸入 | 預期 |
|---|---|
| `null`、空字串、純空白、全形空白 | 空 |
| 全形 Code、大小寫、各類破折號 | 依 §4.1 折成同一 `code_key` |
| 去掉站點前綴才相同的 Code | 不相同 |
| Code 中的零寬字元或換行 | 刪除後再比。剩空字串即無 Code |
| 回傳 5 筆，其中兩筆折成同一 `code_key` | 整次查詢作廢，`ambiguous_hit` |
| 無效日期、部分日期、帶時間日期 | 該欄無值，不製造衝突 |
| 來源自填信心 0.99 | 忽略 |
| 雙空格與單空格指向不同正規名 | 載入時整表損壞 |
| 無 prefix，首 group 失敗，次 group 唯一達標 | 列出，不可套用，`primary_unavailable` |
| 無 prefix，首 group 是非白名單 Mode Y 且零筆 | `source_untrusted_empty`，後續不可套用 |
| Mode S：HTTP 200 但無法解析 | `parse_error`，不是查無 |
| Mode S：分頁未完成 | `incomplete_pagination`，不是查無 |
| Mode Y：Stash 回傳錯誤 | `stash_opaque`，不得記查無 |
| 任一模式：呼叫端放棄等待 | `caller_timeout`，不代表伺服器逾時 |
| 非白名單 Mode Y 零筆，group 另有唯一達標 | 列出，不可套用，`primary_opaque_miss` |
| 白名單 Mode Y 零筆，group 唯一達標 | 依 §5.4 可套用 |
| 不存在的品番回空陣列 | 不得用來簽白名單 |
| 16k scene 全部逾時 | 每源一次，不重試 |
| `batch_size` 或逾時為 0 或負數 | 啟動即批次失敗 |
| 別名表損壞 | 批次失敗，零查詢 |
| 合法空別名表 | 全部 `alias_miss`，繼續 |
| performer 陣列含空字串 | 忽略該項 |
| 0 scene，或全部 scene 失敗 | 可以 `complete` |
| 兩個同時執行 | 後者失敗 |
| crash 後 lock 仍在 | 不自動解鎖 |
| prefix 與 group 同一站 | 不查第二次 |
| 公式字元開頭 | CSV 加單引號 |

`parse_error` 與 `incomplete_pagination` 只適用 Mode S。

## 10. GVDB 與後續

第一版不接 GVDB。開啟 `gvdb.enabled` 即批次失敗。

後續若另開調查，限一天，三個 host 分開記錄，不在本版實作：

- `www.gvdb.org`：只記錄主站是否可連。主站被擋不得當成資料庫不存在。
- `md.gvdb.org`：模特與作品頁。年齡警告只記錄，不在本規格設計繞過。
- `ss.gvdb.org`：站內搜尋與廠牌分類。品番查詢尚未驗證，不得假設它能回傳唯一作品。

任一 host 失敗不得整站判死，也不得把 GVDB 拉回第一版。品番查詢失敗的退出條件是不接 GVDB，不改走 `performerByName`。

live apply 另須同時滿足 `dry_run: false`、`allow_live_apply: true`、該列 `apply_eligible: true`，以及第一個寫入批次已人工全查。這些開關在第一版不生效。

## 11. 驗收

- Task 5 可獨立 dry-run，不依賴其他 task 同時執行。
- 不呼叫 Stash mutation，不寫 customFields。
- 未命中不產生候選檔。
- 非法設定零查詢。
- 稽核能區分 `source_miss`、`source_untrusted_empty`、`stash_opaque`、`caller_timeout`。
- §9 的兩個 Mode Y 情境都有 golden：非白名單凍結；白名單站可依一般規則套用。
- 中斷後 manifest 不是 `complete`。續跑不重查 checkpoint 內的 scene，且 `run_id` 不變。
- 100 個 scene 使用分層抽樣：每個開啟欄位至少 15 個 scene 缺該欄。人工抽查 CSV，不只看測試全綠。
- 附錄 A 的探針報告存在，且含 Code 來源分布。
- 簽收前，每個白名單站再查一筆已知存在品番與一筆已知不存在品番。前者應命中，後者應為空陣列。任一不符，該站不得沿用本次白名單簽收。

## 12. 開工前假設

1. Phase 0–4 已有 plugin task 啟動方式。沒有就停工，不把工作改做成設定頁。
2. 已有 `resolve_sites`。沒有就停工，不建臨時對照表。
3. Code 查詢能力只依附錄 A，以已知存在的品番實測。不以 YAML 鍵推定。
4. `alias-table.json` 結構不同時，改讀取器，不放寬「一寫法一正規名」。

## 附錄 A. D1 探針

本附錄是 50% 門檻與無效條款的唯一定義。日程只可引用，不得改寫數字或分母。

探針不是 plugin，也不是 Phase B 的胚胎。它不取 lock，不寫 manifest，不寫稽核，不寫 `plugin.yml`。

- 抽 200 個符合 selector 的 scene。
- 分母只計有 prefix 對照者。`no_site_mapping` 另列，不計入 50%。
- 有對照但呼叫失敗，算未命中，不得從分母剔除。
- 對每個納入的 scene，向其 prefix 站發一次品番查詢。
- 命中指回應中至少一筆 `code_exact`。`ambiguous_hit` 也算命中，因為站可查，只是資料髒。
- 命中比例低於 50%：不進入 D2，回到規格。不得放寬 §1.3。
- 超過一半的 Code 來自先前同一站的刮削結果時，本次百分比無效。簽收前改用檔名或人工已知品番重跑。
- 輸出 `reports/probe-{YYYYMMDD}-{HHmmss}.json`，時區 `Asia/Taipei`。不得覆蓋舊檔。
- 內容至少含：每站 Mode S 候選或 Mode Y 候選、命中數、空陣列數、錯誤數、Code 來源分布，以及 `failure_surfaces_as_error`。
- D1 將 `failure_surfaces_as_error` 留空。
- 一天內做不出可執行探針：停工重估。不得把 D4 到 D8 的工作吸進 D1。

Mode 觀察不得循環。先嘗試直接執行 script；成功才記 Mode S 候選。其餘記 Mode Y 候選。

### A.1 誘發失敗測試

此測試只在 D4 做，不在 D1 做。它是手動步驟，逐站執行，同一站做兩次。結果回填探針記錄。操作者再依記錄手寫白名單。

故意失敗不得用不存在的品番。空陣列對不存在的品番是合法查無，不能證明管線誠實。回錯誤也可能只是 script 對怪輸入崩潰。

有鑑別力的失敗，是在 Stash 主機上暫時阻斷該 scraper 實際請求的 host，然後發一次查詢。阻斷錯 host 的結果不得記入。測完恢復連線，再做下一次，再測下一站。

兩次都回錯誤，才可把 `failure_surfaces_as_error` 記為 true，並由操作者考慮簽入 `trusted_miss_sites`。任一回空陣列，或兩次結果不一致，該站不得入白名單。

這個結果不是永久屬性。程式 MUST NOT 自動寫入 `plugin.yml`。
