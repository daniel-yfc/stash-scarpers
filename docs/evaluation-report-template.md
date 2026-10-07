# 本機評估報告模板

獨立的本機完整測試評估報告格式。每次執行 `bash tools/run-all-checks.sh`
後，依此模板產出報告。

> 執行順序與依賴關係見 `tools/run-all-checks.sh` 檔頭註解。
> 線上 CI 流程見 `docs/05_CI_Workflows.md`。

---

## 1. 報告標頭

| 項目        | 內容                                                   |
| ----------- | ------------------------------------------------------ |
| 報告日期    | YYYY-MM-DD HH:MM (時區)                                |
| 執行者      |                                                        |
| Repo commit | `hash`（分支：`main`）                                 |
| 執行環境    | OS / Node 版本 / Python 版本                           |
| 執行方式    | `bash tools/run-all-checks.sh --all`（或註明互動選項） |
| 總 verdict  | ✅ 通過 / ❌ 失敗                                      |

---

## 2. 層級結果矩陣

依執行順序列出每層結果。狀態僅允許：通過 / 失敗 / 警告 / 跳過。

| 層級 | 名稱                | 依賴   | 狀態 | 耗時 | 備註                                 |
| ---- | ------------------- | ------ | ---- | ---- | ------------------------------------ |
| L0   | YAML 解析           | —      |      |      | 失敗則中止後續                       |
| L1   | Schema 驗證         | L0     |      |      | `validator -a --ci`                  |
| L2   | URL 排序檢查        | L1     |      |      | `validator -a -s --ci`               |
| L3   | Quality Gate 全站   | L1     |      |      | 16 scraper 逐檔                      |
| L4   | Scraper 語義檢查    | L0     |      |      | Gender enum、movieByURL、parseDate   |
| L5   | 文件-vs-Schema 對齊 | —      |      |      | entity 欄位、entry points、operators |
| L6   | Scraper 文件檢查    | —      |      |      | 內嵌 YAML 範例                       |
| L7   | 文件索引檢查        | —      |      |      | index.yml 43 documents               |
| L8   | Fixture Runner 自測 | —      |      |      | 1 正 6 負                            |
| L9   | 機密資料掃描        | —      |      |      |                                      |
| L10  | 證據標籤檢查        | —      |      |      |                                      |
| L11  | Pytest 完整套件     | L1–L10 |      |      | 最終閘門                             |
| L12  | 程式碼格式檢查      | —      |      |      | 建議性，不影響 verdict               |

**通過率**：通過 __ / 12（L12 警告不計入失敗）

---

## 3. 失敗與警告明細

每個失敗或警告一列。若無，填「無」。

| 編號 | 層級 | 目標 | 錯誤/警告訊息 | 根本原因 | 處置 |
| ---- | ---- | ---- | ------------- | -------- | ---- |
|      |      |      |               |          |      |

---

## 4. 覆蓋聲明

### 已驗證

- [ ] 所有 `scrapers/*.yml` 通過 schema 驗證（L1）
- [ ] 所有 URL 陣列已排序（L2）
- [ ] Quality gate 16/16 通過（L3）
- [ ] Gender 值符合官方 enum（L4）
- [ ] 無 `movieByURL` 殘留（L4，如有則列為警告）
- [ ] parseDate 皆為 Go reference layout（L4）
- [ ] 文件欄位聲稱與 schema 一致（L5）
- [ ] 文件內嵌 YAML 範例可解析且無矛盾（L6）
- [ ] 文件索引完整（L7）
- [ ] Fixture runner 自測通過（L8）
- [ ] 無機密資料外洩（L9）
- [ ] 證據標籤無誇大（L10）
- [ ] Pytest 30/30 通過（L11）

### 未驗證（本報告不聲稱）

- [ ] Live 網站 selector 有效性（需 `scrutiny.js` 或瀏覽器）
- [ ] Stash runtime 載入（需 live Stash）
- [ ] CDP 渲染頁面（需 Chrome + CDP）
- [ ] 外部連結有效性（`link-check.yml` 為 advisory）

---

## 5. 與上次報告的差異

| 項目       | 上次 | 本次 | 差異說明 |
| ---------- | ---- | ---- | -------- |
| 總 verdict |      |      |          |
| 失敗層級   |      |      |          |
| 新增警告   |      |      |          |

---

## 6. 簽核

| 角色   | 姓名 | 日期 | 意見 |
| ------ | ---- | ---- | ---- |
| 執行者 |      |      |      |
| 審閱者 |      |      |      |

---

_模板版本：2026-10-07。修改模板需同步更新 `tools/run-all-checks.sh` 的層級定義。_
