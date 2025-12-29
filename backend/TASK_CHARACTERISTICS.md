# GPT-Researcher 任务特性分析

## 任务类型：I/O 密集型（网络等待）

### 主要操作分析

#### 1. 网络 I/O 操作（占 90%+ 时间）

**LLM API 调用**：

- OpenAI/Azure OpenAI API 调用
- 每次调用等待时间：1-10 秒
- 一个报告可能需要 10-50+ 次 API 调用

**搜索 API 调用**：

- Tavily API（网络搜索）
- Google Search API
- 内部 API（internal_biblio）
- 每次调用等待时间：0.5-3 秒

**网页抓取**：

- 使用浏览器抓取网页内容
- 等待页面加载和渲染
- 每次抓取等待时间：1-5 秒

**Webhook 通知**：

- 发送完成通知
- 网络请求

#### 2. 轻量级 CPU 操作（占 <10% 时间）

**文档处理**：

- PDF 解析（PyMuPDF）- 轻量级
- HTML 解析（BeautifulSoup）- 轻量级
- Markdown 处理 - 轻量级

**文件生成**：

- PDF 生成（md2pdf）- 中等 CPU
- DOCX 生成（python-docx）- 轻量级

**文本处理**：

- 文本提取和清理
- 向量化（embedding）- 但通常也是 API 调用

## 时间分布估算

假设一个报告生成需要 5 分钟：

```
网络 I/O 等待: 4.5 分钟 (90%)
  - LLM API 调用: 3 分钟
  - 搜索 API 调用: 1 分钟
  - 网页抓取: 0.5 分钟

CPU 处理: 0.5 分钟 (10%)
  - 文档解析: 0.2 分钟
  - 文件生成: 0.2 分钟
  - 其他处理: 0.1 分钟
```

## 并发策略建议

### ✅ 使用 asyncio pool（当前配置）

**优势**：

- 适合 I/O 密集型任务
- 可以设置较高的并发数（8-16+）
- 资源消耗低（主要是内存，CPU 使用率低）

**推荐并发数**：

- **轻负载**: 4-8 并发
- **中等负载**: 8-16 并发
- **高负载**: 16-32 并发（取决于系统资源）

### ❌ 不适合 prefork pool

**原因**：

- prefork 适合 CPU 密集型任务
- 每个进程消耗更多内存
- 对于 I/O 密集型任务，asyncio 更高效

## 性能优化建议

### 1. 增加并发数（主要优化）

由于大部分时间在等待网络响应，可以设置较高的并发数：

```yaml
# docker-compose.yml
CELERY_WORKER_CONCURRENCY: 16 # 可以设置较高
```

**理由**：

- 一个任务等待 API 响应时，其他任务可以继续执行
- CPU 使用率低，不会成为瓶颈
- 内存消耗主要是任务数据，不是 CPU 计算

### 2. 启动多个 Worker（水平扩展）

```bash
# 启动 2 个 worker，每个 16 并发 = 32 个并发任务
docker-compose up -d --scale gpt-researcher-worker=2
```

### 3. 监控资源使用

```bash
# 监控 CPU 和内存
docker stats gpt-researcher-worker

# 如果 CPU 使用率 < 50%，可以增加并发
# 如果内存使用率 < 70%，可以增加并发
```

### 4. API 限流考虑

**注意**：虽然可以设置高并发，但需要考虑：

1. **LLM API 限流**：

   - OpenAI/Azure 有速率限制（RPM、TPM）
   - 并发过高可能导致 429 错误
   - 建议：根据 API 限制调整并发

2. **搜索 API 限流**：

   - Tavily 有免费/付费限制
   - 内部 API 可能有速率限制

3. **网络带宽**：
   - 大量并发请求需要足够的网络带宽

## 实际测试建议

### 测试不同并发数

```bash
# 测试 4 并发
CELERY_WORKER_CONCURRENCY=4 docker-compose up -d gpt-researcher-worker

# 测试 8 并发
CELERY_WORKER_CONCURRENCY=8 docker-compose up -d gpt-researcher-worker

# 测试 16 并发
CELERY_WORKER_CONCURRENCY=16 docker-compose up -d gpt-researcher-worker
```

### 监控指标

1. **任务完成时间**：是否因为并发增加而减少
2. **API 错误率**：是否出现 429（限流）错误
3. **系统资源**：CPU、内存、网络使用率
4. **任务排队时间**：队列中等待的任务数

## 推荐配置

### 开发环境

```yaml
CELERY_WORKER_CONCURRENCY: 4
# 1 worker × 4 并发 = 4 个任务
```

### 生产环境（中等负载）

```yaml
CELERY_WORKER_CONCURRENCY: 8
# 2 workers × 8 并发 = 16 个任务
```

启动：

```bash
docker-compose up -d --scale gpt-researcher-worker=2
```

### 生产环境（高负载）

```yaml
CELERY_WORKER_CONCURRENCY: 16
# 3 workers × 16 并发 = 48 个任务
```

启动：

```bash
docker-compose up -d --scale gpt-researcher-worker=3
```

## 总结

✅ **任务特性**：I/O 密集型（网络等待占 90%+）

✅ **当前配置**：使用 `asyncio` pool 是正确的选择

✅ **优化方向**：

- 增加并发数（主要优化）
- 启动多个 worker（水平扩展）
- 监控 API 限流

✅ **预期效果**：

- CPU 使用率低（< 50%）
- 内存使用适中（主要存储任务数据）
- 可以支持较高的并发数（8-32+）

✅ **限制因素**：

- API 速率限制（主要限制）
- 网络带宽
- 系统内存（每个任务需要存储上下文）
