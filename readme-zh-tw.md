---
doc_id: DOC-ROOT-01
title: Stash 擷取器建置指南（繁體中文）
status: active
layer: repository
owner: maintainer
audience:
  - contributor
  - agent
applies_to:
  - scrapers
  - testing
last_verified: "2026-10-01"
authority: translation
routing:
  intents:
    - quick-start
    - scraper-authoring
    - zh-tw
---

# Stash 擷取器建置指南

[English README](README.md) · [文件索引](docs/README.md)

本儲存庫用於製作與驗證 Stash 擷取器的 YAML，並非 Stash 主程式，也不是社群擷取器儲存庫（CommunityScrapers）。Schema 與 validator 的上游關係請參閱 [來源紀錄](skills/stash-scraper-builder/references/upstream-sources.md)。本文件為譯本，僅供輔助操作；schema、工具與各主題的權威文件仍為判定依據。採用範本、通過 schema 驗證或 CI 全綠，都不等於實際在目標網站上測試通過。

## 建置流程

1. 先讀 [AGENTS.md](AGENTS.md)、[SKILL.md](skills/stash-scraper-builder/SKILL.md) 與 [閱讀順序](skills/stash-scraper-builder/references/skill-read-order.md)；再依需求閱讀 [執行環境選擇](skills/stash-scraper-builder/SKILL.md#runtime-selection) 與 [機密政策](skills/stash-scraper-builder/references/phase0-secrets-policy.md)。
2. 確認目標網站真正的 URL、回應格式、語系及存取限制，並保存來源 URL 與日期。不要虛構搜尋端點、模式或 selector；無法存取時標記 `UNVERIFIED`。
3. 從 [templates/](templates/README.md) 或已驗證的相近檔案起步。公開 YAML 放在 `scrapers/<CamelCaseName>.yml`，保留根層 `name:`；不得在任何版本、fixture 或報告中重現憑證、cookie、token 或瀏覽器設定檔內容。
4. 只採用已證實夠用的最簡方式：XPath → 真正的 JSON 回應 → 必要的 script → 僅在必須渲染或獲准互動時才用 CDP。HTML 內嵌的 JSON 不會自動變成 `scrapeJson` 可讀取的回應。只實作網站確實支援的入口，並保留來源語言。
5. 對完整目標頁進行測試，先排除挑戰頁、登入閘門、HTTP 錯誤與部分渲染。每個已設定的搜尋模式都需檢查有結果的搜尋頁、結果 URL 及獨立詳情頁；另測可選欄位缺失、版面變體與適用語系。請參閱 [測試指南](docs/50-testing-guide.md) 與 [渲染 DOM fixture 指南](docs/51-rendered-dom-fixture-testing.md)。
6. 保存證據與未解問題；唯有滿足 [A–H 正式環境閘門](docs/30-production-gate.md)的證據，才能宣稱可上正式環境。將事故與實際頁面的失敗案例回饋至規則、fixture 與測試。

## 本機檢查

在儲存庫根目錄執行：

```bash
npm ci
python -m pip install -r requirements.txt
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/parse_committed_yaml.py
node tools/verify-scraper-fixtures.mjs --self-test
python tools/run_fixture_manifests.py
python tools/scan_session_material.py
python tools/check_evidence_labels.py
python tools/check_evidence_contract.py
python tools/check_live_cdp_status.py
python tools/check_scraper_docs.py
python tools/check_docs_index.py
npm run format:check
```

`--self-test` 只測試 runner；沒有提交 manifest 時，檢查程序應回報 `UNVERIFIED`。若要指定特定 manifest，請執行 `python tools/run_fixture_manifests.py --expect tests/fixtures/<scraper>-fixtures.yml`。fixture 通過僅代表其中實際存在的案例與斷言皆通過，不代表涵蓋所有搜尋模式。格式化檢查屬於本機驗證，未實際執行即不得宣稱通過。

網站允許且可直接存取時，請分別檢查搜尋頁與詳情頁的原始 HTTP 回應：

```bash
node tools/scrutiny.js scrapers/<Scraper>.yml --search
node tools/scrutiny.js scrapers/<Scraper>.yml --url="<detail-url>"
```

此工具以 HTTP 加 JSDOM 檢查，不執行網站的 JavaScript；需要渲染的頁面，請改用瀏覽器 DOM 或 live Stash/CDP 驗證。請遵守存取限制，不繞過任何閘門。

## 證據與測試案例

逐一記下擷取器路徑、修訂版次、日期、來源 URL、回應種類（原始 HTTP、JSON、渲染 DOM、live Stash/CDP）、存取狀態、實際執行的命令與結果、欄位預期值與實得值，以及尚未驗證的 selector。建議的案例包括：版面有差異時的兩筆詳情、每種已設定搜尋模式的有結果頁與詳情結果、可選欄位缺失案例，以及適用的語系斷言；挑戰頁或錯誤頁需獨立分類。XPath fixture 應斷言匹配數量與代表值。以上撰寫要求並非全由 runner 強制執行。

務必分開記錄 schema、URL 排序、政策閘門、自動測試、快照／fixture、live-search、live-detail 與正式環境就緒狀態；未執行或遭封鎖的項目一律標為 `UNVERIFIED`。使用 [實測狀態](docs/60-live-test-status.md) 與 [報告範本](docs/71-test-report-template.md)記錄來源與限制。歷史 `evidence/` 不是現行政策，檢查清單或審查建議也不能取代實際測試。

## 儲存庫地圖

- `scrapers/` 與 `scrapers/private/`：分別存放公開與私有 YAML；兩者都不是存放真實密鑰的地方。
- `templates/`：起始範本（scaffolding），並非已驗證的網站 scraper。
- `skills/stash-scraper-builder/`：撰寫合約與專門參考文件。
- `validator/` 與 `tools/`：schema 驗證、品質檢查、fixture 與審查工具。
- `docs/README.md` 與 `docs/index.yml`：供人工與機器查閱的文件路由。
- `CONTRIBUTING.md`：貢獻與審查流程。

新增的 Markdown 檔案使用兩位數前綴加小寫 kebab-case，並與文件 ID 編號對應（例如 `DOC-QG-21` 對應 `21-quality-gate-rules.md`）。Metadata、ID、索引與格式請依循[文件架構](docs/00-documentation-architecture.md)處理。
