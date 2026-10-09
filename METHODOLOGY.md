# 方法論：main → standalone-skill

本文件定義如何從主 repo（`daniel-yfc/stash-scarpers` 的 `main` 分支）衍生出獨立的 `stash-scraper-builder` skill（`standalone-skill` 分支），以及之後如何同步。目標是讓轉換過程可重複、可驗證，而不是一次性手工搬運。

## 1. 目的與定位

- **main 是 canonical**：`skills/stash-scraper-builder/` 是 skill 內容的唯一真實來源（SKILL.md、references、範本、工具）。
- **standalone-skill 是衍生物**：它是為了「不帶整個 repo 也能用這個 skill」而產生的 build artifact，照方法論重新產生，而不是手工長期維護的分叉。
- 本文件放在 standalone skill 根目錄（`METHODOLOGY.md`），跟著衍生物走，確保任何拿到 standalone 的人都能追溯它怎麼來的、怎麼更新。

## 2. 原則

1. **單一真實來源**：skill 的知識內容只在 main 上改，standalone 用方法論重產。
2. **零 repo 洩漏**：standalone 不得引用 repo 專屬路徑（`docs/`、`tools/`、`validator/`、`scrapers/`、`.github/`）、CI 或內部文件。
3. **自給自足**：standalone 只依賴官方 CommunityScrapers validator／schema＋自己的 `assets/`，不依賴本 repo 的任何東西。
4. **結構符合 skill 標準佈局**：根目錄 `SKILL.md`＋`references/`＋`assets/`＋`scripts/`（＋`tools/tests/`）。

## 3. 內容對應表（main → standalone）

| main 路徑                                                                                                                         | standalone 路徑 | 處理方式                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `skills/stash-scraper-builder/SKILL.md`                                                                                           | `SKILL.md`      | 提升到根目錄；按 skill best practice 重排呈現；更新 `metadata.version`                                                                           |
| `skills/stash-scraper-builder/references/*`                                                                                       | `references/*`  | 原樣搬運；**刪除** `skill-read-order.md`（router 就是 SKILL.md 內的 map）                                                                        |
| `templates/` 中的代表範本                                                                                                         | `assets/*.yml`  | 精選改寫為骨架（kebab-case 命名），不是整包複製；目前三個：`scene-xpath-template.yml`、`scene-json-template.yml`、`performer-xpath-template.yml` |
| 可獨立運作的工具                                                                                                                  | `scripts/*.py`  | 只收無 repo 依賴的：`check-scraper.py`、`new-scraper.py`，並驗證可獨立執行                                                                       |
| `LICENSE-MIT`、`LICENSE-CC-BY-SA-4.0`                                                                                             | 根目錄          | 原樣複製                                                                                                                                         |
| `.prettierrc.yml`、`.gitignore`                                                                                                   | 根目錄          | 複製／按 standalone 調整                                                                                                                         |
| 其餘全部（`docs/`、`scrapers/`、`validator/`、`tools/`、`skills/`、`.github/`、CI、`AGENTS.md`、`CONTRIBUTING.md`、根 README 等） | —               | **刪除**                                                                                                                                         |

## 4. 執行步驟

### Phase 1 — 抽取（機械化，可用 `scripts/sync-from-main.sh`）

1. 決定來源：`MAIN_REF`（預設 `origin/main`，或某個已驗證的 commit）。
2. `git archive $MAIN_REF skills/stash-scraper-builder | tar -x` 取出 skill 目錄。
3. `SKILL.md` → 根目錄；`references/` → 根目錄（排除 `skill-read-order.md`）。
4. 按對應表精選 `assets/`、`scripts/` 來源。

### Phase 2 — 剝離

刪除所有 repo scaffolding（見對應表最後一列）。刪完後根目錄只剩：`SKILL.md`、`references/`、`assets/`、`scripts/`、`tools/tests/`、LICENSE、prettier／gitignore 設定。

### Phase 3 — 重構（需人工判斷，見 §5 檢查清單）

- 移除 repo-only 標記與失效的相對連結。
- `schema-checklist.md`、`authoring-checklist.md` 改寫為圍繞 `assets/`＋官方 validator（不再指向 repo 內 `validator/`）。
- `scraper.schema.json` 的引用指向官方 CommunityScrapers URL。
- `SKILL.md` 的 `metadata.version` 更新為來源日期；description 的 scope／out-of-scope 與 main 一致。

### Phase 4 — 驗證（全部通過才算完成）

- [ ] `prettier --check` 乾淨
- [ ] `scripts/check-scraper.py`、`scripts/new-scraper.py` 可獨立執行
- [ ] `SKILL.md` frontmatter 合法（`name`、`description`、`metadata`）
- [ ] 無 repo 路徑洩漏：`grep -r "skills/stash-scraper-builder\|docs/0[1-7]\|validator/index\|\.github/" --include="*.md" --include="*.py" .` 無命中
- [ ] schema 引用為官方 URL（`https://github.com/stashapp/CommunityScrapers/...`）
- [ ] `references/` 與 main 來源 diff：差異只應是 §5 允許的重構，不應有內容缺失

## 5. 重構檢查清單（人工判斷項目）

轉換時每個 references 文件問三個問題：

1. 有沒有指向 repo 內路徑的連結或文字（`../docs/`、`../tools/`、`validator/`）？→ 改寫或刪除。
2. 有沒有假設讀者能跑 repo 的指令（`npm run …`、`bash tools/…`）？→ 改為官方 validator 指令或 standalone 內 `scripts/`。
3. 有沒有引用 repo 治理文件（`CONTRIBUTING.md`、`docs/0X_*.md`）？→ 刪除或改為 skill 內的對應說明。

## 6. 同步策略（main 演進時）

standalone 不會自動跟著 main 走。同步時機與做法：

- **觸發**：以下任一有實質變更時
  1. `skills/stash-scraper-builder/`、`templates/`（skill 內容本體）；
  2. **作者知識**：`docs/03_Quality_Gate_Rules.md` 的寫作規則、`tools/` 下可執行的語義檢查（如 `check_metadata_feed.py`、`check_scraper_semantics.py`）若新增了影響 scraper 寫法的規則——例如 2026-10-10 的 Rule 4（禁用 `*ByFragment` 裸 `"{url}"`）——要評估是否同步到 standalone 的 `references/`／`scripts/`（人工判斷，見 §5；standalone 的 `scripts/check-scraper.py` 是這類規則的對應落點）。
- **做法**：在 `standalone-skill` 分支上重跑 Phase 1–4（`scripts/sync-from-main.sh <new-main-ref>`），再按 §5 檢查清單處理重構差異。不要用 rebase 硬合——重產比解衝突可靠。
- **版本**：`SKILL.md` 的 `metadata.version` 寫來源日期；本文件 §8 記錄每次同步的來源 commit。

## 7. 已知限制

- standalone 的驗證是離線的（prettier、腳本自測、連結檢查）；live 站點驗證仍在 main repo 做。
- `assets/` 是精選骨架，不是 `templates/` 的完整鏡像；新增範本時回到 main 的 `templates/` 先行，再按對應表挑選。

## 8. 版本紀錄

| 日期       | 來源 main commit | 說明                                                                                                                                                                                                                                                                                                                                              |
| ---------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-10-09 | `ab53a21`        | 初次衍生：重構為 standalone skill（fba6288、8d30c73、4225e59）                                                                                                                                                                                                                                                                                    |
| 2026-10-10 | —                | 方法論文件化（本文件＋`scripts/sync-from-main.sh`）                                                                                                                                                                                                                                                                                               |
| 2026-10-10 | `b3fac11`        | 複檢：main 合併 #61（GraphQL 文件）、#62（Studio.URLs）；`skills/`、`templates/` 無變更，無需同步。§6 觸發條件擴大為含作者知識（`docs/03_Quality_Gate_Rules.md`、`tools/` 語義檢查）。待合併分支 `fix/fragment-url-rule` 含 Rule 4（禁用 `*ByFragment` 裸 `"{url}"`），合併後應評估同步到 standalone 的 `references/`／`scripts/check-scraper.py` |
