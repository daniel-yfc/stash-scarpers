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

本儲存庫用於製作與驗證 Stash 擷取器 YAML，並非 Stash 主程式或 CommunityScrapers。Schema 與 validator 的上游關係見 [來源紀錄](skills/stash-scraper-builder/references/UPSTREAM_SOURCES.md)。此譯本協助操作；schema、工具與各主題的權威文件仍是判定依據。範本、schema 通過或 CI 綠燈，都不等於網站實測通過。

## 建置流程

1. 先讀 [AGENTS.md](AGENTS.md)、[SKILL.md](skills/stash-scraper-builder/SKILL.md) 與 [閱讀順序](skills/stash-scraper-builder/references/skill-read-order.md)；再按需求讀 [來源選擇](skills/stash-scraper-builder/references/source-selection.md) 與 [機密政策](skills/stash-scraper-builder/references/phase0-secrets-policy.md)。
2. 檢查目標網站真正的 URL、回應格式、語系及存取限制，保存來源 URL 與日期。不要虛構搜尋端點、模式或 selector；無法存取時標記 `UNVERIFIED`。
3. 從 [templates/](templates/README.md) 或已驗證的相近檔案起步。公開 YAML 放在 `scrapers/<CamelCaseName>.yml`，保留根層 `name:`；不得在任何版本、fixture 或報告內重現憑證、cookie、token 或瀏覽器設定檔內容。
4. 選用已證實足夠的最簡執行方式：XPath → 真正的 JSON 回應 → 必要的 script → 必須渲染或獲准互動時才用 CDP。HTML 中內嵌 JSON 不會自動變成 `scrapeJson` 可讀的 JSON 回應。僅實作網站確實支援的入口，保留來源語言。
5. 對完整目標頁測試，先排除挑戰頁、登入閘門、HTTP 錯誤與部分渲染。每個已設定的搜尋模式需檢查有結果的搜尋頁、結果 URL 及獨立詳情頁；另測可選欄位缺失、版面變體與適用的語系。參照 [測試指南](docs/06_Testing_Guide.md) 與 [渲染 DOM fixture 指南](docs/07_Rendered_DOM_Fixture_Testing.md)。
6. 保存證據與未解問題；只有滿足 [A–H 生產閘門](docs/04_Production_Gate.md)的證據，才能主張生產就緒。把事故與實頁失敗回饋到規則、fixture 與測試。

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
python tools/check_live_cdp_status.py
python tools/check_scraper_docs.py
python tools/check_docs_index.py
npm run format:check
```

`--self-test` 只測試 runner；沒有提交 manifest 時，發現程序應回報 `UNVERIFIED`。要要求特定 manifest，執行 `python tools/run_fixture_manifests.py --expect tests/fixtures/<scraper>-fixtures.yml`。fixture 通過僅代表其中實際存在的案例與斷言通過，不代表所有搜尋模式已涵蓋。格式化是本機檢查，沒有執行就不可宣稱通過。

網站允許且可直接取得時，分別檢查搜尋與詳情頁的原始 HTTP 回應：

```bash
node tools/scrutiny.js scrapers/<Scraper>.yml --search
node tools/scrutiny.js scrapers/<Scraper>.yml --url="<detail-url>"
```

此工具以 HTTP 加 JSDOM 檢查，不執行網站 JavaScript；需渲染的頁面另以瀏覽器 DOM 或 live Stash/CDP 驗證。遵守存取限制，不繞過閘門。

## 證據與測試案例

逐一記下擷取器路徑、修訂版、日期、來源 URL、回應種類（原始 HTTP、JSON、渲染 DOM、live Stash/CDP）、存取狀態、實際命令與結果、欄位預期值與實得值、尚未驗證的 selector。建議案例包含有版面差異時的兩筆詳情、每種已設定搜尋模式的有結果頁與詳情結果、可選欄位缺失案例，以及適用的語系斷言；挑戰或錯誤頁要獨立分類。XPath fixture 應斷言匹配數量及代表值。這些撰寫期望不全是 runner 強制規則。

務必分開記錄 schema、URL 排序、政策閘門、自動測試、快照／fixture、live-search、live-detail 與生產就緒；未執行或遭封鎖的項目標為 `UNVERIFIED`。使用 [實測狀態](docs/LIVE_TEST_STATUS.md) 與 [報告範本](docs/test-report-template.md)記錄來源和限制。歷史 [evidence/](evidence/) 不是現行政策，清單或審計建議也不能代替測試。
