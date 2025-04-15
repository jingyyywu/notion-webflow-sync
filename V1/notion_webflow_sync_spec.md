# Notion → Webflow 增量同步系统规范

本系统用于将 Notion 中的多个结构化数据库（如 posts、tags、tag_types）同步到 Webflow 的 CMS Collections 中，支持自动处理：

- 新增字段的结构更新
- 新建与更新的内容同步
- 删除项的清理
- 多层级 relation 的准确绑定

---

## 🧱 系统总流程（分两阶段）

### 🔹 阶段一：Schema 检查 + Create & Delete

目的：**确保所有 Notion 数据项都先在 Webflow 中注册为占位符，便于后续建立 relation**

流程：

```
for each Notion database:
    1. 检查字段结构是否有变动
        - 若有：调用 Webflow API 添加新字段
        - 并记录新的字段结构到 schema_store/{database}.json

    2. 拉取该数据库所有当前存在的 Notion item

    3. 读取 mapping.json 中已有的 notionID → webflowID 映射记录

    4. 比对差异，得出：
        - createQueue: mapping 中不存在的 notionID
        - deleteQueue: mapping 中存在，但已不在 Notion 当前返回中的 notionID

    5. 执行操作：
        - 创建 createQueue 中的 Webflow item（字段留空，仅记录 notionID）
        - 删除 deleteQueue 中的 Webflow item，并清除对应 mapping
        - 更新 mapping.json（新增或移除记录）
```

---

### 🔹 阶段二：字段内容填充（包括 relation）

目的：**完成所有字段的数据同步，包括文字、选择项、relation 关联等**

流程：

```
for each Notion database:
    1. 读取最新的 Notion 数据（或复用阶段一结果）

    2. 读取最新的 mapping.json

    3. 对每个 item 判断是否需要更新：
        - 若 last_edited_time > lastSyncedAt → 加入 updateQueue

    4. 对 updateQueue 中每一项：
        - 使用 mapping 表将所有 relation 从 notionID 替换为 webflowID
        - 构建字段值 payload
        - 调用 Webflow API 进行 patch 更新
        - 更新该项在 mapping.json 中的 lastSyncedAt
```

---

## 📦 数据存储结构

### `mapping.json`

记录每个同步过的 Notion item：

```json
{
  "N001": {
    "webflowID": "W001",
    "lastSyncedAt": "2025-04-13T08:30:00Z"
  }
}
```

### `schema_store/{database}.json`

记录每个 Notion 数据库上一次同步时的字段结构：

```json
{
  "title": { "type": "title" },
  "tags": { "type": "relation", "target": "tags" },
  "post_author": { "type": "text" }
}
```

---

## 🔄 Notion 与 Webflow 字段类型映射建议

| Notion Type     | Webflow Type         | 说明                          |
|------------------|----------------------|-------------------------------|
| `title`         | `plain_text`         | 标题字段                      |
| `text`, `rich_text` | `plain_text`     | 普通文本                      |
| `select`        | `option`             | 单选项                        |
| `multi_select`  | `multi_option`       | 多选项                        |
| `relation`      | `reference`          | 关联另一个 Collection（用 webflowID）|
| `number`        | `number`             | 数值                          |
| `date`          | `plain_text`         | 作为字符串处理或扩展后处理     |

---

## 🧠 重要判断逻辑

### 判断是否为新建：

```ts
if (notionID ∉ mapping):
    → create item in Webflow
```

### 判断是否为更新：

```ts
if (notionID ∈ mapping) and (last_edited_time > lastSyncedAt):
    → update item fields
```

### 判断是否被删除：

```ts
if (notionID ∈ mapping) and (notionID ∉ 当前 Notion 数据列表):
    → delete item in Webflow + remove from mapping
```

---

## 🛡️ 错误处理建议

- 所有 API 调用添加 retry（最多 3 次）
- 每次操作生成同步日志 `sync.log.json`
- 错误项加入 `sync.errors.json` 等待后续人工或系统重试

---

## 📚 后续扩展支持

- Webflow slug 自定义生成逻辑
- 子项/父项（subitem/parent）结构自动构建
- 同步 Notion 中的排序字段
- 多语言字段支持（如 title_en, title_zh）

---

## ✅ 同步触发入口（伪函数）

```ts
async function syncAllDatabases(databases) {
  // Phase 1: Create & Delete
  for (const db of databases) {
    await syncPhase1_CreateDelete(db);
  }

  // Phase 2: Update fields
  for (const db of databases) {
    await syncPhase2_UpdateFields(db);
  }
}
```