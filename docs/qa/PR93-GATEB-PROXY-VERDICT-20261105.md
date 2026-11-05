# Agent D 判讀 — PR #93 Lease-03 Proxy 證據包（凍結 HEAD ce7ef6c）

- 判讀日期：2026-11-05
- 判讀者：Agent D（獨立 QA）
- 對象：~/workspace/qa-pr93-gateb-proxy-20261103/（MANIFEST-LIVE 56 檔、PR93-GATEB-PROXY-HANDOFF-20261104.yaml）
- 裁決（僅對本包、僅對 ce7ef6c）：**GATE_B_FAIL / BASELINE_BLOCKED_LIVE_QA**
- 唯一驅動項：DEF-01 — Duration 在 B1/B2 六次擷取與 B5 QueryFragment 路徑全為 null，不符本 assignment 當時有效的驗收值 1800。

## Agent D 獨立驗證依據（非採信 handoff 摘要）

- 完整性：自行重跑 sha256sum -c — MANIFEST-LIVE 56/56 OK；pkgbuild/BRAVO.zip 雜湊 cdb9d2c5…de78 與 handoff 逐字相同、ZIP 僅含 BRAVO.yml；證據 zip 836,389 bytes／67 entries 相符。
- B0：installedPackages 實載 BRAVO = ce7ef6c（隔離來源）、共 21 件；listScrapers 單一 BRAVO、supported=[URL]、僅 clips 網址。
- B1/B2 原始 response 逐筆回讀（6/6）：Title/Code/URLs 全對；Details 61 字（284）／65 字（282）、產品專屬互不相同、另做 codepoint 檢查確認無 U+200B → DEF-02 在本包證據下 CLOSED；Duration 6/6 null；Image 全空。
- B4：live 999999 核心欄位全 null（fail-closed 成立）、僅 URLs 回顯 + 9 個站台通用 Tags；fixture missing-title 為 repo 測試層證據（11 passed），紀錄誠實標明 lxml $desc 限制未用作證據。
- B5：QF 有效路徑回 284 正確結果（Duration 同為 null）；兩個空 Title 變體皆安全報錯（{url} 無法載入），無假 URL。
- B6：KOShop 控制案回凍結值（ナマ狂い種壺待機／BWB365_DVD）；fixture manifest SHA be1885d2… 與 assignment 指定值一致；/dvds/284 upstream panic 獨立分類、未歸責 PR #93。
- Rollback：restoration-comparison 五項全 true、stats 前後同為 15、lease-03 已釋放、零 Scene 持久化。

## 保留事項

- 範圍綁定：本裁決只對 ce7ef6c 與當時契約（Duration 驗收值 1800）成立。其後 HEAD 88d27a5 已在修訂後契約（Duration 不對映、defer 決策）下通過 focused 重跑，PR #93 亦已合併 — 本 FAIL 不得解讀為現行版本的 Gate B 結果。
- B3 poster-present 分支維持 UNVERIFIED_BRANCH：本包因 CDP tunnel 逾時改以 page-HTML 證據，兩頁皆無 poster 屬性；不把「無 poster 分支通過」升級為 poster 路徑已驗證。
- B4 的 999999 Tags 非空屬原始事實紀錄、非本次裁決驅動項（核心欄位 fail-closed 且無持久化），但值得 Controller 留意（後續 DVD 契約已以不對映 Tags 處理同型問題）。
- 與 Agent D 本人 v3 裁決（同 HEAD、GATE_B_FAIL、DEF-02 closed／DEF-01 open）結論一致，但本判讀僅立基於 Proxy 包的原始證據 — 兩次獨立執行收斂到同一結論，是互相印證而非互相引用。
