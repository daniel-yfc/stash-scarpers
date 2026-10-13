# Prefix Metadata Suite（Tasks 1–4）

依據版本化前綴表（`prefix-table/`），從檔名前綴自動填入、驗證、標準化 Stash Scene 的 Studio／Code。現階段為獨立腳本，尚未打包成 Stash plugin（尚無 `plugin.yml`、設定頁）。Task 5（Source Enrich）僅有設計文件，不在本目錄。

## Tasks

| # | 腳本 | 行為 |
|---|------|------|
| 1 | `tasks/doctor.py` | 唯讀診斷：比對現有 Studio 與前綴解析結果，寫 audit journal＋CSV |
| 2 | `tasks/enrich.py` | 只填空值：Studio／Code，依 Label → Series → Sub-Studio → Studio 順序取值 |
| 3 | `tasks/normalize.py` | 依 `alias-table.json` 把 Studio 更名為正規名稱（同 ID 改名，真重複列衝突） |
| 4 | `tasks/rename.py` | 依模板搬移檔案（Stash `moveFiles`），高度設防 |

`tasks/fix_miswritten_studios.py` 是一次性修復腳本（修 2026-10-12 live enrich 被錯誤 resolver 寫錯的 Studio），非例行 task。

## 設定

Stash 位址由環境變數提供，預設為本機 placeholder：

```sh
export STASH_URL="http://<your-stash-host>:9999/graphql"
```

腳本會讀 `HTTPS_PROXY`（如有）。公開 repo 內不得放真實 Stash 位址或憑證。

## 使用

```sh
cd prefix-metadata-suite
python3 tasks/doctor.py            # 唯讀，可先看報告
python3 tasks/enrich.py            # 預設 dry-run
python3 tasks/enrich.py --live     # 實際寫入（寫入前請先看 dry-run 報告）
```

## 資料與工具

- `prefix-table/*.json`：每站前綴 → Studio／Sub-Studio／Label／Series 對應表（含 `_meta.json` 表版本）。
- `alias-table.json`：正規 Studio 名稱 ↔ 別名。
- `extractor.py`／`resolver.py`：純函式（品番提取、前綴解析），測試見 `tests/test_extractor_resolver.py`。
- `md_to_json.py`／`sync_md_from_json.py`：五欄 MD 總表 ↔ JSON 的轉換／增量同步（MD 總表本身不在 repo 內）。
- `docs/`：V1.0 規格書、實作計畫、修正案。
- `reports/`：各 task 執行時產生的 audit journal／CSV，屬於本地執行產出，不進版控。
