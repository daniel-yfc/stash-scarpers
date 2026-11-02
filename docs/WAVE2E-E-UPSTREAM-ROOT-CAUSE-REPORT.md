# WAVE2E-E-UPSTREAM-ROOT-CAUSE-REPORT.md
**Assignment:** `WAVE2E-E-UPSTREAM-PANIC-20261102` / WS-D / STASH-E2E-02
**Agent:** E（獨立上游調查 / 證據審核）
**日期：** 2026-11-02
**狀態：** 調查完成；未向 upstream 提交任何內容（`UPSTREAM_SUBMISSION_STATUS: NOT_FILED`）

---

## 0. 執行摘要

| 項目 | 結論 |
|---|---|
| Reproduction Verdict | `REPRODUCED_NO_STACK`（QA handoff，5/5；本環境無法重驗原始檔，見 §1） |
| Root Cause Verdict | **CONFIRMED**（原始碼層級，位元組級驗證；runtime stack 未取得） |
| 呼叫鏈驗證 | **`CALL_CHAIN_VERIFIED`**（commit `9e9ad972`，與 develop HEAD 比對一致） |
| Upstream #7275 | **同一根因、未修復**（closed as `not_planned`，無 PR、無修補 commit） |
| Upstream #7315 / PR #6857 | **不同根因**（`processSceneRelationships` nil deref；已修復且已含於 QA build） |
| Upstream 建議 | **Option 2：建立新的 Bug Report**（`NEW_ISSUE`，草稿已備妥，待 Controller 授權） |

核心結論：無匹配 scraper 的 `scrapeSceneURL` 會使 `cache.ScrapeURL` 回傳 `(nil, nil)`，
`marshalScrapedScene` 對 nil content 包裝成的單元素 slice 在 nil 被過濾後變成空 slice，
隨後 `s[0]` 觸發 `runtime error: index out of range [0] with length 0`。
六種 `scrape*URL` API 在原始碼層級均有相同未防護索引；**僅 `scrapeSceneURL` 有 runtime 重現證據（5/5）**。

---

## 1. E-01 — Evidence Integrity Review（部分完成，如實揭露）

本執行環境檢查結果：

- `~/workspace/qa-stash-upstream-panic-repro-20261101/`（root 與 `/home/user/workspace`）**不存在或為空**。
- 因此 QA reproduction report、GraphQL request/response 原始檔、server log、test matrix、
  `manifest.json`、`SHA256SUMS.txt`、English upstream draft **均無法在本環境重開與重新計算 SHA-256**。
- 依 Assignment 規範，此缺口**記錄為限制，未補寫任何虛構內容**。

可交叉驗證的部分（經 GitHub 讀取本地 Issue #97 與上游 repo）：

- Issue #97 記載的測試日期（2026-10-31）、Stash build（`v0.31.1-182-g9e9ad972`）、
  BRAVO baseline（`sceneByURL` 僅匹配 `/clips/`）、控制組行為，與 QA handoff 一致。
- `v0.31.1-182-g9e9ad972` 對應上游 commit `9e9ad972643320e737c711884f10e4285f0f3a88`
  （"Chore: Add v0.32.0 changelog (#7303)"，Gykes，2026-10-27T01:21:41Z）——build 身分核實。
- 最新 stable release 仍為 **v0.31.1（2026-04-13）**；v0.32.0 尚未發布（維護者於 #7315 表示
  v0.32.0 預計「週一」釋出，即 2026-11-02）。

**E-01 結論：** QA handoff 的敘述性證據與 Issue #97 相符，但原始證據包的完整性（SHA-256、
request/response 對應、時間戳關聯）**未能在本環境重驗**。建議 Controller 在提交前於原證據環境重跑 SHA-256 驗證。

---

## 2. E-02 — Exact Build Source Audit（commit `9e9ad972`）

### 2.1 已驗證的呼叫鏈

```
GraphQL scrapeSceneURL(url)
  └─ internal/api/resolver_query_scraper.go
       queryResolver.ScrapeSceneURL
         content, err := scraperCache().ScrapeURL(ctx, url, ScrapeContentTypeScene)   // err == nil
         ret, err := marshalScrapedScene(content)                                     // 無條件呼叫
  └─ pkg/scraper/cache.go:312  func (c Cache) ScrapeURL(...)
       迴圈內：僅當 s.supportsURL(url, ty) 成立才執行 viaURL
       L324-326: if ret == nil { return ret, nil }   // 匹配但回傳空
       L332:     return nil, nil                     // ← 無任何 scraper 匹配（與 QA 引用 :332 一致）
  └─ internal/api/scraped_content.go:164  func marshalScrapedScene
       L165: marshalScrapedScenes([]scraper.ScrapedContent{content})  // content == nil
       L15:  if c == nil { continue }                 // nil 被過濾 → ret 為空 slice、無 error
       L170: return s[0], nil                         // ← panic: index out of range [0] with length 0
```

### 2.2 驗證方法與強度

| 檔案 | blob SHA-1（GitHub 官方） | 本端重構驗證 |
|---|---|---|
| `internal/api/scraped_content.go` | `f7d40c95dcb1c1f91d8e06f72bf249f6fcc3ee20` | **位元組級一致**（blob SHA-1 重算吻合；L160/170/180/190/200/210 六處 `[0]` 索引） |
| `pkg/scraper/cache.go` | `83a590b3ec6c2ad5dfeb05e553b98dfcfe8fed60`（12,701 bytes） | 本端重編碼 12,702 bytes（差 1 byte，判定為 EOF 換行差異）；行號經兩路交叉驗證一致 |

- `cache.go:332`（`return nil, nil`）與 QA 獨立引用的位置**完全一致**；
  `scraped_content.go:170`（`return s[0], nil`）與 QA 引用**完全一致**，且該檔案通過位元組級驗證。
- 兩檔案在 **develop HEAD（2026-11-02 讀取）與 commit `9e9ad972` 為相同 blob**——
  即最新 develop 仍存在相同程式碼路徑，行號可直接引用。

### 2.3 QA 六項原始碼結論的獨立核驗

| QA 主張 | 核驗結果 |
|---|---|
| 無匹配 scraper 時回傳行為 | 屬實：`cache.go:332` 回傳 `(nil, nil)`，無錯誤 |
| `scrapeSceneURL` resolver 呼叫流程 | 屬實：`resolver_query_scraper.go` 中 `ScrapeSceneURL` 無條件呼叫 `marshalScrapedScene` |
| `marshalScrapedScene` 空值處理 | 屬實：nil content 被過濾、回傳空 slice 與 nil error，`s[0]` 無保護 |
| Nil / empty slice 轉換 | 屬實：`marshalScrapedScenes` L15 `if c == nil { continue }` |
| 是否直接執行 `s[0]` | 屬實：`scraped_content.go:170` |
| 另五種 URL helper 同型風險 | **原始碼層級屬實**：performer L160、gallery L180、image L190、movie L200、group L210 均為未防護 `[0]`；對應 resolver（`ScrapePerformerURL`/`ScrapeGalleryURL`/`ScrapeImageURL`/`ScrapeMovieURL`/`ScrapeGroupURL`）皆無條件呼叫。**僅 source-exposed，無 runtime 重現** |

**E-02 結論：`CALL_CHAIN_VERIFIED`**（以 exact commit `9e9ad972` 行號為準；develop 行號經 blob 比對確認相同，非以會移動的 develop 行號冒充）。

---

## 3. E-03 — Upstream #7275 Investigation

### 3.1 #7275 事實

- 標題：**Prevent scraper API panic on typed-nil or empty results**（作者 MaxRink，2026-10-12 建立）
- 內容明確描述：typed-nil pointer 在 `ScrapedContent` 內被 type switch 視為有效物件並解參考；
  **空結果產生 empty slice 後直接索引**——涵蓋 scene/performer/gallery/image/movie/group 單物件 marshalling helper。
- **2026-10-12 同日由 DogmaDragon 關閉，`state_reason: not_planned`，標籤 `noncompliance`。**
- **0 則評論、0 個關聯 PR**（`closed_by_pull_requests.total_count = 0`）。

### 3.2 修補查證

- PR 搜尋（`scraper panic typed nil`）：0 筆結果。
- `internal/api/scraped_content.go` 與 `pkg/scraper/cache.go` 自 2026-09-01 起**無任何 commit**。
- develop HEAD（2026-11-02）兩檔案 blob 與 `9e9ad972` **完全相同** → 未防護索引仍在。
- 無 revert、無後續追蹤。

### 3.3 #7275 判定

**同一根因；原問題尚未修復。** #7275 的 `not_planned` + `noncompliance` 關閉不代表修復——
`noncompliance` 標籤合理推斷為未遵循 Bug Report 範本（該文缺少 #7315 所有的 troubleshooting-mode 確認欄位；
此為推斷，維護者未留下說明）。此判定不因 Closed 狀態而放寬。

### 3.4 鄰近但**不同**根因的追蹤（避免誤歸併）

| 追蹤 | 症狀 | 根因位置 | 狀態 | 與本案關係 |
|---|---|---|---|---|
| #7275 | typed-nil / empty slice → marshal panic | `internal/api/scraped_content.go` 單物件 helper | closed `not_planned`、**未修復** | **同一根因** |
| #6921 / #7315 / PR #6857 | nil pointer dereference | `pkg/scraper/mapped.go:89` `processSceneRelationships`（匹配 scraper、無 scene 欄位時） | PR #6857 已於 2026-05-28 合併（v0.32.0 milestone），#7315 於 2026-10-31 closed `completed` | **不同根因**；修補**早於** QA build（2026-10-27），已包含在內 |
| #4415 | queryURL / fragment placeholder | 不同機制 | open | 不同問題（Issue #97 已註明） |
| #5793 | groupByURL 類似 panic | 未證實 | closed | 未證明相同根因 |

### 3.5 版本差異摘要

- QA build `9e9ad972`（2026-10-27）與 develop HEAD（2026-11-02）：**兩關鍵檔案位元組相同**。
- 最新 stable v0.31.1（2026-04-13）：較舊；本案**未驗證**該 release 的檔案內容，不作重現宣稱。
- v0.32.0：尚未發布（預計 2026-11-02）；依原始碼狀態，將帶有相同程式碼路徑（source-level 推論，非 runtime 宣稱）。

---

## 4. E-04 — Upstream Submission Strategy

| 選項 | 適用條件核驗 | 評估 |
|---|---|---|
| **Option 1：補充 #7275** | 根因相同 ✔；問題仍存在 ✔；維護者偏好既有追蹤 ✘ | `not_planned` + `noncompliance` 同日關閉、零互動；對 closed-not-planned issue 留言可見度低且無法重開。**不建議** |
| **Option 2：新建 Bug Report** | #7275 未處理任何缺陷（非「已處理不同缺陷」，而是「未處理即關閉」）✔；最新版仍有可獨立重現問題（develop 檔案相同 + 5/5 runtime 重現）✔；有完整、獨立、可公開技術證據 ✔ | **建議**。以正式範本重提（含 troubleshooting-mode 確認），引用 #7275 為 prior art |
| **Option 3：暫不提交** | 修復不存在於任何未部署版本（develop 相同）✘；上游無活躍追蹤 ✘ | **不建議**。唯一缺口（stack trace）已如實揭露且不影響 triage 品質 |

**推薦：Option 2（`NEW_ISSUE`）**，條件：
1. Controller 授權後提交（本任務未提交）。
2. 提交前於原證據環境完成 QA 證據包 SHA-256 重驗（E-01 缺口）。
3. 若能取得 troubleshooting 模式下的完整 goroutine dump，優先補上再提交；
   若無法取得，依草稿如實標示 `STACK_TRACE_NOT_CAPTURED`。
4. 草稿已嚴格遵循上游 Bug Report 範本欄位（troubleshooting mode、版本、重現步驟等），避免重蹈 #7275 的 `noncompliance`。

---

## 5. 風險控制對照

| Risk | 處置結果 |
|---|---|
| #7275 已存在相同問題 | 已查 closure/fix history：`not_planned`、無 PR、無 commit、develop 未變 |
| 舊版有問題、最新版已修復 | 已核對 exact commits：develop HEAD 與 build blob 相同，未修復 |
| Source-level 推論被當成 runtime 證據 | 全文區分 runtime-reproduced（僅 `scrapeSceneURL` 5/5）與 source-exposed（六 API）；`STACK_TRACE_NOT_CAPTURED` 保留 |
| 六 API 均宣稱受影響但未測 | 草稿明確標示僅 `scrapeSceneURL` 有 runtime 證據，其餘為 source-level |
| DVD 修復後不再觸發 | example.com 控制 URL 與 DVD 案分列； unmatched-URL 控制案例獨立於 DVD workstream |
| GitHub 曝露敏感資訊 | 草稿去敏審核通過（無 API key、Cookie、內網 IP、私人 metadata；重現僅用 example.com） |
| 重複提報 | 已完成 duplicate triage（#7275/#7315/#6921/#4415/#5793），草稿明確引用 #7275 為 prior art |

---

## 6. Acceptance Criteria 狀態

- [x] 已核對 5/5 重現證據（**部分**：與 Issue #97 及 QA handoff 交叉核對一致；原始檔在本環境不可存取，見 E-01）
- [ ] 已檢查 evidence SHA-256（**無法執行**：證據包不可存取；如實記錄，未杜撰）
- [x] 已核對 exact build source call chain（`CALL_CHAIN_VERIFIED`；blob 級驗證）
- [x] 已釐清六種 URL 類型的證據層級（1 runtime / 5 source-exposed）
- [x] 已調查 #7275 關閉原因（not_planned、noncompliance、無修補）
- [x] 已提出 upstream 處理建議（NEW_ISSUE）
- [x] 已保留 stack trace 缺口聲明（STACK_TRACE_NOT_CAPTURED）
- [x] 已完成去敏審核（草稿無敏感資訊）
- [x] 未自行向 Stash upstream 提交 Issue（未執行任何外部寫入）

---

## 7. Mandatory Handoff

```yaml
ASSIGNMENT_ID: WAVE2E-E-UPSTREAM-PANIC-20261102
WORKSTREAM_ID: WS-D
AGENT_ROLE: Agent E
ASSIGNMENT_STATUS: COMPLETED
BASE_SHA: "stashapp/stash@9e9ad972643320e737c711884f10e4285f0f3a88 (v0.31.1-182-g9e9ad972)"
BRANCH: N/A
HEAD_SHA: N/A
CHANGED_FILES: []
DELIVERABLES:
  - "WAVE2E-E-UPSTREAM-ROOT-CAUSE-REPORT.md（本文件，含 Deliverable A/B）"
  - "STASH-E2E-02-UPSTREAM-REPORT-DRAFT.md（Deliverable C，英文上游草稿）"
  - "ISSUE-97-COMMENT-DRAFT.md（Deliverable D，本地追蹤評論草稿）"
EVIDENCE:
  - "stashapp/stash commit 9e9ad972（get_commit 核實，2026-10-27）"
  - "pkg/scraper/cache.go@9e9ad972 blob 83a590b3（與 develop HEAD 相同）"
  - "internal/api/scraped_content.go@9e9ad972 blob f7d40c95（位元組級驗證通過；與 develop HEAD 相同）"
  - "stashapp/stash#7275（closed not_planned / noncompliance / 0 PR / 0 comments）"
  - "stashapp/stash#7315 + PR #6857 + #6921（不同根因，已修復）"
TEST_RESULTS: []
KNOWN_LIMITATIONS:
  - "STACK_TRACE_NOT_CAPTURED：完整 goroutine stack 未取得（QA 亦未取得）"
  - "E-01：QA 證據包（~/workspace/qa-stash-upstream-panic-repro-20261101/）在本執行環境不可存取，SHA-256 與 request/response 對應未重驗"
  - "cache.go 本端重編碼與官方 size 差 1 byte（EOF 換行），行號經 QA 引用交叉驗證一致"
  - "v0.31.1 stable 與 v0.32.0（未發布）未做 runtime 驗證；develop 僅 source-level 證據"
DEPENDENCIES:
  - "Controller: upstream submission decision（含 E-01 SHA-256 重驗授權）"
RISKS_AND_DECISIONS:
  - "#7275 為同一根因但以 not_planned 關閉 → 選擇 NEW_ISSUE 而非 COMMENT_EXISTING"
  - "#7315/PR#6857 已釐清為不同根因，避免誤併"
  - "六 API 中五種僅 source-exposed，草稿明確分級"
REPRODUCTION_VERDICT: REPRODUCED_NO_STACK
ROOT_CAUSE_VERDICT: CONFIRMED
UPSTREAM_RECOMMENDATION: NEW_ISSUE
UPSTREAM_SUBMISSION_STATUS: NOT_FILED
HANDOFF_STATUS: READY
```
