# Internal Biblio Retriever

内部文献检索器，用于访问用户特定的文献数据、笔记和 PDF 片段。

## 功能特性

- 支持访问内部 API 获取用户特定的文献数据
- 支持三种类型的数据检索：
  - `biblio`: 文献数据
  - `highlight`: 笔记/高亮
  - `File`: PDF 片段
- 通过 `user_id` 在 headers 中传递，实现用户特定的数据访问

## 使用方法

### 1. 在 WebSocket 请求中设置 headers

在发送 WebSocket 消息时，需要在 JSON 数据中包含 `headers` 字段：

```json
{
  "task": "你的查询问题",
  "report_type": "research_report",
  "report_source": "web",
  "headers": {
    "user_id": "your_user_id",
    "retriever": "internal_biblio",
    "internal_api_type": "biblio"
  }
}
```

### 2. Headers 参数说明

- **user_id** (必需): 用户 ID，用于访问用户特定的数据
- **retriever** (可选): 设置为 `"internal_biblio"` 来使用此 retriever
- **internal_api_type** (可选): 数据类型，可选值：
  - `"biblio"` (默认): 文献数据
  - `"highlight"`: 笔记/高亮
  - `"File"`: PDF 片段
- **internal_api_base_url** (可选): API 基础 URL，默认为 `http://unob.ivy:8080`

### 3. 环境变量配置

也可以通过环境变量设置默认的 API 基础 URL：

```bash
export INTERNAL_API_BASE_URL=http://unob.ivy:8080
```

### 4. 使用示例

#### 示例 1: 检索文献数据

```json
{
  "task": "查找关于机器学习的相关文献",
  "report_type": "research_report",
  "report_source": "web",
  "headers": {
    "user_id": "user123",
    "retriever": "internal_biblio",
    "internal_api_type": "biblio"
  }
}
```

#### 示例 2: 检索笔记

```json
{
  "task": "查找我的相关笔记",
  "report_type": "research_report",
  "report_source": "web",
  "headers": {
    "user_id": "user123",
    "retriever": "internal_biblio",
    "internal_api_type": "highlight"
  }
}
```

#### 示例 3: 检索 PDF 片段

```json
{
  "task": "查找相关 PDF 内容",
  "report_type": "research_report",
  "report_source": "web",
  "headers": {
    "user_id": "user123",
    "retriever": "internal_biblio",
    "internal_api_type": "File"
  }
}
```

#### 示例 4: 组合使用多个 retriever（推荐）

**混合模式**：同时使用 internal_biblio 和外部 retriever（如 tavily），确保数据全面性。

```json
{
  "task": "综合搜索",
  "report_type": "research_report",
  "report_source": "web",
  "headers": {
    "user_id": "user123",
    "retrievers": "internal_biblio,tavily",
    "internal_api_type": "biblio"
  }
}
```

**优势：**

- 本地数据（internal_biblio）：用户特定的文献、笔记、PDF 片段
- 外部数据（tavily）：补充最新的网络信息，确保数据全面性
- 系统会并行调用所有 retriever，然后合并结果

**其他组合示例：**

```json
// 三个 retriever 组合
{
  "headers": {
    "user_id": "user123",
    "retrievers": "internal_biblio,tavily,google",
    "internal_api_type": "biblio"
  }
}

// 只使用本地数据（不推荐，可能数据不全面）
{
  "headers": {
    "user_id": "user123",
    "retriever": "internal_biblio",
    "internal_api_type": "biblio"
  }
}
```

## API 端点

Retriever 会调用以下 API 端点：

```
POST {base_url}/internal/biblios/vector_search/
```

返回项可能是向量检索格式，例如：

```json
{
  "content": "....",
  "metadata": { "biblio_id": 123 },
  "score": 0.87
}
```

Retriever 会优先从 `href/url/id` 取标识符；如果不存在，会从 `metadata.biblio_id`（以及 `highlight_id/file_id/...`）取 **id** 作为标识符（不会强行拼不可访问的 URL）。 

其中：

- `base_url`: 默认为 `http://unob.ivy:8080`，可通过 headers 或环境变量配置
- `type`: `biblio`, `highlight`, 或 `File`
- `user_id`: 从 headers 中获取
- `query`: 搜索查询

## 返回格式

API 需要返回以下格式之一：

### 标准格式（推荐）

直接返回数组：

```json
[
  {
    "href": "source_url_or_id",
    "body": "content_text"
  },
  {
    "id": "another_id",
    "content": "another_content"
  }
]
```

### 包装格式

也可以包装在对象中：

```json
{
  "results": [
    {
      "href": "source_url_or_id",
      "body": "content_text"
    }
  ]
}
```

或使用 `data` 或 `items` 作为键名。

### 字段要求

**每个结果对象必须包含：**

1. **标识符字段**（必需）：`href`, `url`, 或 `id` 之一
2. **内容字段**（必需）：`body`, `content`, 或 `text` 之一

**字段映射：**

- 标识符：`href` → `url` → `id` → `source` → `link`
- 内容：`body` → `content` → `text` → `abstract` → `description` → `snippet`

**注意：** 如果某个结果缺少标识符或内容字段，该结果会被跳过并记录警告日志。

### 最终转换格式

Retriever 会将所有格式统一转换为：

```python
[
    {
        "href": "source_url_or_id",  # 来自 href/url/id 字段
        "body": "content_text"       # 来自 body/content/text 字段
    },
    ...
]
```

## 引用处理

### href/id 字段在引用中的使用

当 API 返回 `id` 或 `href` 字段时，该值会被用于生成报告中的引用。引用格式如下：

```markdown
## References

- [identifier](identifier)
```

**重要说明：**

1. **如果返回的是 ID**（如 `"doc123"`）：

   - 引用会显示为：`- [doc123](doc123)`
   - 这不是可点击的 URL，只是一个标识符
   - 建议：如果可能，返回完整的 URL 或可访问的链接

2. **如果返回的是 URL**（如 `"https://example.com/doc123"`）：

   - 引用会显示为：`- [https://example.com/doc123](https://example.com/doc123)`
   - 这是可点击的超链接

3. **最佳实践**：
   - 优先返回完整的 URL，这样引用会是可点击的链接
   - 如果只能返回 ID，可以考虑在 API 端生成一个可访问的 URL
   - 例如：`"https://your-system.com/view/doc123"` 而不是 `"doc123"`

### 引用生成流程

1. 搜索结果中的 `href` 字段会被收集到 `visited_urls` 集合中
2. 在报告生成时，所有 `visited_urls` 中的值会被添加到报告末尾的 "References" 部分
3. 每个引用格式为：`- [href_value](href_value)`

## 错误处理

- 如果 `user_id` 未提供，retriever 会抛出 `ValueError`
- 如果 API 请求失败，retriever 会返回空列表并记录错误日志
- 如果返回的数据格式不符合预期，retriever 会尝试自动转换

## 注意事项

1. **user_id 必需**: 必须在 headers 中提供 `user_id`，否则 retriever 无法工作
2. **网络访问**: 确保服务器可以访问内部 API 端点 (`unob.ivy:8080`)
3. **超时设置**: API 请求的超时时间为 30 秒
4. **数据格式**: Retriever 会自动处理不同的 API 响应格式，但建议 API 返回标准格式
