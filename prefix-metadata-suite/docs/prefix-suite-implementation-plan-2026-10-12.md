# Prefix Metadata Suite — 規格審查與實作展開

## 第一部分：規格可執行性審查

### ✅ 規格中紮實、可直接執行的部分

| 條文 | 評估 |
|------|------|
| Phase 0–4 階段劃分（§12） | 清晰，每階段有明確驗收標準，無循環依賴 |
| extractor／resolver 純函式＋pytest（§2） | 可執行；與 Stash 解耦的設計正確 |
| 最長前綴優先查表（§4.1） | 明確，trie 或排序比對皆可實作 |
| 載入期驗證規則（§4.3） | 具體可測，可直接轉成 validator 函式 |
| 欄位狀態機 unique／ambiguous／absent（§5.3、§6） | 明確，寫入政策表可直接轉成程式分支 |
| 批次策略：scene id 游標、50–100 筆、單執行緒（§10） | 務實，避開 offset 效能坑 |
| Rename 閘門（§8.4）＋ JSONL journal（§9） | 保守但正確，符合檔案操作的最佳實務 |

### ⚠️ 執行前必須先確認的外部事實（規格 §14 已列出，補充影響）

**✅ 已於 2026-10-12 實機探測（Stash v0.31.1，經 Tailscale）：**

| 事實 | 結果 |
|------|------|
| `moveFiles` | ✅ 支援（`MoveFilesInput` 存在） |
| `metadataClean` 的 `paths`＋`dryRun` | ✅ 支援（`CleanMetadataInput` 含兩者） |
| scene custom field | ❌ **不支援**（`Scene` type 無 `customFields`）→ 稽核欄位改存外部 JSONL journal |
| 多層 studio 的 include child studios 行為 | 未驗證，兩層內不影響 |

**關鍵發現**：13,606／16,374 scenes（83%）無 studio，Enrich 價值極大。

**規格修正**：§3 的稽核欄位（`prefix_suite_prefix`、`prefix_suite_table_version`、`prefix_suite_confidence`、`prefix_suite_needs_review`、`prefix_suite_alt_codes`）**不得寫入 Stash**，改為每次 task 執行時寫入 `reports/audit-{task}-{timestamp}.jsonl`，以 `scene_id` 為鍵。`needs_review` 的續跑改為讀取上次 journal 而非查詢 custom field。

### 🔍 規格中的潛在缺口（建議補）

1. **前綴表 JSON 的生成流程未定義**：規格定義了 JSON schema（§4.1），但沒說我們現有的 500 行 Markdown 表如何轉成 JSON。需要一個 `md_to_json.py` 轉換腳本＋人工審核 `label_is_publisher`（這是關鍵欄位，機器無法自動判斷）。
2. **`title_hints` 的用途未展開**：§4.1 範例有 `title_hints: ["大失禁"]`，但 §5.3 只說標題關鍵字「可加分排序」。加分算法未定義 → 建議 Phase 0 先定義為「僅用於人工確認批次的排序提示，不影響 unique／ambiguous 判定」（與 §5.3 的 MUST NOT 一致）。
3. **別名表初始內容為空**：正規化規則（§4.2）可程式化，但別名表需要從現有 Stash 庫的實際髒資料長出來。建議 Phase 3 開始前先跑一個「別名採礦」腳本：列出所有 studio 名稱的變體候選，人工確認後寫入。
4. **site-patterns.json 的初始內容**：需要為每站定義 pattern。我們有 6 站的掃描經驗，可直接寫第一版。

### 總結論：規格可執行

邏輯自洽，無矛盾條文（抽查了 MUST／MUST NOT 的交叉引用）。唯一需要補的是「Markdown 表 → JSON」的轉換流程，這是 Phase 0 的第一個 task。

---

## 第二部分：實作展開

### 目錄結構

```
prefix-metadata-suite/
├── prefix-table/
│   ├── games.json
│   ├── koshop.json
│   ├── hunkch.json
│   ├── mensrushtv.json
│   ├── ckdownload.json
│   ├── coat.json
│   ├── acceed.json
│   └── _meta.json              # 表版本、生成日期、來源
├── aliases.json                # 別名表
├── site-patterns.json          # 站別 pattern＋第二段碼註冊表
├── extractor.py                # 純函式：文本 → 品番候選
├── resolver.py                 # 純函式：品番 → 欄位狀態
├── validator.py                # 載入期驗證（§4.3）
├── md_to_json.py               # Markdown 總表 → JSON（一次性＋可重跑）
├── tasks/
│   ├── doctor.py
│   ├── enrich.py
│   ├── normalize.py
│   ├── rename.py
│   └── clean_empty_dirs.py
├── tests/
│   ├── test_extractor.py
│   ├── test_resolver.py
│   ├── test_validator.py
│   └── golden/                 # golden set（含短前綴靜默錯填案例）
├── reports/                    # 產出目錄（CSV、差異報告、audit JSONL journal）
│   └── audit-{task}-{timestamp}.jsonl  # 稽核欄位（Scene 無 customFields，改存外部）
├── plugin.yml                  # Stash plugin 描述檔
└── .github/workflows/ci.yml    # pytest＋validator
```

### Phase 0：基礎建設

**目標**：表、validator、CI、extractor、resolver、golden set 全部 pytest 全綠。

| # | Task | 內容 | 工作量 | 產出 |
|---|------|------|--------|------|
| 0.1 | 環境探測腳本 | 檢測目標 Stash 版本：`moveFiles`、custom field、`metadataClean` paths/dryRun、多層 studio 行為。輸出報告 | S | `probe.py`＋報告 |
| 0.2 | Markdown → JSON 轉換 | `md_to_json.py`：解析五欄總表，生成每站 JSON。`id` = `{site}:{prefix}`，`match.priority` 預設 20，`ambiguous_fields` 標記一對多（如 KKE 的 series） | M | 7 個站 JSON＋`_meta.json` |
| 0.3 | `label_is_publisher` 人工標註 | 逐站判斷每個 Label 是否為發行主體。這是機器做不了的，需要人看。約 500 行，預估 2–3 小時人工 | M（人工） | 標註完成的 JSON |
| 0.4 | `site-patterns.json` 第一版 | 為 6 站定義提取 pattern＋第二段碼註冊表（如 G＠MES 的 DSK／OND／THT） | S | `site-patterns.json` |
| 0.5 | `aliases.json` 第一版 | 從已知變體建立（如 KO-EAST→KO East）。先放 10–20 個已知，Phase 3 再擴充 | S | `aliases.json` |
| 0.6 | `extractor.py` | 兩段式提取：token 化 → 最長前綴查表。來源順序：basename→URL→title→資料夾。排除 1080p／x264／日期等雜訊。正規化全形半形 | M | `extractor.py` |
| 0.7 | `resolver.py` | 品番 → 每欄位 `unique`／`ambiguous`／`absent`。實作 §6 寫入政策表 | M | `resolver.py` |
| 0.8 | `validator.py`（載入期） | 實作 §4.3 的 MUST 失敗／MUST NOT 失敗規則 | M | `validator.py` |
| 0.9 | Golden set＋CI | 每站五類樣本（命中、雜訊、分隔符變體、一對多、無品番）＋短前綴靜默錯填案例。GitHub Actions 跑 pytest＋validator | M | `tests/`＋`ci.yml` |
| 0.10 | `plugin.yml`＋空 task 殼 | Stash plugin 描述檔，四個 task 的參數定義（開關、dry-run、批次大小），先不接實作 | S | `plugin.yml` |

**Phase 0 驗收**：`pytest` 全綠；`validator.py` 對故意放錯的表能正確失敗；CI 綠燈。

**工作量估計**：約 5–7 天（含 0.3 的人工標註）。

### Phase 1：Doctor（唯讀）

**目標**：對媒體庫跑第一次唯讀掃描，產出差異報告。**不寫入任何東西**。

| # | Task | 內容 | 工作量 |
|---|------|------|--------|
| 1.1 | Stash GraphQL 讀取層 | 分批讀取 scenes（id、path、studio、tags、code、URL），scene id 游標，每批 50–100 | M |
| 1.2 | `tasks/doctor.py` 主流程 | 對每個 scene：extractor→resolver→比對現值→寫入差異 CSV。範圍包含 Studio 為空的 scene | M |
| 1.3 | 報告生成 | 兩個並列數字（唯一命中衝突率、覆蓋率）＋五類計數＋unknown-prefix 清單＋非發行主體 label 統計＋同 code／同 URL 清單。**不產生自動建議** | M |
| 1.4 | Progress＋取消＋checkpoint | plugin progress 回報、可中斷、`last_id` 續跑 | S |

**Phase 1 驗收**：在測試庫跑完，報告數字合理；重跑可從 checkpoint 續行。

**工作量估計**：約 3–4 天。

### Phase 2：Enrich（有限寫入）

**前置條件**：完成 §7 衝突抽樣（人工看 Doctor 差異 CSV，判斷是表錯還是庫錯）。

| # | Task | 內容 | 工作量 |
|---|------|------|--------|
| 2.1 | 變更計畫生成 | 先出完整 CSV（含 `create studio` 獨立列），人工抽查 | M |
| 2.2 | `tasks/enrich.py` | 只填空值：`unique` 的 studio／series／發行主體 Label、空的 `code`。稽核資訊（prefix、表版本、信心、`needs_review`）寫入 `reports/audit-enrich-{ts}.jsonl`（Scene 無 customFields）。分批 mutation | M |
| 2.3 | 報告 | 已填／需人工／查無前綴三個計數 | S |

**Phase 2 驗收**：變更計畫經人工抽查無誤；寫入後抽查 DB 一致。

**工作量估計**：約 3 天（不含人工抽樣時間）。

### Phase 3：Normalize

| # | Task | 內容 | 工作量 |
|---|------|------|--------|
| 3.1 | 別名採礦 | 從庫中實際 studio 名稱列出變體候選，人工確認後寫入 `aliases.json` | M（含人工） |
| 3.2 | `tasks/normalize.py` | 只依別名表＋正規化規則統一名稱。dry-run 預設開 | S |
| 3.3 | 驗收 | 寫入結果與別名 diff 一致；未收錄寫法留報告 | S |

**工作量估計**：約 2 天。

### Phase 4：Rename（重度閘門）

**前置條件**（§8.4，缺一不可）：
1. 第二次明確人工確認
2. 50 筆完整 cycle 驗收記錄（rename→scan→比對，無重複、無孤兒、DB 路徑同步）
3. 該 scene 路徑欄位為 `unique` 且無 `needs_review`

| # | Task | 內容 | 工作量 |
|---|------|------|--------|
| 4.1 | 路徑生成＋驗證 | 按模板生成新路徑；檢查：library root 內、無非法字元、Windows 260 上限、UTF-8 byte 截斷、目標不存在 | M |
| 4.2 | JSONL journal | 執行前寫 `scene_id`、`file_id`、`old_path`、`new_path`、`fingerprint` | S |
| 4.3 | `tasks/rename.py` | 只用 Stash `moveFiles`；多 file scene 跳過；有 sidecar 跳過；生成檔不改名。執行前備份 SQLite（文件說明） | M |
| 4.4 | `tasks/clean_empty_dirs.py` | 獨立 task，預設 disabled。路徑只取自 journal，用 `metadataClean(dryRun: true)` 先比對 | M |

**工作量估計**：約 4–5 天（含 50 筆驗收的人工時間）。

---

## 第三部分：總工作量與路徑

### 工作量總覽

| Phase | 內容 | 估計 |
|-------|------|------|
| 0 | 基礎建設（表轉換、extractor、resolver、validator、CI） | 5–7 天 |
| 1 | Doctor 唯讀掃描＋報告 | 3–4 天 |
| 2 | Enrich 有限寫入 | 3 天 |
| 3 | Normalize | 2 天 |
| 4 | Rename＋clean_empty_dirs | 4–5 天 |
| **合計** | | **約 17–21 工作天** |

*註：估計為單人開發，含測試。不含人工抽樣／標註的等待時間。*

### 關鍵路徑

```
0.1 環境探測
  → 0.2 表轉換 → 0.3 人工標註 label_is_publisher ← 最長的人工阻塞點
  → 0.6/0.7 extractor＋resolver → 0.8 validator → 0.9 golden＋CI
  → Phase 0 驗收
  → Phase 1 Doctor → 人工看報告
  → §7 衝突抽樣（人工）← 第二個人工阻塞點
  → Phase 2 Enrich → Phase 3 Normalize
  → 50 筆 Rename 驗收（人工）← 第三個人工阻塞點
  → Phase 4 Rename
```

### 風險與緩解

| 風險 | 機率 | 緩解 |
|------|------|------|
| `label_is_publisher` 人工標註耗時超預期 | 中 | 先標註高頻 Label（覆蓋 80% scene 的前 20%），低頻延後 |
| 目標 Stash 版本不支援 `moveFiles` | 低 | 0.1 探測先確認；不支援則 Phase 4 整段擱置，不影響前三階段 |
| 品番提取率低（使用者自訂檔名） | 中 | Doctor 報告的「無訊號」比例會先揭露；低於預期則先補表或調整 pattern，不硬寫 |
| 一對多前綴（如 KKE）佔比過高 | 低 | 規格已規定只填 studio 不填 series；影響有限 |

### 建議的啟動順序

1. **先跑 0.1**（環境探測，半天）：確認四個外部事實，避免白做工。
2. **0.2＋0.3 並行啟動**：轉換腳本寫完就丟著跑，人工標註同步進行。
3. **0.6／0.7／0.8 是核心**：extractor＋resolver＋validator 的品質決定整個專案的上限，多花時間寫 golden test 值得。

---

*文件版本：2026-10-12。依據 `prefix-metadata-suite-spec-V1.0-2026-10-12.md`（Grok 4.7）展開。*
