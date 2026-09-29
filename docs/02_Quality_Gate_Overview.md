---
doc_id: DOC-QG-20
title: Quality Gate Overview
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - ci
last_verified: "2026-09-29"
authority: canonical
routing:
  intents:
    - quality-gate
    - validation
---

# Scraper 品質管線總覽

## 目的

本文件提供品質管線的高层概覽。詳細規則以 [`03_Quality_Gate_Rules.md`](03_Quality_Gate_Rules.md) 為準；渲染後 DOM 檢查以 [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) 為準。

## 驗證層級

| 層級 | 工具 | 證明範圍 |
|---|---|---|
| Schema | `npm run validate` | YAML 符合官方 schema |
| URL ordering | `npm run validate-sort` | URL array 排序 |
| Repository policy | `bash tools/validate-all.sh` | 命名、公開 cookies、fragment、日期政策 |
| Raw scrutiny | `node tools/scrutiny.js scrapers/<Scraper>.yml --search` | HTTP 加 JSDOM；不執行站點 JavaScript |
| Fixture control | `node tools/verify-scraper-fixtures.mjs --self-test` | 檢查器本身；不是站點 fixture 證據 |
| Evidence labels | `python tools/check_evidence_labels.py` | 拒絕缺少 artifact 的驗證聲稱 |
| CDP claim gate | `python tools/check_live_cdp_status.py` | 失敗閉合；不是 live Stash 執行 |

綠色 CI 不代表 live selector、rendered-DOM fixture 或 production readiness。

**最後更新**: 2026-09-29
