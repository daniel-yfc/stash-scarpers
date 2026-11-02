# ISSUE-97-COMMENT-DRAFT.md
**用途：** 可貼入 `daniel-yfc/stash-scarpers#97` 的去敏追蹤摘要（Agent E / WAVE2E-E-UPSTREAM-PANIC-20261102）。
**未經 Controller 授權前不貼出；不含私人原始日誌。**

---

## STASH-E2E-02 上游調查更新（Agent E，2026-11-02）

### 結論總覽

- **Reproduction Verdict：** `REPRODUCED_NO_STACK`（維持 QA 結論；5/5 unmatched URL panic、matched control 正常）。
- **Exact build：** `v0.31.1-182-g9e9ad972` = 上游 commit [`9e9ad972`](https://github.com/stashapp/stash/commit/9e9ad972643320e737c711884f10e4285f0f3a88)（2026-10-27，"Chore: Add v0.32.0 changelog (#7303)"），build 身分已核實。
- **Source findings：** `CALL_CHAIN_VERIFIED`。`pkg/scraper/cache.go:332` 無匹配 scraper 時回傳 `(nil, nil)`；`internal/api/scraped_content.go:170` 的 `return s[0], nil` 對空 slice 索引 → `runtime error: index out of range [0] with length 0`。`scraped_content.go` 已通過 blob SHA-1 位元組級驗證；`cache.go` 行號與 QA 引用交叉一致。
- **六種 URL API 證據層級：** 僅 `scrapeSceneURL` 有 runtime 重現；`scrapePerformerURL` / `scrapeGalleryURL` / `scrapeImageURL` / `scrapeMovieURL` / `scrapeGroupURL` 為 source-exposed（L160/180/190/200/210 同型未防護 `[0]`），未做 runtime 宣稱。
- **Upstream duplicate assessment：**
  - [#7275](https://github.com/stashapp/stash/issues/7275)（Prevent scraper API panic on typed-nil or empty results）為**同一根因**，但 2026-10-12 以 `not_planned` + `noncompliance` 關閉，**無 PR、無修補 commit**；develop HEAD（2026-11-02）兩關鍵檔案與我們的 build **blob 完全相同** → 未修復。
  - [#7315](https://github.com/stashapp/stash/issues/7315)（2026-10-31 closed completed，PR #6857 修復）為**不同根因**（`mapped.go:89` nil deref，修補 2026-05-28 已含於我們的 build）。
- **Missing stack trace：** `STACK_TRACE_NOT_CAPTURED` 維持揭露；root cause 判定基於 runtime error text + exact-commit 原始碼檢視，非杜撰 stack。
- **Evidence package：** QA 證據包（`qa-stash-upstream-panic-repro-20261101`）在 Agent E 執行環境不可存取，SHA-256 未能重驗（已如實記錄）。提交 upstream 前應於原環境重跑 `SHA256SUMS.txt` 驗證。
- **Recommended submission strategy：** **NEW_ISSUE**（新 Bug Report）。#7275 是「未處理即關閉」而非「已修復不同缺陷」；新報告遵循官方範本（含 troubleshooting-mode 確認）並引用 #7275 為 prior art。英文草稿已完成：`STASH-E2E-02-UPSTREAM-REPORT-DRAFT.md`。

### 下一步

1. **Controller 決策：** 是否授權提交 upstream 新 issue（以及是否先補抓完整 goroutine stack）。
2. **提交前：** 於原證據環境重驗 SHA-256；確認草稿去敏（已審核通過：無 API key / Cookie / 內網 IP / 私人 metadata）。
3. **提交後：** 回填 upstream issue URL、日期、狀態與解法版本；修復前本 Issue 保持開啟。
4. DVD 實作（`feat/e2e-bravo-dvds`）持續獨立進行；其 PASS 不結案本 Issue（unmatched-URL panic 控制案例獨立追蹤）。
