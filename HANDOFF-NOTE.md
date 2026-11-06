# PR #93 Lease-03 Proxy — 去敏證據集 QA 交接包 v1（2026-11-06）

來源：分支 `docs/qa-pr93-gateb-proxy-20261103` HEAD `80f53073384214da2db902038b3e49c805a110bf`（62 檔）。
內容：去敏證據集 `sanitized/`（62 檔）、五份報告、原始↔去敏 SHA-256 對照表、雙層 manifest、三份 custody 文件更正版、掃描/去敏/驗證腳本（可重播）。

給獨立 Reviewer：請依 `PR93-LEASE03-SECURITY-QA.md` 之交接清單獨立重跑（原始雜湊重算、雙樹掃描、XPath 重播、對照抽核），並簽署終局 verdict。
現況：修復者分類為「無 CONFIRMED_SECRET」；本包**不含**原始證據 bytes（請自來源分支 pin HEAD 取得）、不含任何秘密原值。
未關閉：原封存 ZIP（67 entries）與 BRAVO.zip 二進位保管缺口；本包發布至公開分支須待 QA 通過＋Controller 核准。
