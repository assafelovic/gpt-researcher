# Retriever 配置说明

## 概述

Retriever 可以通过环境变量或配置文件进行默认设置，无需每次请求都传递。

## 配置方式

### 1. 环境变量配置（推荐）

在 `.env` 文件或 `docker-compose.yml` 中设置：

```bash
# 默认的 retriever 配置（支持多个，逗号分隔）
DEFAULT_RETRIEVERS=internal_biblio,tavily

# Internal API 基础 URL（如果使用 internal_biblio）
INTERNAL_API_BASE_URL=http://unob.ivy:8080
```

### 2. Docker Compose 配置

在 `docker-compose.yml` 中：

```yaml
environment:
  # 默认 retriever 配置
  DEFAULT_RETRIEVERS: ${DEFAULT_RETRIEVERS:-internal_biblio,tavily}
  # Internal API 配置
  INTERNAL_API_BASE_URL: ${INTERNAL_API_BASE_URL:-http://unob.ivy:8080}
```

### 3. 配置文件（可选）

在配置文件中设置（需要修改配置加载逻辑）。

## 配置优先级

1. **请求中的 headers**（最高优先级）
   - 如果请求中指定了 `retriever` 或 `retrievers`，使用请求中的值
2. **环境变量 `DEFAULT_RETRIEVERS`**
   - 如果设置了环境变量，使用环境变量的值
3. **自动推断**
   - 如果提供了 `user_id`，默认使用 `internal_biblio,tavily`
   - 如果没有 `user_id`，使用 `RETRIEVER` 环境变量或默认值 `tavily`

## 使用示例

### 示例 1: 使用环境变量配置（推荐）

**设置环境变量：**

```bash
export DEFAULT_RETRIEVERS="internal_biblio,tavily"
export INTERNAL_API_BASE_URL="http://unob.ivy:8080"
```

**API 请求（不需要指定 retriever）：**

```json
{
  "task": "研究任务",
  "report_type": "research_report",
  "report_source": "web",
  "tone": "objective",
  "user_id": "user123"
  // 不需要指定 retriever，会自动使用 DEFAULT_RETRIEVERS
}
```

### 示例 2: 测试脚本（不需要指定 retriever）

```bash
# 使用环境变量配置的默认值
python backend/scripts/submit_task.py \
  -t "研究任务" \
  -u "user123"
```

### 示例 3: 覆盖默认配置

即使配置了默认值，也可以在请求中覆盖：

```json
{
  "user_id": "user123",
  "headers": {
    "user_id": "user123",
    "retrievers": "tavily,google" // 覆盖默认配置
  }
}
```

## 配置选项

### DEFAULT_RETRIEVERS

支持的值：

- 单个 retriever: `"tavily"`, `"internal_biblio"`, `"google"` 等
- 多个 retriever: `"internal_biblio,tavily"`, `"internal_biblio,tavily,google"` 等

**推荐配置：**

```bash
# 混合模式（推荐）：本地数据 + 网络数据
DEFAULT_RETRIEVERS=internal_biblio,tavily

# 只使用本地数据（不推荐，可能数据不全面）
DEFAULT_RETRIEVERS=internal_biblio

# 只使用网络数据
DEFAULT_RETRIEVERS=tavily
```

### INTERNAL_API_BASE_URL

当使用 `internal_biblio` retriever 时，可以配置 Internal API 的基础 URL。

默认值：`http://unob.ivy:8080`

## 完整配置示例

### .env 文件

```bash
# Retriever 配置
DEFAULT_RETRIEVERS=internal_biblio,tavily
INTERNAL_API_BASE_URL=http://unob.ivy:8080

# 其他配置...
AZURE_OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key
```

### docker-compose.yml

```yaml
environment:
  DEFAULT_RETRIEVERS: ${DEFAULT_RETRIEVERS:-internal_biblio,tavily}
  INTERNAL_API_BASE_URL: ${INTERNAL_API_BASE_URL:-http://unob.ivy:8080}
```

## 优势

1. **简化请求**：不需要每次都在请求中指定 retriever
2. **统一配置**：所有请求使用相同的 retriever 配置
3. **灵活覆盖**：仍然可以在请求中覆盖默认配置
4. **环境隔离**：不同环境可以有不同的默认配置

## 注意事项

1. 如果使用 `internal_biblio`，必须提供 `user_id`
2. 环境变量配置后需要重启服务才能生效
3. 如果请求中指定了 retriever，会覆盖环境变量配置
4. 多个 retriever 用逗号分隔，不要有空格（系统会自动处理空格）
