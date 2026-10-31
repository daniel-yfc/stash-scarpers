---
doc_id: DOC-E2E-92
title: "Stash Live E2E Fix Implementation Specification"
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
    - fix-spec
    - implementation-roadmap
---

# Live E2E 修復實施規格（M0–M6；平行開發 v3）

**Controller plan status:** `FIX-PLAN-STASH-E2E-20261031-v2 / ACCEPTED_WITH_AMENDMENTS`；以實際 QA v2 補測更正為基礎。  
**Baseline commit:** `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`。  
**Limits:** 此文件授權**規劃，不代表授權實際改 YAML、Stash 或 merge**。正式開發採獨立修復分支與 Draft PR，僅 Controller / 使用者核准範圍內修改；**不自行 merge**。

## 不變約束（Surgical Discipline）

1. 同一檔案在同一輪僅一個主要 Owner；並行研究只能提供 findings，不同時改同檔。
2. 每項實際修復先補「修前 FAIL → 修後 PASS」的可執行回歸；以 source 完成頁 DOM 與 Stash runtime 確認，不只看 Schema。
3. 每個 PR 審核 `Gate A`（schema/fixture/unit）、`Gate B`（候選包指紋 + 真實 stash-test delta）、`Gate C`（exact HEAD CI、CodeQL、來源 ZIP 檢驗）；任何一個缺失不得稱 `FIXED_VERIFIED`。
4. **不**重跑 21 個 Scraper 全量 Live E2E，也不重審 QA-17/18/19 或已接受的歷史 CodeQL dismissal。
5. 禁止從 public repo、歷史提交或 fixture 取用真實 Cookie、API Key、Token；未取得授權不得登入、寫入生產 Scene、開放 Chrome remote debugging。
6. 主張的修復目標是 metadata **正確與可用**，非僅「非空」。

## 裁決 D1–D3

- **D1 DVD:** BRAVO 新增 DVD 功能，但先修既有 Clips。兩個連續、獨立的 PR；`/dvds/` 路由目前不存在，不應把 Stash unmatched-URL panic 當 YAML selector 的直接錯誤。
- **D2 CDP:** 固定 `http://<internal-host>:9222/json/version` 已由 v2 實測在三個 Scraper 可用；先完成重啟 / ACL，不再預先設計 UUID 同步腳本。僅若此固定形式經實測失效才討論替代方案。
- **D3 推進:** M1 Metadata Integrity 與 M0 OPS 平行，BRAVO Clips 可獨立平行開發；Gate B 在 CDP 重啟可靠後進行。

## 工作流與檔案 Owner

| 里程碑 | 工作 Owner / 建議分支 | 修改範圍 | 關鍵交付／相依 |
| --- | --- | --- | --- |
| M0 | OPS（不操作正式站） | stash-test 部署/ACL/備份驗證紀錄 | 固定端點重啟三態、備份實體、存取限制 |
| M1 | WS-B1 `fix/e2e-metadata-integrity` | `scrapers/Justice01.yml`、`KOShop.yml`、`CK-Download.yml` + 相應 sidecars/fixtures/tests | 一個 Draft PR、三個獨立 finding commits |
| M1b-A | WS-B2A `fix/e2e-acceed-auth-guard` | `ACCEED.yml` + own fixture / tests | First wave in parallel; E2E-09 root cause before patch |
| M1b-B | WS-B2B `fix/e2e-performer-identity` | Necessary GAMES/Justice01/RGBEE/CK-Download/Trance + dedicated tests | Wave 2 only after overlapping M1/M3 files are integrated; E2E-10/11 A/B cause confirmed |
| M2 | WS-A1 `fix/e2e-bravo-clips` | `BRAVO.yml` Clips 部分 + fixtures/tests | 分離 clip selectors；移除不可靠直接 Fragment |
| M2b | WS-A2 `feat/e2e-bravo-dvds` | `BRAVO.yml` DVD 路由/獨立 scraper + fixtures/tests | 基於 M2（檔案同 Owner 串行）；完整 DVD DOM 證據先行 |
| M3 | WS-C `fix/e2e-search-quality`（先調查） | `KOTube.yml`、`Trance.yml`、經證據確認的 GVWiki/Gayerdar/Pubu | Query 能力與站台參數先驗證；無解停損 |
| M4 | WS-D 文檔／upstream | E2E findings 的文件狀態、[Issue #80](https://github.com/daniel-yfc/stash-scarpers/issues/80) 後續更新、上游 issue | 本工作包不直接改 upstream 或 issue；避免無證據的 panic 因果斷言 |
| M5 | WS-F site monitoring | ClubCK/GetFilm/JGVData 狀態記錄 | 下次增量 QA 前低頻各複測一次；BLOCKED_SITE 非 YAML FAIL |
| M6 | Independent QA | [94-delta-acceptance.md](94-delta-acceptance.md) | 所有經核准修復的原 case、負例、跨功能 smoke；最後 Controller verdict |


## Parallel Implementation Addendum — 首波三分支、最多六分支

**此節為現有 M0–M6 的強制執行補充。** 第一波三條 code-only Draft PR 可以同步開發；第二波按檔案依賴及實測可行性再建。分支與單一 Owner 的配置如下：

| Wave | Branch | Sole YAML owner | Finding | Dependency |
| --- | --- | --- | --- | --- |
| 1A | `fix/e2e-metadata-integrity` | Justice01, KOShop, CK-Download | E2E-05, 06a/06b, 08 | Latest main |
| 1B | `fix/e2e-bravo-clips` | BRAVO Clips only | E2E-03, 04 (direct Fragment) | Latest main |
| 1C | `fix/e2e-acceed-auth-guard` | ACCEED only | E2E-09 | Latest main |
| 2D | `fix/e2e-search-quality` | KOTube and Trance Search | E2E-07; E2E-12 investigation | Site/API feasibility confirmed |
| 2E | `feat/e2e-bravo-dvds` | BRAVO DVD route/parser | E2E-02 (repo component) | **1B merged to main first** |
| 2F | `fix/e2e-performer-identity` | A/B verified necessary YAML only | E2E-10/11 | **1A and 2D overlapping files merged first** |

**First-wave executable English assignment prompts:**

1. [Wave 1A — Metadata Integrity](96-agent-prompt-metadata-integrity.md).
2. [Wave 1B — BRAVO Clips](97-agent-prompt-bravo-clips.md).
3. [Wave 1C — ACCEED Auth Guard](98-agent-prompt-acceed-guard.md).

### Ownership and shared-files policy

- Scope each PR to assigned YAML, matching `scrapers/*.test.yaml`, corresponding `tests/fixtures/<site>/` and new uniquely named regression tests. **Do not let independent agents edit `docs/workbench/**, `docs/index.yml`, global workflows/validator/schema, or the same shared test file**. Those require a separate owner and Controller scope approval.
- `BRAVO.yml`: 1B first; 2E only after 1B is merged. `Justice01.yml` and `CK-Download.yml`: 1A first, then 2F if indicated. `Trance.yml`: 2D Search first, 2F Performer later. Never resolve conflicts by blindly taking one branch's version.
- Existing [docs PR #92](https://github.com/daniel-yfc/stash-scarpers/pull/92) is the **Docs Owner**. Until merged, use this branch's document URLs for agent prompts while deriving implementation code branches from `main`. The act of writing this plan **does not start the three code branches**.
- M0 OPS is an independent operational track (no code branch unless infrastructure changes are explicitly approved). M4 upstream/docs is not an extra scraper-fix branch; M5 is observation; M6 is independent QA.

### Phase orchestration

1. **Wave 1 kickoff:** three developers independently inspect main and create authorized `Draft PR → main` branches; M0 OPS validates fixed CDP HTTP `/json/version` restart-recovery, Chrome ACL, Stash GraphQL ACL and recoverable backup **in parallel**.
2. **Offline build phase:** each developer follows Skill `REVISE` P0–P6, checks real DOM vs error/login, writes a regression that fails before fix and passes after, builds a branch candidate ZIP with full Git history; attach exact commit/revision/hash.
3. **QA readiness:** Gate A and exact HEAD Gate C pass, changed-file ownership is clean; submit a `QA_LEASE_REQUESTED` including case list and candidate package provenance. **Do not claim live PASS using existing main-installed ZIPs.**
4. **Single shared stash-test acceptance lane:** Independent QA/OPS grants only one lease at a time (including reload, source installation and config changes); snapshot installed packages/settings before test, prove candidate version loaded, run original failing and key negative probes; restore baseline and record release of lease. No concurrent candidate installs or Scene updates.
5. **Merge train:** user alone decides merge. After each merge, other PRs sync current main, recheck CI/source ZIP and revalidate any Gate B evidence invalidated by HEAD/source changes. A merge may trigger public Source deployment; therefore **do not merge before candidate Live Gate B**.
6. **Second wave:** start only when dependencies and concrete evidence support it. No useless branch if the defect belongs to upstream Stash or a blocked external site.
7. **M6:** Independent Delta QA reruns affected failing cases, one non-CDP and CDP URL smoke, one Search→Detail, environment recovery, and external-site status classification. Final verdict requires exact HEAD/ZIP/Stash build and reviewer evidence; only then consider archive handoff.

### QA lease and stopping rules

`QA_LEASE_REQUESTED → QA_LEASE_GRANTED → CANDIDATE_INSTALLED → LIVE_DELTA_RECORDED → BASELINE_RESTORED → QA_LEASE_RELEASED`. Only an authorized QA owner may operate the shared staging instance. Failed M0 or hash mismatch ⇒ `GATE_B_BLOCKED` or `WRONG_REVISION`; insufficient live access ⇒ `NOT_RUN`. Do not recategorize such cases as PASS.

No additional staging persistence writes unless the backup file/snapshot actually exists, a restoration path is validated, and writes are explicitly authorized. Do not copy tokens/cookies/browser profiles into a public PR. Do not test formal production. If an agent cannot causally determine ACCEED's returned `ログイン` or a name-null performer stub, report a bounded diagnostic instead of speculative YAML changes.

### Every Draft PR must report

`BASE_MAIN_SHA, HEAD_SHA, BRANCH, OWNER_FILES, FINDING_IDS, BEFORE_AFTER_REGRESSION, SCHEMA_AND_FIXTURE, CI_CODEQL, PR_CANDIDATE_PACKAGE_VERSION_SHA256, STASH_BUILD, LIVE_QA_EVIDENCE_REF, NEGATIVE_CASES, GATE_A/B/C, ROLLBACK, BLOCKERS, MERGE_NOT_AUTHORIZED`. Exact HEAD changes invalidate unverified revision-dependent claims.

### Practical anti-failure checks

| Failure | Required mitigation |
| --- | --- |
| Parallel branches edit same file | Single owner, changed-file allowlist, start 2E only after 1B merge; 2F after 1A/2D |
| QA tests an old main package | Compare PR head, package version, ZIP SHA, installedPackages and selected Scraper before Gate B |
| Shared stash-test settings overwrite each other | Exclusive QA lease, baseline snapshot/restore, stop on unexpected changes |
| A fixture passes but Stash still saves bogus Title | Gate B negative/error/login scenario verifies **all writable metadata**, not Title alone |
| Static evidence mistaken for Live PASS | State `REPORTED`, `OFFLINE_PASS`, `LIVE_NOT_RUN` separately |
| Site block or Stash panic unrelated to repo | `BLOCKED_SITE` / `UPSTREAM_STASH`, bounded minimal reproduce, no invented workaround |

### GitHub source and implementation references

- [Repository AGENTS](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/AGENTS.md), [Skill entrypoint](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/skills/stash-scraper-builder/SKILL.md).
- [Official-derived validator / quality policy](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/21-quality-gate-rules.md), [Testing guide](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/50-testing-guide.md).
- [Source publisher workflow](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/.github/workflows/publish-scraper-source.yml), [Source ZIP builder](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tools/build_scraper_source.py).
- [Acceptance details](94-delta-acceptance.md), [Design decisions](93-design-decisions-and-references.md), [Archive handoff](95-archive-handoff.md).

**Production readiness remains `NOT_READY`** until independent QA, QA-06 and production-only authorization/security/backup gates are separately accepted.

## M0 — 操作環境 Gate

**M0-1** 從 Stash 內部驗證 `http://<internal-host>:9222/json/version` 可達（不要把私網主機名貼入公開報告）；分別重啟 Stash、Chrome、兩者，使用相同公開 CDP Scraper（GVWiki）原案擷取，證據留私有。

**M0-2** 驗證 Chrome debugging socket 只被授權主機／容器存取；stash-test GraphQL 須有認證或足夠嚴格 Tailnet ACL，並記錄測試人、存取路徑、收回機制。

**M0-3** 確認 `backupDatabase` 對應的備份產物確實存在且有可還原途徑（或使用已驗證的實例 snapshot），之後才可進行新持久化寫入。原有 15 個測試 Scene 暫留至 M6；Scene 7 的檔名與內容碼不同，不得用作 Identify matching PASS。

## M1 — 第一批 Metadata Integrity（可開發）

- **E2E-05 Justice01:** 現行 `URLs` 將 canonical 與 og:url XPath union 後 `concat: "\\n"`；改採 canonical 優先、og:url 缺席時 fallback，對單一有效 URL 產生結果。Fixture `justice115th`：恰一個可解析 URL、不含換行、與 canonical 一致。不能只在 JS 字串上盲目 split 以掩蓋不正確 selector。
- **E2E-06 KOShop（同一檔案內兩問題一起修）:** Search `URLs` 的 `v.replace(/\\?.*$/, "")` 砍掉 `?product_id=`；保留必要 product_id 並允許相對網址安全正規化，不要無差別保留追蹤參數。Scene Title 不得以 `//title` 接受不存在產品時的錯誤頁；只有有效商品節點存在才回可用 metadata（**驗證整體輸出無錯誤可寫入欄位，不只是 Title 變空**）。Probe：KERO256 → 搜尋結果保留 product_id、可續擷詳情；不存在 ID → 無可寫入假值；有效 41979 凍結案不退化。
- **E2E-08 CK-Download:** Title union `DVDタイトル td | h3 | //title` 遵循 XPath document-order 而非程式設計的 fallback 次序。以有效商品節點做首選與有條件備援；不要再無條件加入 `//title`。Probe `detail/34418` 的 URL 與 Search Title 一致，另加一個 DVD 商品及不存在商品負例。

**驗收：** M1 修前 FAIL／修後 PASS、原樣本＋第二布局樣本、Stash search → selected detail、錯誤頁不污染。

## M1b — 身分與誤導資料（先做根因 A/B）

- **E2E-09 ACCEED:** GraphQL 返回「ログイン」是否真的由 `//div[@id='content4']//blockquote/h2` 抽到，須先對照完成登入頁 DOM、Stash 實際選取的 Scraper 與 response 結構；定位前不改 XPath。未登入頁不得回可寫入 scene；合法登入頁只在使用者另外授權的 Session 測試後才可稱完整 PASS。
- **E2E-11 Performer stub:** 現有固定 Gender/Country 等欄位與 `name: null` 同時存在，**尚未因果驗證**。使用可重現的完成頁 fixture/獨立 Stash A/B 先證明 fixed 值是否造就 stub，再確認 Name-required 的可行 schema 寫法；不能憑猜測在所有 Scraper 刪固定欄位。
- **E2E-10 Trance:** 解析 `performerByURL` 回「指定なし」是否代表無有效 performer；若來源只給占位值，YAML 應拒絕建立該實體，否則留下文件化限制。
- 與 M1 的 `Justice01.yml`、M3 的 `Trance.yml` 相依；同檔修改串行，避免 PR overlap。

## M2/M2b — BRAVO 拆分

- **M2 Clips:** 原路由僅 `/clips/`，但 Title/Code/Image selectors 是 DVD page；建立 `clipSceneScraper` 及 Clips 專用 Title/Code（從完成頁取值）。如來源未提供 Date/Studio，**不要杜撰**。`/clips/284` 和 `/clips/282` 應以真實值比較；先移除可靠性不足的 `sceneByFragment`（`{title}` 空值可能送 `%7Btitle%7D`），保留正常 `sceneByQueryFragment` 搜尋結果 URL 保存行為。禁止將 DVD routing 混入本 PR。
- **M2b DVD:** 基於 Clips PR 的新 HEAD，先確認 `/dvds/234`、`/dvds/084` 及不同 DVD layout 的完成頁，建立獨立 `dvdSceneScraper` 與 `sceneByURL` 模式，至少兩個不同模板通過。未匹配 URL 的 panic 屬上游待查，不應為了使其消失而宣稱 Stash 已修。

## M3 — Search 精確度，設停損

- KOTube `29-01-0209-01`（原 160 筆無目標）、Trance `TC-05-0013-01`（原 60 筆無目標）：先檢查站台 query 參數、HTTP redirect、完成搜尋頁，判斷原始 query 是否在 Stash postProcess 中可用；站台原生精確比對優先。不可無差別逐筆打開 160 個詳情頁；單輪無法定位，`PARTIALLY_FIXED` 或 `BLOCKED_SITE` 需與驗收證據一致，**不能假裝 PASS**。
- GVWiki `JST56X`、Gayerdar `GD-025`、Pubu `348474`：各做匿名/授權環境對照，無 code-level 證據則轉 M5 觀察，不盲改 XPath。

## M4/M5 — 上游、文件、第三方站台

- [stashapp/stash#4415](https://github.com/stashapp/stash/issues/4415) 已由 GitHub API 確認目前 Open，討論缺值 queryURL 的行為；先補充 BRAVO 最小重現再決定開新議題。未匹配 URL panic 同樣先查重。
- [Epic #80](https://github.com/daniel-yfc/stash-scarpers/issues/80) 需在後續授權 PR/Issue 更新新的主幹 SHA、finding 狀態及 M6 憑據；**本工作包不改該 Issue**。
- Draft [#84](https://github.com/daniel-yfc/stash-scarpers/pull/84)（GraphQL harness）/ [#85](https://github.com/daniel-yfc/stash-scarpers/pull/85)（Evidence Validator）**不直接合併**，待 M1 後評估可移植元件。
- M5：ClubCK（timeout）、GetFilm（503）、JGVData Search（500）僅低頻複測恢復狀態，不用偽造 Scraper fix。

## M6 — 最小有效整合驗收

只執行改過的 finding 原案例＋必要負例＋一組跨功能 smoke：來源/套件載入、非 CDP detail、CDP detail、Search→Detail。結果需含精確 PR HEAD、Scraper revision/ZIP SHA、Stash build、證據位置、獨立 QA verdict。詳 [94-delta-acceptance.md](94-delta-acceptance.md)。

若正式發布/部署前 QA-06、登入功能、私網 ACL 或備份仍 OPEN，僅可有限測試發布，不得稱 `PRODUCTION_READY`。
