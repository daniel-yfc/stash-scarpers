# Prefix Metadata Suite 規格書 V1.0

- 狀態：定版。
- 版號：V1.0
- 規格作者：Grok 4.7（Perplexity 平台）
- Timestamp：2026-10-12 05:10 CST
- 依據：審查鏈至 2026-10-12 05:08 的模型共識。條文沿用 v1.2 凍結基準稿，僅改版號與狀態。
- 出處限制：未核對到使用者逐項確認原文前，不把任何條文寫成使用者裁決。
- 原始規劃 repo 名稱維持 `daniel-yfc/stash-scarpers`。遠端核對前不得改名。

關鍵字：MUST 必須、MUST NOT 禁止。未標註的敘述是定案規則。

未見的附錄 B 項目 C2–C12 不得用「A 優先」或「最新裁決鏈」一次帶入。本規格只收錄已裁決條文。

## 1. 目標與非目標

### 1.1 目標

用版本化前綴表，從檔名、URL、標題或資料夾提取品番，推導 Studio、發行主體 Label 與 Series，先做只讀比對，再依欄位唯一性做有限寫入。

### 1.2 V1.0 範圍

- Doctor、Enrich、Normalize、Rename，以及獨立的 `clean_empty_dirs`。
- 前綴表、別名表、載入期驗證、CI、golden tests。
- 覆蓋率報告、差異 CSV、人工確認批次。
- 寫入一律先出變更計畫，dry-run 預設開啟。

### 1.3 非目標

V1.0 MUST NOT：

- 一鍵連跑。
- 用 `Scene.Update.Post` 跑全庫、改檔或自動 enrich。
- 建立品番級映射表。提前條件見 §4.4，缺任一項就是新爬蟲專案。
- 用出演者消歧。
- 用標題相似度偵測、建議合併或建立等價關係。
- 自動把新前綴寫回前綴表。
- 建立 `prefix:*` tag。
- 把非發行主體 Label 建成 studio 或 tag。
- 搬移 sidecar，或提供「只搬影片、sidecar 留在原地」。
- 重命名 screenshot、preview 等依 hash 命名的生成檔。
- 綁定任何 renamer fork 或 WatchTower 原始碼。
- 由覆蓋率自動建議「先補表或先填值」。
- 為衝突率另造百分比門檻。

## 2. 架構

一個 Python 外部 plugin，多個 task，同一份 plugin YAML。不得拆成第二個 plugin。

```
prefix-table/*.json     純資料。不得 import Stash client
aliases.json            獨立版控
site-patterns.json      站別 pattern 與第二段碼註冊表
extractor.py            純函式：文本 → 品番候選
resolver.py             純函式：品番 → 欄位狀態
tasks/                  唯一可寫入的層
```

extractor 與 resolver MUST 能在 plugin 外以 pytest 執行。

技術選型：Python 與 `stashapp-tools`（stashapi），走 GraphQL。embedded JS 只保留給日後 scene 頁檢視，不得做引擎。

V1.0 單執行緒，每批 50–100 筆 mutation，不並行。

## 3. 資料模型

| 概念 | Stash 歸屬 | 規則 |
|---|---|---|
| Studio | 頂層 studio | 欄位狀態 `unique` 才可寫 |
| Sub-Studio／Label | 子 studio | 只有 `label_is_publisher=true` 才建 studio |
| 非發行主體 Label | 別名表 | 不建 studio，不建 tag |
| Series | tag，可有系列父 tag | 欄位狀態 `unique` 才可寫；不得放入 studio 樹 |
| 品番 | scene `code` | 寫完整品番。只在 `code` 為空時寫入 |
| 跨站其他品番 | custom field | V1.0 只保存，不做等價運算 |
| 前綴、表版本、信心、`needs_review` | custom field | 只供稽核與續跑，不作主篩選 |

同一 canonical Label MUST NOT 同時存在於 studio 與 tag。

Studio 深度跟隨實際發行主體，不設任意上限。兩層是預設與驗證起點，不是天花板。大於兩層的鏈在寫入前，MUST 先在目標實機證明 include child studios 於該深度有效。此驗證不得阻擋兩層以內的寫入，也不得阻擋 Phase 0 或 Doctor。

歷史出處可引用：Stash v0.8.0（2021-07-02）release note 列有 “Support Studio filter including child studios. (#1397)”。該出處不證明目前安裝版的多層深度。

Custom field 名稱：

- `prefix_suite_prefix`
- `prefix_suite_table_version`
- `prefix_suite_confidence`
- `prefix_suite_needs_review`
- `prefix_suite_alt_codes`

發行主體 Label 的自動建 studio，MUST 在變更計畫 CSV 以獨立動作 `create studio` 列出。dry-run 不得真正建立 studio。

## 4. 表

### 4.1 前綴表

唯一鍵是 `id`（`source_site:match`），不是 prefix 本身。

```json
{
  "id": "hunkch:GV-DSK",
  "source_site": "hunk-ch.com",
  "match": {"kind": "prefix", "value": "GV-DSK", "priority": 20},
  "studio": "G＠MES",
  "sub_studio": null,
  "label": null,
  "label_is_publisher": false,
  "series": "筋肉雄マラ大失禁!!",
  "ambiguous_fields": [],
  "title_hints": ["大失禁"]
}
```

必填：`id`、`source_site`、`match.value`、`match.priority`、`studio`、`label_is_publisher`、`ambiguous_fields`。

`KKE` 這類列可以 `studio` 唯一，同時把 `series` 列入 `ambiguous_fields`。MUST NOT 使用列級 `ambiguous` 布林，也 MUST NOT 規定歧義列不得有唯一 series。

查表：最長前綴優先。同長度才看 `priority`。`GV-DSK` 必須勝於 `GV-`。

### 4.2 別名表與正規化

二者分檔、分層、各自版控，不得寫死在程式裡。

- 正規化：全形半形、大小寫、空白與分隔符等價。
- 別名表：真正的名稱變體，例如 `KO-EAST` → `KO East`。

分流判準只使用這兩層，不得另做 fuzzy collapse。

### 4.3 載入期驗證

失敗即停止 task，不准帶病跑全庫。同一 validator 進 CI。

MUST 失敗：

- 同一 `source_site + match.value` 指向不同 studio。不同站的相同字串不得因此失敗。
- 站別 pattern 註冊表宣告該站有結構化第二段碼，且已知系列碼只會落到較短前綴。
- `ambiguous_fields` 的值不在允許欄位內，或與可寫判定矛盾。
- 同一 studio 的 canonical 拼法不一致。
- 孤兒系列：series 有名稱，但沒有唯一值或候選定義。

MUST NOT 失敗：

- 長前綴存在而短前綴不存在。`GV-DSK` 不要求 `GV-` 存在。

golden set MUST 包含這個失敗模式：短前綴帶有唯一 series、較長列缺失時，`GV-DSK10004` 不得落到 `GV-` 並取得該 series。

### 4.4 品番級映射表

不是 V1.0 交付物。

只有同時具備品番、所屬系列、來源頁與抓取日期，才可另案提前。缺任一項就是新爬蟲專案。沒有來源與抓取日期的號段表 MUST NOT 建立。

### 4.5 治理

設定頁顯示表版本，並產出 added／changed／removed diff。

V1.0 只輸出 unknown-prefix 待審清單。MUST NOT 自動寫回表。

## 5. 提取與解析

### 5.1 來源順序

1. `files[].basename`
2. scene URL
3. title
4. 路徑資料夾名
5. `unextractable`

查不到就報告，不猜，不做全庫模糊搜尋。

### 5.2 比對

兩段式：先抽候選 token，再做最長前綴查表。不得使用一把 mega-regex。

站別 pattern 優先。通用 `[A-Z]+-?\d+` 只可做低分 fallback，且必須有詞邊界。排除至少包含 `1080p`、`720p`、`4K`、`x264`、`x265`、`MP4` 與 `20xx` 日期。

匹配前先正規化。`ＷＩＧ-123`、`wig_123`、`WIG123` 必須落到 `WIG`。

多候選時取最長且查得到表的一個。查無表的候選不得當成確定品番。

### 5.3 Resolver

每個欄位只允許 `unique`、`ambiguous`、`absent`。

標題關鍵字、既有 tag、既有 studio 只可加分與排序。MUST NOT 因超過閾值把 `ambiguous` 改成 `unique`。V1.0 不使用 performer。

### 5.4 測試

前綴表涵蓋的每一站都要有五類樣本：命中、雜訊、分隔符變體、一對多、無品番。另加 §4.3 的短前綴靜默錯填案例。改 regex 或改表，CI 必須全綠。

## 6. 寫入政策

| 欄位狀態 | Enrich | Normalize | Doctor |
|---|---|---|---|
| `unique` 且目標為空 | 可寫 | 不適用 | 列入可填清單 |
| `unique` 且現值是別名或正規化後同一 canonical | 不覆寫非空值 | 可改成 canonical | 列入別名差異 |
| `unique` 且現值為語意衝突 | 不寫 | 不寫 | 列入人工批次 |
| `ambiguous` | 不寫該欄位 | 不寫該欄位 | 只提案 |
| `absent`／`unextractable` | 不猜 | 不猜 | 列入未命中 |

機械分流，供 CI 使用：

- 現值出現在別名表，或經 §4.2 正規化後與推導值同屬一個 canonical：別名差異。
- 其餘一律語意衝突。
- 不得在這兩層之外留人工分流。

`unique` 是欄位級。`KKE` 可寫 studio，不可寫 series。`GV-DSK` 的 series 唯一時 MUST 可寫。發行主體 Label 唯一時可建子 studio，但必須先出現在 `create studio` 列。

禁止「用第一個」。Enrich MUST 只填空。Normalize 只做別名收斂。

## 7. 衝突抽樣

第一次 Enrich 前 MUST 抽樣 Doctor 差異 CSV。不另定衝突率百分比。

| 抽樣結論 | 動作 |
|---|---|
| 該前綴的表是錯的 | 先修表。該前綴隔離，不得 Enrich |
| 該前綴的庫是錯的 | 已通過抽樣的前綴仍可填空。語意衝突進人工確認批次，不得進 Normalize |
| 只有別名差異 | 交給 Normalize |

不得因單一前綴未通過而阻擋其他已通過前綴。這是停查，不是歸責，也不是整段死鎖。

## 8. Tasks

使用者必須分別啟動。任一 task 失敗不得自動啟動下一個。

### 8.1 Doctor

只讀。不寫 scene、studio、tag 或檔案。這是第一個對媒體庫的里程碑。

掃描範圍 MUST 包含 Studio 為空的 scene。已有 Studio 的比對只是差異 CSV 的一部分。

報告 MUST 並列兩個數字，且不得產生自動建議：

- 唯一命中衝突率：給人判斷是否信任該前綴的表。
- 覆蓋率：給人判斷是否開放 Rename。

50% 只是覆蓋率的暫定參考線，不是軟體閘門，不是補表訊號，也不是第二個待首跑後才制定的百分比門檻。敘事文字放在數字之後，並標成人工詮釋區。

另產出：

- 五類計數：可提取、表命中、一對多、與現值衝突、無訊號。
- unknown-prefix 清單。
- 非發行主體 label 清單與各自 scene 數。沒有這份統計，不得重開 tag 路線。
- sidecar 附帶比例。只供評估跳過影響，不改變預設跳過。
- 同 code、同 URL 兩份唯讀清單。不建等價，不含標題相似度，不建議合併。

### 8.2 Enrich

只填空值。可寫範圍是 `unique` 的 studio、series、發行主體 Label，以及空的 `code` 與稽核欄位。

先出完整變更計畫 CSV，抽查後才分批 apply。`create studio` 必須是獨立列。報告已填、需人工、查無前綴三個計數。

### 8.3 Normalize

只依別名表與 §4.2 正規化統一名稱。dry-run 預設開啟。

驗收是實際寫入與別名 diff 一致。未收錄寫法留在報告，作為別名表下一版的輸入。MUST NOT 為了全綠而改語意衝突。

### 8.4 Rename

V1.0 可註冊，預設 disabled。以下任一不滿足即拒絕執行：

- 本次有第二次明確確認。
- 已存在 50 筆完整 cycle 驗收記錄。
- 該 scene 的路徑欄位為 `unique`，且沒有 `needs_review`。

覆蓋率數字不得由程式自動拒絕或自動放行 Rename。是否開放由人看 Doctor 報告決定。

plugin 只產出新路徑。搬移只用 Stash `moveFiles`。MUST NOT 呼叫 `os.rename` 或 `os.replace`。

預設模板：

```text
{Studio}/{Sub-Studio}/{Label}/{品番} {標題}.{ext}
```

模板必須含品番或 scene id。空 title、空必填 studio，或資料值含路徑分隔符的該筆拒絕執行。空的可選層 MUST 省略，不得製造空資料夾。

### 8.5 clean_empty_dirs

獨立 task，預設 disabled。Rename MUST NOT 自動呼叫它。

路徑只能取自 journal，不得是 library root，不得跑全庫 Clean。真刪前 MUST 先以 `metadataClean` 的 `dryRun: true` 執行並由人比對輸出。啟動時 MUST 確認目前 schema 支援 `paths` 與 `dryRun`。不支援則拒絕執行，不得自行刪檔。

## 9. Rename 與 sidecar

1. 目標已存在則中止該筆。V1.0 不加後綴，不覆寫。
2. 執行前寫 JSONL：`scene_id`、`file_id`、`old_path`、`new_path`、`fingerprint`。有 sidecar 而跳過時，journal 同時記錄 sidecar 路徑與跳過原因。
3. 目標只能在 library root 內，不跨 library root，不跨磁碟。
4. 依 UTF-8 byte 截斷。處理 Windows 260 字元上限、保留名與 NFC。路徑分隔符只能來自模板。
5. 多 file scene 預設跳過。偵測到同名 sidecar 的 scene 預設整筆跳過。V1.0 不得提供「搬影片、留 sidecar」。後續版本若要支援，唯一允許的行為是 sidecar 同步改名並同搬；規格只寫行為。
6. 生成檔不改名。
7. 空目錄只記 journal。
8. 放量前先單檔，再 50 筆完整 cycle：rename、scan、比對。無重複 scene、無孤兒、DB 路徑已同步，才可擴大。
9. 執行前備份 SQLite。備份寫在操作文件，不做成 plugin 功能。

## 10. 批次

- 用 plugin progress 回報，並檢查取消。報告寫檔，不只寫進 Stash log。
- 先批次讀取 id、path、studio、tags、code、URL，再只對有 diff 的 scene 逐筆 mutation。
- 以 scene id 為游標。MUST NOT 用 offset。
- 不得覆寫未讀取的關聯欄位。
- checkpoint 記錄 `last_id`。不得自包跨 mutation 交易。
- 批量執行期間停用 enrich hook。
- task 開頭檢查 Python import。失敗則明確報錯。
- 設定用 `find_plugin_config()` 帶預設值。不得要求使用者手改設定檔才能首次啟動。

## 11. 設定

- 表版本、diff、手動更新。
- 各 task 獨立開關。Rename 與 `clean_empty_dirs` 預設關。
- 全域 dry-run 預設開。
- Rename 模板檢查。
- 排除路徑，以及只跑指定 studio。
- 批次大小，預設 50–100。
- 不提供「用第一個」。
- 不提供「sidecar 留在原地」。

## 12. 階段

| Phase | 內容 | 阻擋 | 驗收 |
|---|---|---|---|
| 0 | 表、validator、CI、extractor、resolver、golden set | 無 | pytest 全綠。validator 不得實作「短前綴必須存在」 |
| 1 | Doctor 與全部唯讀報告 | 無 | 含空 Studio。兩數字並列且無自動建議 |
| 2 | Enrich | 第一次執行前完成 §7 抽樣。大於兩層的鏈另需實機驗證 | 變更計畫含 `create studio`。抽查無誤寫 |
| 3 | Normalize | 無 | 寫入與別名 diff 一致 |
| 4 | Rename | §8.4 三項執行閘門，加上人已決定開放 | 50 筆無重複、無孤兒；JSONL 可對帳 |

Phase 0 不受附錄、changelog、實機驗證、repo 名稱或簽章 URL 阻擋。

## 13. 不在 V1.0

- 跨站等價表。等價關係必須有來源 URL，不得由標題相似度生成。
- 單筆 hook enrich。
- sidecar 同步同搬。
- 品番級映射表。
- 自動把待審前綴寫回表。
- scene 頁 JS diff。

## 14. 尚未由規格決定的事實

這些不是未定案的設計，只是尚未核對的外部事實：

- 遠端 repo 是否就叫 `stash-scarpers`。
- 品番級原始資料是否仍在。
- 目標 Stash 的多層 include child studios 行為。
- 目標版本是否支援 `moveFiles`，以及 `metadataClean` 的 `paths` 與 `dryRun`。
- scene custom field 在實機上的篩選穩定性。稽核欄位不依賴該篩選。

`response_KimiK3.md` 的簽章 URL 只阻擋公開分享，不阻擋私人開發。
