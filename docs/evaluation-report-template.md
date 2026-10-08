# 本機評估報告模板

獨立的本機完整測試評估報告格式。每次執行 `bash tools/run-all-checks.sh`
後，依此模板產出報告。

自動產生：`bash tools/run-all-checks.sh --report [輸出檔]`
（未指定輸出檔時寫入 `docs/reports/evaluation-YYYYMMDD-HHMMSS.md`）。
`{{...}}` 為佔位符，由 `--report` 模式填入；手動填寫時直接取代。

> 執行順序與依賴關係見 `tools/run-all-checks.sh` 檔頭註解。
> 線上 CI 流程見 `docs/05_CI_Workflows.md`。

---

## 1. 報告標頭

| 項目        | 內容           |
| ----------- | -------------- |
| 報告日期    | {{REPORT_DATE}} |
| 執行者      | {{EXECUTOR}}   |
| Repo commit | `{{COMMIT}}`（分支：`{{BRANCH}}`） |
| 執行環境    | {{ENV}}        |
| 執行方式    | {{METHOD}}     |
| 總 verdict  | {{VERDICT}}    |

---

## 2. 層級結果矩陣

依執行順序列出每層結果。狀態僅允許：通過 / 失敗 / 警告 / 跳過。

| 層級 | 名稱 | 依賴 | 狀態 | 耗時 | 備註 |
| ---- | ---- | ---- | ---- | ---- | ---- |
{{LEVEL_ROWS}}

**通過率**：{{PASS_RATE}}（L12 警告不計入失敗）

---

## 3. 失敗與警告明細

每個失敗或警告一列。若無，填「無」。

| 編號 | 層級 | 目標 | 錯誤/警告訊息 | 根本原因 | 處置 |
| ---- | ---- | ---- | ------------- | -------- | ---- |
{{ISSUE_ROWS}}

---

## 4. 覆蓋聲明

### 已驗證

<!-- CHECKBOX:L1 -->- [ ] 所有 `scrapers/*.yml` 通過 schema 驗證（L1）
<!-- CHECKBOX:L2 -->- [ ] 所有 URL 陣列已排序（L2）
<!-- CHECKBOX:L3 -->- [ ] Quality gate 16/16 通過（L3）
<!-- CHECKBOX:L4 -->- [ ] Gender 值符合官方 enum（L4）
<!-- CHECKBOX:L4 -->- [ ] 無 `movieByURL` 殘留（L4，如有則列為警告）
<!-- CHECKBOX:L4 -->- [ ] parseDate 皆為 Go reference layout（L4）
<!-- CHECKBOX:L5 -->- [ ] 文件欄位聲稱與 schema 一致（L5）
<!-- CHECKBOX:L6 -->- [ ] 文件內嵌 YAML 範例可解析且無矛盾（L6）
<!-- CHECKBOX:L7 -->- [ ] 文件索引完整（L7）
<!-- CHECKBOX:L8 -->- [ ] Fixture runner 自測通過（L8）
<!-- CHECKBOX:L9 -->- [ ] 無機密資料外洩（L9）
<!-- CHECKBOX:L10 -->- [ ] 證據標籤無誇大（L10）
<!-- CHECKBOX:L11 -->- [ ] Pytest 30/30 通過（L11）

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

_模板版本：2026-10-08。修改模板需同步更新 `tools/run-all-checks.sh` 的層級定義與 `--report` 填值邏輯。_
