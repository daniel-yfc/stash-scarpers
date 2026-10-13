# Spec V1.0 修正案（2026-10-12 實機探測後）

## 背景

2026-10-12 對目標 Stash（v0.31.1，經 Tailscale）執行 Phase 0.1 環境探測，發現規格 §3、§14 的一個假設不成立。

## 修正

### §3 稽核欄位儲存位置

**原規格**：`prefix_suite_prefix`、`prefix_suite_table_version`、`prefix_suite_confidence`、`prefix_suite_needs_review`、`prefix_suite_alt_codes` 存為 scene custom field。

**修正**：Stash v0.31.1 的 `Scene` type 無 `customFields`（GraphQL introspection 確認）。上述欄位改存外部 JSONL：

```
reports/audit-{task}-{timestamp}.jsonl
```

每行：`{"scene_id": ..., "prefix": ..., "table_version": ..., "confidence": ..., "needs_review": bool, "alt_codes": [...]}`

**影響**：
- `needs_review` 的續跑改為讀取上次 journal，而非查詢 custom field。
- 稽核資料與 Stash DB 分離，備份時需一併保存 `reports/` 目錄。

### §14 外部事實核對結果

| 事實 | 結果 |
|------|------|
| `moveFiles` | ✅ 支援 |
| `metadataClean` paths＋dryRun | ✅ 支援 |
| scene custom field | ❌ 不支援（已修正如上） |
| 多層 studio 行為 | 未驗證，兩層內不影響 |

### 附加發現

13,606／16,374 scenes（83%）無 studio。Enrich 優先級提高。
