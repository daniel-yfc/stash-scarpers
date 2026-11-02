# WAVE2E-D-BASELINE-CI-REPORT.md

**Assignment ID:** `WAVE2E-D-BASELINE-CI-20261102`  
**Workstream:** `WS-2E-00`  
**Role:** Baseline / CI / Release Readiness Agent (Agent D)  
**Repository:** `daniel-yfc/stash-scarpers`  
**Primary PR:** #93 (`fix/e2e-bravo-clips` → `main`)  
**Planning PR:** #98 (`docs/e2e-wave-2e-upstream-panic-20261101` → `main`)  
**Audit date:** 2026-11-02  
**Verdict:** `BASELINE_BLOCKED_LIVE_QA`

## 1. Current PR State

| Item | Verified value |
|---|---|
| PR #93 state | OPEN / DRAFT |
| Merged | No |
| Mergeable state | `clean`（無衝突；此為 GitHub 合併性指標，不等於授權合併） |
| Base branch / SHA | `main` @ `4bbafca9cf7b5d67117ac41136e74a303c28e4f4` |
| Head branch / SHA | `fix/e2e-bravo-clips` @ `86e34a24642dad2e64ae984e7e9182605e98cbcf` |
| Commits | 2（`c1843a8` → `86e34a2`） |
| Changed files | 9 |
| Merge authorization | `NOT_AUTHORIZED` |
| Gate B | `NOT_RUN` |

PR #93 目前仍為 Draft，且 PR body 明確標示 `MERGE_STATUS=NOT_AUTHORIZED`。本審查未發現任何已授權合併或已解除 Draft 的跡象。

## 2. Exact HEAD SHA

- **HEAD SHA：`86e34a24642dad2e64ae984e7e9182605e98cbcf`**（短 SHA：`86e34a2`）
- HEAD commit：`fix(e2e-bravo-clips): stabilize evidence, poster-only Image, isolated Clips manifest`（2026-11-01T03:47:42Z）
- 所有已核對的 CI check runs 皆對應此 HEAD（run 時間 2026-11-01T03:48Z 起），非舊 HEAD 的殘留結果。

## 3. CI / CodeQL Check Matrix

PR #93 HEAD 共 11 個 check runs：

| Check | Result | Required? |
|---|---|---|
| CodeQL | SUCCESS | 已確認成功 |
| Analyze (actions) | SUCCESS | CodeQL job |
| Analyze (javascript-typescript) | SUCCESS | CodeQL job |
| Analyze (python) | SUCCESS | CodeQL job |
| github-advanced-security | SUCCESS | 已確認成功 |
| pr-check | SUCCESS | 已確認成功 |
| Build installable scraper source | SUCCESS | 已確認成功 |
| Full Test & Validation Suite | SUCCESS | 已確認成功 |
| fixture-manifests | SUCCESS | 已確認成功 |
| evidence | SUCCESS | 已確認成功 |
| Deploy installable source to GitHub Pages | SKIPPED | 部署類 job，非測試失敗 |

- 10 項 SUCCESS、1 項 SKIPPED、0 項 FAILURE。
- 無 stale CI：所有 check runs 的時間戳（2026-11-01T03:48Z）晚於 HEAD commit 時間（2026-11-01T03:47:42Z），且 run URL 對應同一 workflow run。
- Required check 設定（branch protection）無法透過目前可用的 read-only GitHub connector 直接讀取；以 `mergeable_state: clean` 作為間接證據（GitHub 僅在無衝突且必要檢查未失敗時回報 clean）。此為已知限制，非直接證據。

## 4. Required vs Optional Checks

- **已確認成功的關鍵 gates：** CodeQL、Evidence Contract（`evidence`）、Fixture Manifest Verification（`fixture-manifests`）、Full Test & Validation Suite、Source Build（`Build installable scraper source`）。
- **Skipped：** `Deploy installable source to GitHub Pages`。此為部署類 job，非測試 gate；不影響 baseline 技術判定，但若該 job 在 branch protection 被設為 required，則需另行確認。目前無證據顯示其為 required。
- **無法直接讀取：** repo 的 branch protection required-check 清單。建議 Controller 在合併前於 GitHub UI 確認 required checks 設定。

## 5. Fixture Integrity

### 5.1 歷史 fixture digest

- 檔案：`tests/fixtures/bravo/bravo-fixtures.yml`
- 於 HEAD `86e34a2` 重新取得內容並計算：
  - **SHA-256：`be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`** ✅ 與指定值完全一致。
  - Git blob SHA：`f38a38e8ef8bdacc1546b2817f1a014eb2c91544`。
- 與 `main`（`4bbafca9`）同一檔案比對：blob SHA 完全相同 → **byte-for-byte identical to main**，歷史證據未被改寫。
- 與 `docs/archive/evidence/status/bravo.yml` 交叉核對：
  - 該檔 pin 的 `fixture.sha256` = `be1885d2...` ✅
  - `artifact` = `tests/fixtures/bravo/bravo-fixtures.yml` ✅
  - `captured_at` = `2026-10-14T19:09:10+08:00` ✅
- 結論：**歷史 fixture 完整性 PASS**，未發現為使 CI 通過而改寫歷史證據的行為。

### 5.2 Clips fixture manifest 獨立性

- 新檔 `tests/fixtures/bravo/bravo-clips-fixtures.yml` 已存在，且 `scraper: scrapers/BRAVO.yml`。
- 內含 6 個 cases：clip 284、clip 282、clip missing title、clip no verified cover、clip 284 with extra headings、Cloudflare failure。
- 歷史 manifest（bravo-fixtures.yml）仍保留 3 個 DVD/Cloudflare cases，無 scraper key、無 Clips cases。
- `tools/tests/test_bravo_clips.py` 內含 `test_historical_fixture_manifest_preserved`，直接 pin 上述 digest、artifact path 與 captured_at，並已在 Full Test & Validation Suite 通過。

## 6. Candidate Package Provenance

| Item | Value | 狀態 |
|---|---|---|
| Candidate revision | `86e34a2` | 與 HEAD 一致 ✅ |
| BRAVO ZIP SHA-256 | `a4d24b1f94b2f6343e2379555e95c3d3bba29afa1b71ef3ea4e1a14057aa1390` | PR body 記錄，repo 內無獨立檔案記錄 |
| BRAVO.zip 內容 | `BRAVO.yml` only（宣稱 6532 bytes） | PR body 記錄 |
| Build 來源 | `tools/build_scraper_source.py`，isolated preview dir，`--verify-only` PASS | PR body 記錄 |
| CI Source Build | `Build installable scraper source` SUCCESS on HEAD | GitHub CI 已確認 ✅ |

- **評估：** HEAD 未變（仍為 `86e34a2`），故 PR body 中的 package digest 不屬於「舊版殘留」，可作為 candidate provenance 的初步依據。
- **限制：** `a4d24b1f...` 此 SHA 僅存在於 PR body 文字，repo 內（code search）未找到獨立的 digest 記錄檔；本 Agent 無法在 read-only 環境重跑 build 以重算 ZIP SHA。建議 Gate B QA 在安裝前以實際下載的 ZIP 重算 SHA-256 並比對。
- **BRAVO.yml at HEAD** 已核對：Clips-only routing、poster-only Image、無 direct `sceneByFragment`、保留 `sceneByQueryFragment`（`queryURL: "{url}"`）。

## 7. Gate B Evidence

| 檢查項 | 狀態 |
|---|---|
| PR #93 專屬獨立實機 QA 報告 | **不存在**（repo docs 與 issues 搜尋皆無） |
| 報告對應 exact HEAD | N/A（無報告） |
| 安裝 package 對應 candidate SHA | N/A（無報告） |
| Clips 284 / 282 實際 Title、Code、URLs、Duration | **未驗證（NOT_RUN）** |
| Image poster-only 實際結果或缺失 | **未驗證（SOURCE_IMAGE_UNVERIFIED）** |
| Title-less negative case 不被誤判為完整成功 | YAML/fixture 已記錄限制，但實機行為未驗證 |
| 不構造 `clips/%7Btitle%7D` 假 URL | 結構層已移除 direct sceneByFragment（offline 已驗證），實機未驗證 |

- `docs/60-live-test-status.md` 的 BRAVO live verification 日期為 2026-10-06，屬舊版 baseline，**不得**作為 PR #93 新版的 Gate B 證據。
- 結論：**Gate B = NOT_RUN**，無任何可取代獨立實機 QA 的證據。

## 8. Missing Conditions

1. **獨立 Gate B QA 未執行**（stash-test、M0 preflight、exclusive lease、GraphQL request/response、正負例、Image 來源、log 保存）。
2. **Controller／使用者合併授權未取得**。
3. **BRAVO ZIP SHA-256 的 repo 內獨立記錄缺失**（僅 PR body），建議 Gate B 執行時補實測重算。
4. **Branch protection required-check 清單未直接讀取**（僅間接證據 `mergeable_state: clean`）。

## 9. Risk Assessment

| Risk | Assessment |
|---|---|
| Clips Title/Code 只在 fixture 成功 | **必須實機重測**（Gate B 未跑，offline fixture 不算數） |
| Image selector 指向無關圖片 | 已改為 poster-only（`//video/@poster`），fail-closed；實際 live poster 值仍未驗證 |
| 空 Title 但其他欄位存在 | YAML 已明文記錄：Title-less result **不得**算完整成功；實機行為待 Gate B 確認 |
| QueryFragment 仍固定使用 Clips scraper | 已確認保留 `sceneByQueryFragment` + `queryURL: "{url}"`；交接 Agent B/F |
| 修改 BRAVO YAML 導致舊測試失效 | 歷史 manifest 已 byte-for-byte 還原，digest 未變；Clips cases 已隔離至新 manifest |
| Source package 與 branch HEAD 不一致 | HEAD 未變，candidate revision `86e34a2` 與 HEAD 一致；ZIP SHA 需 Gate B 實測重算確認 |

## 10. Controller Decision Recommendation

**建議裁決：`BASELINE_BLOCKED_LIVE_QA`**

- 技術 Gate A（offline）與 Gate C（exact-HEAD CI/CodeQL）目前皆為 PASS。
- 但 Gate B（獨立實機 QA）尚未執行，且合併授權未取得。
- **不可**在 Gate B 完成前宣告 `FIXED_VERIFIED` 或合併 PR #93。
- 若 Gate B 通過且 Controller 授權，方可建議批准合併。

## 11. Gate B QA Handoff（可直接執行的任務規格）

**測試環境：** `stash-test`  
**前置：** M0 preflight、取得獨占 lease、確認 Stash 版本與 BRAVO package 版本。

**必測項目：**
1. 安裝 candidate BRAVO package（revision `86e34a2`），安裝前重算 ZIP SHA-256 並比對 `a4d24b1f...`。
2. Clips 284 正例：驗證實際 Title、Code（284）、URLs（canonical）、Duration（1800）。
3. Clips 282 正例：同上（Code 282、Duration 1800）。
4. Title-less negative case：確認 Title 為空時，Code/Duration/URLs 雖可能存在，但**不得**判定為完整成功。
5. Image 來源檢查：確認 poster-only selector 在實機的實際行為（有 poster → 該值；無 poster → Image 空），並確認不會回傳 myfans logo GIF 或無關 Wix 圖。
6. 確認不會構造 `clips/%7Btitle%7D` 假 URL。
7. GraphQL request/response 全程留存。
8. 環境復原與 log 保存。

**未取得環境授權時：** 狀態維持 `BLOCKED_OPS_AUTHORIZATION` 或 `NOT_RUN`，不得宣稱 PASS。

## 12. Agent F Baseline Handoff

| Item | Value |
|---|---|
| Accepted / proposed baseline SHA | `86e34a24642dad2e64ae984e7e9182605e98cbcf`（proposed，待 Gate B + 授權） |
| Clips regression expectations | Title = h1；Code = h2 before "Clip"；Duration = h2 before 作品TIME ×60；URLs = canonical；Image = `//video/@poster` only |
| Package SHA-256 | `a4d24b1f94b2f6343e2379555e95c3d3bba29afa1b71ef3ea4e1a14057aa1390`（PR body 記錄，待 Gate B 實測重算） |
| QA verdict | `NOT_RUN` |
| Merge authorization status | `NOT_AUTHORIZED` |
| Remaining blockers | Gate B 獨立實機 QA、Controller 合併授權、ZIP SHA repo 內獨立記錄（建議補） |

**Agent F 指引：** 在 PR #93 未合併前，不得將 Wave 2E 正式 YAML 修改視為已具備 G0 基準。可先行準備（不落地）Wave 2E 規劃，但正式整合須等 baseline verdict 轉為 `BASELINE_ACCEPTABLE` 且合併授權取得。

## 13. Mandatory Handoff YAML

```yaml
ASSIGNMENT_ID: WAVE2E-D-BASELINE-CI-20261102
WORKSTREAM_ID: WS-2E-00
AGENT_ROLE: Agent D
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "4bbafca9cf7b5d67117ac41136e74a303c28e4f4"
BRANCH: N/A
HEAD_SHA: "86e34a24642dad2e64ae984e7e9182605e98cbcf"
CHANGED_FILES:
  - "scrapers/BRAVO.yml"
  - "scrapers/BRAVO.test.yaml"
  - "tests/fixtures/bravo/bravo-clips-fixtures.yml"
  - "tests/fixtures/bravo/clip-284.html"
  - "tests/fixtures/bravo/clip-282.html"
  - "tests/fixtures/bravo/clip-missing-title.html"
  - "tests/fixtures/bravo/clip-no-cover.html"
  - "tests/fixtures/bravo/clip-extra-headings.html"
  - "tools/tests/test_bravo_clips.py"
DELIVERABLES:
  - "WAVE2E-D-BASELINE-CI-REPORT.md"
  - "Gate B QA Handoff"
  - "Agent F Baseline Handoff"
EVIDENCE:
  - "GitHub check runs (11) on HEAD 86e34a2: 10 success, 1 skipped, 0 failure"
  - "bravo-fixtures.yml SHA-256 = be1885d2... (matches archived record and main blob)"
  - "docs/archive/evidence/status/bravo.yml cross-check PASS"
  - "BRAVO.yml at HEAD: Clips-only routing, poster-only Image, no direct sceneByFragment"
TEST_RESULTS:
  - "GATE_A (offline): PASS per PR body + CI corroboration"
  - "GATE_C (exact-HEAD CI/CodeQL): PASS (10 success, 1 skipped deploy job)"
  - "GATE_B (live QA): NOT_RUN"
KNOWN_LIMITATIONS:
  - "Branch protection required-check list not directly readable via connector"
  - "BRAVO ZIP SHA-256 recorded only in PR body; no repo-side digest file found"
  - "Gate B live QA not executed; no independent QA report exists for PR #93"
DEPENDENCIES:
  - "Independent authorized QA: Wave 1B Gate B"
  - "Controller: merge authorization"
RISKS_AND_DECISIONS:
  - "Clips live Title/Code/Duration unverified -> must re-test in Gate B"
  - "Image poster-only selector live value unverified (SOURCE_IMAGE_UNVERIFIED)"
  - "Title-less negative case must not be accepted as full success"
BASELINE_VERDICT: BASELINE_BLOCKED_LIVE_QA
HANDOFF_STATUS: BLOCKED
```