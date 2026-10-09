---
doc_id: DOC-INTEGRATION-81
title: Stash GraphQL API Reference
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - graphql
  - api
  - identify
last_verified: "2026-10-10"
authority: reference
routing:
  intents:
    - graphql
    - stash-api
    - api-reference
    - identify
---

# Stash GraphQL API 參考

StashApp 的 GraphQL 就是它的主要 API。以下內容已對照官方文件與 repo 的 schema（develop 分支）確認。與 scraper 工作的關聯：scraper 產出的欄位（Studio、URLs、Performer 等）最終經由這些 mutation 寫入，理解 schema 有助於對齊欄位語義與 Identify 行為。

## 連線方式

- **端點**：`POST http://localhost:9999/graphql`（所有請求都是 POST）
- **認證**：header `ApiKey`（官方推薦）。金鑰在 Settings > Security > Authentication 產生，或用 `generateAPIKey` mutation。舊的 `/login` cookie 登入已過時。
- **Playground**：Settings > Tools > GraphQL playground。schema 是 introspective 且自我文件化的，直接在裡面查欄位。
- 官方文件沒寫 rate limit。

## Schema 組織（graphql/schema/）

- `schema.graphql` 定義頂層 Query / Mutation / Subscription。
- 型別拆在 `types/` 下 29 個檔案：scene、performer、studio、tag、group、gallery、image、filters、scalars、scraper 等。
- **常用 Query**：`findScene(s)`、`findPerformer(s)`、`findStudio(s)`、`findTag(s)`、`findGallery/Galleries`、`findImage(s)`、`findGroup(s)`、`stats`、`version`、`scrapers`。
- **常用 Mutation**：實體 CRUD（`sceneCreate` / `sceneUpdate` / `scenesUpdate`…）、`metadataScan` / `metadataAutoTag` / `metadataGenerate` / `metadataExport|Import`、`sceneGenerateScreenshot`、`backupDatabase`、`configure*` 系列。
- **過濾**：`FindFilterType`（`q` 全文搜尋、`page`、`per_page`（-1 取全部，預設 25）、`sort`、`direction`）；各 FilterType 支援 `AND` / `OR` / `NOT` 巢狀；欄位比對用 `CriterionModifier`（`EQUALS`、`GREATER_THAN`、`IS_NULL`、`INCLUDES_ALL`…）。
- `GenderEnum` 就是 scraper 那邊的六值：`MALE`、`FEMALE`、`TRANSGENDER_MALE`、`TRANSGENDER_FEMALE`、`INTERSEX`、`NON_BINARY`。
- `graphql/stash-box/query.graphql` 是呼叫外部 stash-box API 的範例查詢。

## Mutation 簽名（develop 分支 schema，逐字確認過）

```graphql
sceneCreate(input: SceneCreateInput!): Scene
sceneUpdate(input: SceneUpdateInput!): Scene
scenesUpdate(input: [SceneUpdateInput!]!): [Scene]  # 批次
performerCreate(input: PerformerCreateInput!): Performer
performerUpdate(input: PerformerUpdateInput!): Performer
groupCreate(input: GroupCreateInput!): Group
groupUpdate(input: GroupUpdateInput!): Group
tagCreate(input: TagCreateInput!): Tag
tagUpdate(input: TagUpdateInput!): Tag
```

## 關鍵規則

- **必填**：Performer / Group / Tag 的 Create 都要 `name`；SceneCreate 全選填。所有 Update 都要 `id`。
- **關聯欄位**（`tag_ids`、`performer_ids`、`gallery_ids`、`parent_ids`、`child_ids`）是普通 `[ID!]` 清單，Update 時整份取代，不是增量加。
- **只有兩個是巢狀**：Scene→groups 用 `[{ group_id, scene_index }]`；Group→containing/sub_groups 用 `[{ group_id, description }]`。
- **已棄用欄位別用**：`url` → `urls`，`movies` → `groups`，`o_counter` → 專用 increment mutation。
- `custom_fields` 在 Create 是 `Map`，Update 是 `CustomFieldsInput`（full 取代 / partial 部分更新 / remove 刪鍵）。

## 可直接跑的範例

```graphql
mutation {
  createdTag: tagCreate(input: { name: "My Tag", parent_ids: ["7"] }) {
    id
    name
  }
  updatedScene: sceneUpdate(
    input: {
      id: "123"
      rating100: 80
      organized: true
      performer_ids: ["2"]
      tag_ids: ["3", "4"]
      groups: [{ group_id: "5", scene_index: 1 }]
    }
  ) {
    id
    title
  }
}
```

```bash
# curl 格式沿用官方文件
curl -X POST -H "ApiKey: <key>" -H "Content-Type: application/json" \
  --data '{ "query": "mutation { tagCreate(input: { name: \"My Tag\" }) { id name } }" }' \
  localhost:9999/graphql
```

文件上的 curl 範例（API Key 版）：

```bash
curl -X POST -H "ApiKey: <your_api_key>" -H "Content-Type: application/json" \
  --data '{ "query": "<graphql_query>" }' localhost:9999/graphql
```

最小可用查詢：`{ version { version } }`。複雜的 filter 形狀建議直接在 playground 的 Documentation Explorer 對著寫。欄位細節在 playground 的 Documentation Explorer 都查得到，input 型別跟上面一致。

## 來源

- API 文件 schema 主檔：https://docs.stashapp.cc/api/
- schema.graphql：https://github.com/stashapp/stash/blob/develop/graphql/schema/schema.graphql
- graphql 目錄：https://github.com/stashapp/stash/tree/develop/graphql
