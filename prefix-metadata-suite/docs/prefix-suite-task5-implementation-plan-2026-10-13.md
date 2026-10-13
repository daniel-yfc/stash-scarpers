# Task 5 Source Enrich — 開發計畫

- 日期：2026-10-13
- 依據：`prefix-suite-task5-spec-V2.0-2026-10-13.md`
- 前置：Phase 0–4 完成（沿用 `prefix-suite-implementation-plan-2026-10-12.md`）

## 目錄結構（新增）

```
prefix-metadata-suite/
├── alias-table.json            # 已存在（Task 3 建立）
├── learned-candidates.json     # 新增：別名學習候選
├── scrapers/
│   └── GVDB.yml                # 新增：第 18 個 scraper
├── tasks/
│   └── source_enrich.py        # 新增：Task 5 主程式
│       ├── phase_a_alias.py    # 別名正規化
│       ├── phase_b_query.py    # 多源查詢
│       └── phase_c_merge.py    # 合併寫入
├── tests/
│   ├── test_alias.py           # 新增
│   ├── test_source_enrich.py   # 新增
│   └── golden/
│       └── task5/              # 新增：每種衝突類型的 golden case
└── plugin.yml                  # 更新：加入 task5 定義
```

## Phase 5.0：別名基礎設施

| # | Task | 內容 | 工作量 | 產出 |
|---|------|------|--------|------|
| 5.0.1 | `learned-candidates.json` 結構 | 定義候選格式＋確認流程（人工確認後寫入 `alias-table.json`） | S | 結構定義＋讀寫函式 |
| 5.0.2 | 別名反向索引 | `canonical` → `alias→canonical` 反向查詢，O(1) | S | `alias.py` |
| 5.0.3 | 別名學習規則 | 同一 Code 在不同站對應不同演員名 → 記錄候選。定義「同一」的判定（Code 完全一致） | M | 學習函式＋測試 |

**驗收**：`pytest tests/test_alias.py` 全綠。

## Phase 5.1：GVDB Scraper

| # | Task | 內容 | 工作量 | 產出 |
|---|------|------|--------|------|
| 5.1.1 | GVDB 站點調查 | 用 browser 確認：演員頁 URL pattern、別名欄位、filmography 結構、影片頁欄位、rate limit | M（browser） | 調查報告 |
| 5.1.2 | `GVDB.yml` | `sceneByName`、`performerByName`、`sceneByURL`、`performerByURL`。只做已驗證的 mode | M | `GVDB.yml` |
| 5.1.3 | Validator＋測試 | 跑官方 validator＋quality gate；錄製 test fixture | S | `GVDB.test.yaml` |

**驗收**：validator 通過；至少 3 個演員頁＋3 個影片頁手動驗證。

**風險**：GVDB 無公開 API，若站點結構複雜或反爬，降級為「僅手動匯入別名表」，不阻塞 5.2。

## Phase 5.2：三階段主流程

| # | Task | 內容 | 工作量 | 產出 |
|---|------|------|--------|------|
| 5.2.1 | Phase A 別名正規化 | `phase_a_alias.py`：讀 scene performers → 查表 → 回傳正規化後的名單＋`alias_resolved` 旗標 | S | `phase_a_alias.py` |
| 5.2.2 | Phase B 多源查詢框架 | `phase_b_query.py`：來源註冊表、優先順序排序、超時控制（30s/source）、結果標準化為 `{field, value, confidence, source, source_type}` | M | `phase_b_query.py` |
| 5.2.3 | Phase B 來源適配器 | 為每種 source 寫適配器：`prefix_site`（Code 直查）、`group_site`、`gvdb`（performer filmography）、`other_sites`（Title 模糊） | M | 4 個適配器 |
| 5.2.4 | Phase C 合併寫入 | `phase_c_merge.py`：實作 §4.3 寫入政策表；變更計畫 CSV 生成；分批 mutation；稽核 JSONL | M | `phase_c_merge.py` |
| 5.2.5 | `tasks/source_enrich.py` 主程式 | 串起三個 Phase；Phase 間失敗隔離；progress 回報；checkpoint 續跑 | M | `source_enrich.py` |

**驗收**：在 100 個測試 scene 上跑 dry-run，變更計畫 CSV 人工抽查無誤。

## Phase 5.3：設定頁＋Plugin 整合

| # | Task | 內容 | 工作量 | 產出 |
|---|------|------|--------|------|
| 5.3.1 | `plugin.yml` 更新 | 加入 task5 定義：開關、dry-run、來源排序、欄位開關、信心分數、GVDB 設定、別名學習開關 | S | `plugin.yml` |
| 5.3.2 | 設定頁 UI | 來源拖曳排序、8 個欄位 checkbox、信心分數滑桿、別名表查看器 | M | 前端設定頁 |
| 5.3.3 | 別名管理 UI | 查看正式表、查看候選、一鍵確認／拒絕候選 | M | 別名管理頁 |

**驗收**：5 個 task 在 Stash UI 可獨立啟動、獨立 dry-run。

## Phase 5.4：測試＋文件

| # | Task | 內容 | 工作量 | 產出 |
|---|------|------|--------|------|
| 5.4.1 | Golden tests | 每種情況：單源命中、多源一致、多源衝突、別名命中、別名未命中、超時跳過、空值跳過 | M | `tests/golden/task5/` |
| 5.4.2 | 整合測試 | 端到端 dry-run（100 scenes）→ 檢查 CSV → live（10 scenes）→ 驗證 DB | M | 測試報告 |
| 5.4.3 | 文件 | 更新主規格書的 Task 5 章節；寫使用者手冊（設定頁說明） | S | 文件 |

## 工作量總覽

| Phase | 內容 | 估計 |
|-------|------|------|
| 5.0 | 別名基礎設施 | 2 天 |
| 5.1 | GVDB Scraper | 3–4 天（含 browser 調查） |
| 5.2 | 三階段主流程 | 5–6 天 |
| 5.3 | 設定頁＋Plugin 整合 | 3–4 天 |
| 5.4 | 測試＋文件 | 2–3 天 |
| **合計** | | **約 15–19 工作天** |

## 關鍵路徑

```
5.1.1 GVDB 調查 ─┐
                 ├→ 5.1.2 GVDB.yml → 5.2.3 gvdb 適配器
5.0.1/5.0.2 ─────┘
  → 5.2.1 Phase A → 5.2.2 查詢框架 → 5.2.4 合併寫入 → 5.2.5 主程式
  → 5.3 plugin 整合 → 5.4 測試
```

**最長阻塞點**：5.1.1 GVDB 調查（若站點反爬，啟用降級方案）。

## 風險與緩解

| 風險 | 機率 | 緩解 |
|------|------|------|
| GVDB 結構複雜或反爬 | 中 | 降級為手動匯入別名表；Task 5 不依賴 GVDB 也可運行 |
| 多源查詢太慢（16k scenes） | 高 | 預設只跑「有 Code 但缺欄位」的 scene；分批＋checkpoint；單 source 30s 超時 |
| 別名表初始太小，Phase A 命中率低 | 中 | 先從 GVDB 匯入；學習功能預設關閉，人工確認後才生效 |
| 信心分數調校困難 | 低 | 先用預設值跑 dry-run，看人工確認批次的品質再調 |

## 與 V1.0 計畫的銜接

- V1.0 的 Phase 0–4 不變，Task 5 是新增的 Phase 5。
- `alias-table.json` 已在 Task 3 建立，Task 5 直接沿用。
- 稽核 JSONL 格式沿用修正案（`reports/audit-{task}-{ts}.jsonl`）。
- 5 個 task 共用 `plugin.yml`，不拆分（沿用 V1.0 §2）。

---

*文件版本：2026-10-13。依據 `prefix-suite-task5-spec-V2.0-2026-10-13.md` 展開。*
