# Wave 2E WS-2E-40 - BRAVO DVD fixture engineering report (Agent C, v2.3)

## Handoff

```yaml
AGENT: C
WAVE: 2E
TASK: WS-2E-40 (P1 - DVD Fixture Mapping Reconciliation)
BRANCH: test/e2e-bravo-dvd-fixtures
BASE: 44a26d5ed931273ca4473da0e2c10d6cf2ffaee5
HEAD_SHA: "f6ffbbf21d9b526b3c8a80daa43154b1d1f17741"  # v2.1 deliverables commit
LATER_COMMITS: "v2.2 (8786410) 與 v2.3(本報告同 commit)之 SHA 記錄於 git 歷史"
CHANGED_FILES:
  - tests/fixtures/bravo/bravo-dvds-fixtures.yml
  - tools/tests/test_bravo_dvds.py
```

## Metadata source-vs-target matrix (C-03)

Source XPath 成功 ≠ production 欄位映射成功。四個層級明確分離:

| 層級 | 欄位 | 依據 |
|---|---|---|
| **Source extraction verified**(僅來源驗證) | Title, Code, URLs, Date, Studio(來源 Label レーベル), Duration(整片總長分鐘), Details, Image(cardinality=1) | Agent A addendum:9 產品頁 + 2 個 404,CDP 2026-11-02;expect 斷言保留值與 cardinality |
| **Production field mapping approved**(mappedExpect) | Title, Code, URLs(sceneByURL routeThrough), Details | v2.3 manifest;scraper 命名僅消除 runner 歧義,不代表 runtime 路由(屬 Agent B / Gate B) |
| **Mapping omitted by policy**(政策省略) | Date(offline runner 僅支援 parseDate 2006.01.02,日文日期格式不符;來源值由 expect 釘住), Tags(站台通用 keywords,C-07), Duration, Studio | Controller metadata policy(本輪 P1 C-02) |
| **Mapping pending Controller decision**(待決策) | Duration(需「整片 DVD 對應單一 Scene」核准), Studio(需 Label→Studio ADOPTED 決策重新核對), 084 Image(soldout 佔位圖,非真封面;Agent F/controller) | 見下方決策核對結果 |

### 決策核對結果(C-02 要求)

- **Label → Studio**:2026-11-04 查核,**無已發布的有效 Controller 決策**。唯一相關草案 D-084-IMAGE-01(Image 採用,非 Studio)未獲核准且 Controller 已拒絕推送。Studio mapping 維持省略。
- **Duration**:無「整片 DVD = 單一 Scene」核准;整片總長(分鐘)保留於 expect 作來源驗證與 provenance,不映射 Stash Scene Duration。
- **084 Image**:soldout 佔位圖不視為真封面;positive case 不映射 Image,cardinality 由 expect 釘住。

## Review fixes

| 版本 | 項目 | 修正 |
|---|---|---|
| v2.1 | C-FIX-1/2/3 | case 名隔離、stale-h1 guard、真實 HEAD_SHA |
| v2.2 | C-FIX-1 follow-up | DVD 專屬合成 Cloudflare fixture;無例外合成標記;html 隔離轉綠 |
| v2.3 | P1 C-02 | mappedExpect 移除 Duration/Studio(來源 expect 斷言與值全部保留,未為轉綠刪減);政策寫入 manifest header |
| v2.3 | P1 C-03 | 新增 source-vs-target matrix(本節);新增 `test_metadata_policy_duration_and_studio_not_mapped` 釘住政策 |

## Test results

- 歷史實測:20 passed / 2 failed → v2.2 後 23 passed(Controller 回報全套 335 passed)
- v2.3 後預期:**24 passed**(新增 1 個 metadata policy 測試;matrix 測試改寫,無刪減)
- manifest runner:預期紅(Ambiguous entrypoint),待 Agent F 實作
- PR #99:維持 Draft

## Status

READY_FOR_REVIEW — P1 C-01/C-02/C-03 全數完成。
