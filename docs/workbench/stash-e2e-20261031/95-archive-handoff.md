---
doc_id: DOC-E2E-95
title: "Stash E2E Fix Workbench Archive Handoff"
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - live-e2e
last_verified: "2026-10-31"
authority: derived
routing:
  intents:
    - archive-handoff
    - workbench-lifecycle
---

# 完工歸檔交接（不要提前移動）

**目前：WORKBENCH_ACTIVE / NOT_ARCHIVED。**  
**暫存路徑：** `docs/workbench/stash-e2e-20261031/`  
**歸檔目的地：** `docs/archive/stash-e2e-20261031/`（repo 已存在 `docs/archive/`，此即使用者所稱 archived 類別）。

## 1. 何時可以歸檔？

完成下列全部事項，才由 Controller/使用者**另行核准 Archive-only PR**：

- [ ] 第一波三個 Draft 修復 PR 及依賴型第二波任務均有最終處置（合併、授權取消或上游轉交），並清楚標註 M6 Gate B 的證據狀態。
- [ ] 本工作包定義的所有**已核准**實作 workstream 完成，對應分支 PR 由使用者決定合併或明確停止，不留誤認待處理的 Draft。
- [ ] M0 重啟、備份、安全 Gate 完成或阻擋項已列入正式 owner／issue，無擅自升級 `PRODUCTION_READY`。
- [ ] M6 Independent Live Delta QA 已產生**具實際候選 package SHA、Stash build、原案例、負例、reviewer 證據**的正式裁決。
- [ ] 12 個 finding 每項有最終狀態或明確後續責任人；上游 Stash panic、Issue #4415、站台封鎖不得以「repo 修復完成」假裝消失。
- [ ] 將長期有效的運行規則／修復後 scraper 狀態同步至 [docs/60-live-test-status.md](../../60-live-test-status.md) 及其他 canonical docs（這是**後續另行授權**變更，不由歸檔取代）。
- [ ] QA-06 歷史 credential 事件在獨立追蹤中保留 OPEN（除非另外有足夠撤銷/輪替證據），正式部署責任不在歸檔時默認解除。
- [ ] 私有 evidence、登入/Token/Host traces 已留在受限保存區，只保留安全的 artifact index/hashes 於公開 repo；必要時檢查長期保存與可追溯性。

## 2. 如何移動（在核准的 Archive PR 上）

以下為**未執行的未來操作範例**；僅在符合上列條件並獲明確授權後進行：

```sh
git switch -c docs/archive-stash-e2e-20261031
git mv docs/workbench/stash-e2e-20261031 docs/archive/stash-e2e-20261031
# 將移動後 9 個 Markdown 檔案 YAML front matter 的 status: draft 改為 status: archived。
# 同步更新 docs/index.yml 的 9 筆 path/status（doc_id 保持不變），
# 並將 docs/README.md 的 Workbench 連結換成 Archive 連結。
python tools/check_docs_index.py
python tools/check_scraper_docs.py
npm run format:check
git diff --check
```

若文件中有相對路徑，兩個子目錄皆位於 `docs/<bucket>/<workstream>/`，同一深度，因此多數相對連結可保留；仍須以 link checker 核對。使用 `git mv` 讓 Git 保留變更歷史；不要複製後留下第二份「active」版本。

## 3. 歸檔 PR 必要描述與後置驗證

- 範圍僅限目錄移動、front matter `status`、索引／路由修正與結案交接摘要；不得夾帶 scraper fix。
- 必須連結最後 M6 verdict、修復 PR 清單、未結 external/upstream/security issue 清單。
- 過去 Live E2E 的 `PASS` 只對**當時 pinned source + Stash version + site state**有效；歸檔不會凍結網站或代替未來監測。
- Archive PR exact HEAD 的文件索引、格式及 CI PASS，通過 Maintainer review；**仍不可自行 merge**。
- 合併歸檔後回讀 main 確認：暫存目錄不再存在、`docs/archive/stash-e2e-20261031/` 包含全部 9 檔、索引路徑正確且 `status: archived`。

## 4. 最終交接記錄模板

```text
WORKBENCH: stash-e2e-20261031
IMPLEMENTATION_PRS: <numbers-and-merge-or-closed-status>
M6_QA_VERDICT: <independent-review-ref>
REMAINING_UPSTREAM: <issue-refs>
REMAINING_SITE_BLOCKERS: <site-status-refs>
QA06_SECURITY_TRACK: OPEN_SEPARATE | CLOSED_WITH_PRIVATE_ATTESTATION
PRODUCTION_READINESS: <separate-controller-verdict>
ARCHIVE_PR: <number>
ARCHIVE_REVIEWER: <identifier>
ARCHIVE_STATUS: NOT_RUN
```

Archive 後僅作歷史時點記錄；後續新的 Stash runtime findings 應建立新的 workbench / issue，不直接回改 archived 的證據事實。
