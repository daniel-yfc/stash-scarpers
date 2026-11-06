# PR93-LEASE03 獨立安全 QA — 測試紀錄（2026-11-06）

工作區：`~/workspace/review/pr93-lease03-qa-20261106/`
原始來源：遠端分支 `docs/qa-pr93-gateb-proxy-20261103` pin HEAD `80f53073384214da2db902038b3e49c805a110bf`，唯讀 worktree `raw-80f5307/`；歸檔分支 `docs/pr93-lease03-proxy-historical-review-20261105` HEAD `96f71948726246f006255e4448a34da96c300ab0`，唯讀 worktree `archive-96f7194/`。
受審包：`~/workspace/user/files/PR93-LEASE03-SANITIZED-PACKAGE-20261106-v1_0_7bge.zip`，SHA-256 `b0fd77315a8a2921b349abb8448a413b1f8a4a5ebc6d0de8131cab28246414dc`。

## T1. 來源 pin 與 Git 暴露

- `git ls-remote origin docs/qa-pr93-gateb-proxy-20261103` → `80f53073384214da2db902038b3e49c805a110bf`，與修復者 pin 一致。
- 全量 fetch 後（50 遠端分支＋tags）：`git branch -r --contains 80f5307` 僅 `origin/docs/qa-pr93-gateb-proxy-20261103`；`git tag --contains` 無。
- GitHub API：`forks_count: 0`，`private: false`，forks 列表 0 筆。
- 來源 4 commits：`3b36c43`、`ed93399`、`3e09b91`、`80f5307`。

## T2. Manifest 驗證

| 檢查 | 命令 | 結果 |
| --- | --- | --- |
| B1 原始 MANIFEST-LIVE | `sha256sum -c MANIFEST-LIVE.sha256`（原始 evidence 目錄） | 56/56 OK，0 失敗 |
| B2 原始 62 檔清單 | `sha256sum -c PRIVATE-RAW-MANIFEST.sha256`（原始 repo 根） | 62/62 OK，0 失敗 |
| B3 去敏 62 檔清單 | `sha256sum -c PUBLIC-SANITIZED-MANIFEST.sha256`（去敏樹） | 62/62 OK，0 失敗 |
| B3 去敏 MANIFEST-LIVE | `sha256sum -c MANIFEST-LIVE.sha256`（去敏 evidence 目錄） | 56/56 OK |

## T3. 對照表與 JSON（`qa_mapping_check.py`）

- 62 列；原始／去敏 SHA 皆與重算值相符，mismatch NONE。
- 轉換分布：`none (byte-identical copy)` 50；`tailnet_ip_redacted x1; internal_hostname_redacted x1` 1；`file_share_url_redacted x5` 1；`file_share_url_redacted x1` 4；`manifest_regenerated_for_sanitized_bytes` 1；`tailnet_ip_redacted x1` 4；`tailnet_ip_redacted x1; file_share_url_redacted x1` 1。合計轉換 12。
- JSON 解析：原始／去敏各 39 份，0 失敗。

## T4. XPath 重播（`qa_xpath_replay.py`，selector 直接讀自來源 HEAD `scrapers/BRAVO_JAPAN.yml`）

- 282／284 兩頁：Title／Code／URLs／Tags／Details／poster，原始＝去敏，全部相同。
- 與 `field-summary.json` 預期值逐項相符：title、code、urls、details_len（282: 65、284: 61）、tags_n 9、image null、details 前綴。REPLAY FAILS: NONE。
- 修復者 `validate_sanitized.py` 重跑（symlink run 目錄）：JSON 0 失敗；兩頁重播 True；6 份轉換 JSON 套用同一去敏規則後語義相等，全部 True。

## T5. Secret scan

- Gitleaks 8.21.2（QA 自行下載 `gitleaks_8.21.2_linux_x64.tar.gz`，`./gitleaks version` → 8.21.2）：原始樹 `no leaks found`，去敏樹 `no leaks found`。
- 修復者 `scan_custom.py` 重跑（輸出改道，不覆寫交付檔）：原始樹 399（cdp_ws 6、cookie_header 4、email 86、internal_host 1、long_hex_token 216、rfc1918 2、tailscale_ip 6、wix_session 78）；去敏樹 398（cdp_ws 6、cookie_header 4、email 86、internal_host 6、long_hex_token 216、rfc1918 2、wix_session 78）。交付之 `custom-scan-findings.json` 為去敏樹 398，與重跑一致。
- QA 自撰掃描（`qa_sweep.py`，18 類不同 regex）：原始／去敏兩樹 Authorization／Basic／JWT／API key／password／secret／PEM 私鑰／cookie 值／GraphQL 認證標頭／AWS key 皆 0；bearer／GitHub token 皆 0（以檔案計數 `qa_sweep_counts.json` 核實）；tailnet IP 原始 6 → 去敏 0；分享連結原始 10 → 去敏 0；CDP 路徑字串兩樹皆 6（IP 已去，路徑保留屬設計）；email 形命中皆為 Sentry DSN。
- Repo 自帶 `tools/scan_session_material.py`（來源 HEAD 版，全 431 追蹤檔）：僅標示兩份 Page HTML 為 `REPLAYABLE_AUTH_ASSIGNMENT`，其餘 0。QA 以結構化探針追蹤至 QA-N1（見報告 §2.3）。

## T6. 分類逐項核對

- F-01：6 處位置與 FINDINGS.yaml 逐一相符（見報告 §2.2）。
- F-02：1 處（Handoff yaml:9）；去敏樹同位置為 `stash-test-host` 標記。
- F-03：10 處分布逐一核對（install-record.json ×5、installedPackages.json ×1、rollback-log.json ×1、gateb-index3.yml ×1、proxy_install.py ×1、proxy_rollback.py ×1）；去敏樹 0；連結未存取。
- F-04：instanceId 兩頁共 40 處、distinct 19（兩種獨立擷取一致；修復者稱 21 有誤，QA-N2）。
- F-05：全樹 session 類盤點（`qa_session_inventory.py`）：quoted-UUID sessionId 各頁 2 處（L880／L952；282 sha12 `a7d1adab33a0`、284 sha12 `dffb3e73c870`）；sessionId code-expr 各頁 4 處；mpaSessionId code-expr 各頁 2 處、無值；svSession／wixSession2／wixSession3／smSession 僅名稱、無值；sessionId UUID ≠ 任何 instanceId。L952 上下文（值已遮蔽）為 Wix viewerModel site 描述子（metaSiteId、siteId、externalBaseUrl、siteType UGC、dc virginia-pub、editorName Unknown、isSEO false）。
- F-06：兩頁 L87 為 Wix Thunderbolt `handleAccessTokens` bundle script 標籤＋框架程式碼；全樹無 cookie 值。
- F-07：兩頁 L843 為 SVG `<path d="M523.2 259a39 39 …">` 座標資料。
- F-08：email 形命中全為 Sentry DSN URL（`https://<32ch>@sentry.io`／`sentry.wixpress.com`）。
- F-09：長 hex 兩樹皆 216（修復者稱 224 有誤，QA-N3）。

## T7. Custody 文件比對

- `diff archive-96f7194/docs/qa/<file> custody-docs-updated/<file>`（3 份）：皆僅附加補登，歷史文字未動。CUSTODY 文件 status 行正確更新；REVIEW 文件補登句同值重述（QA-N5）；HANDOFF yaml 僅附加 `SECURITY_REMEDIATION_20261106:` 區塊。
- 原件查核：`docs/qa-pr93-gateb-proxy-20261103@80f5307`、MANIFEST-LIVE 56/56、封存 ZIP（67 entries／836,389 bytes）與 BRAVO.zip「仍未取得」、ce7ef6c FAIL、88d27a5 PASS、G0 ACCEPTED_CLOSED，六項皆保留。

## T8. 未執行事項（邊界）

- 未存取 muse.ai 分享連結；未 force-push／刪分支／合併／部署／操作 Stash；未修改原始證據分支；未以重播方式驗證任何可能有效之秘密。
- 原封存 ZIP 與 BRAVO.zip 二進位不在本輪證據範圍（未取得），缺口維持 open。
