# 深度研究提纲与来源可靠性 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在一周内为 GPT Researcher 增加“深度模式先生成可编辑提纲、按模式路由模型、校验并补救失效来源”的完整闭环，并用固定中文题集量化证明有效引用率提升。

**Architecture:** 普通研究保持现有 WebSocket 主流程，直接使用 `qwen-plus`。深度研究先通过独立 HTTP 接口生成 3 至 5 节提纲，用户确认后再把提纲和白名单模型配置随 WebSocket 请求发送。后端按请求创建模型配置，不修改全局环境变量；研究完成前对来源进行归一化、去重和可访问性检查，来源不足时最多补检索一次。离线评测脚本复用同一校验器，对基线和增强版输出同口径指标。

**Tech Stack:** Python 3.12、FastAPI、WebSocket、GPT Researcher、DashScope、Next.js 14、React、TypeScript、Vitest、Testing Library、httpx、Docker Compose。

## Global Constraints

- 保留现有 `research_report`、`detailed_report`、`multi_agents` 行为；本周只增强 `research_report` 和 `deep`。
- `research_report` 不展示提纲确认窗口，三个 LLM 角色均使用 `dashscope:qwen-plus`。
- `deep` 必须先生成提纲；FAST 使用 `dashscope:qwen-plus`，SMART 和 STRATEGIC 使用 `dashscope:qwen3.7-max`。
- 模型名只能来自后端白名单，前端不能提交任意 provider 或模型名。
- 来源补救最多执行一次，禁止无限重试。
- `.env`、API Key、评测生成的完整报告和服务器 IP 不提交到 Git。
- 本周不做整站中文化、拖拽提纲、报告版本历史、多搜索引擎路由和事实真伪判定。
- 主指标为有效引用率；验收目标为提升至少 15 个百分点，报告成功率不下降，深度模式平均耗时增长不超过 30%。

---

## Day 1：建立请求级模型路由和可回退开关

**当天结果：** 后端能根据报告类型解析 `simple` 或 `deep` 配置；普通请求不会意外调用高成本模型；功能可通过 `reliability_enabled` 关闭以运行基线。

### Task 1：先写模型配置解析测试

**Files:**
- Create: `tests/test_model_profiles.py`
- Create: `gpt_researcher/config/model_profiles.py`
- Modify: `gpt_researcher/config/config.py`

- [ ] **Step 1: 写失败测试，固定两套允许的模型组合**

```python
import unittest

from gpt_researcher.config.model_profiles import resolve_model_profile


class ModelProfileTests(unittest.TestCase):
    def test_simple_profile_uses_qwen_plus_for_every_role(self):
        name, values = resolve_model_profile("research_report", "simple")
        self.assertEqual(name, "simple")
        self.assertEqual(values["FAST_LLM"], "dashscope:qwen-plus")
        self.assertEqual(values["SMART_LLM"], "dashscope:qwen-plus")
        self.assertEqual(values["STRATEGIC_LLM"], "dashscope:qwen-plus")

    def test_deep_profile_routes_smart_roles_to_qwen_max(self):
        name, values = resolve_model_profile("deep", "deep")
        self.assertEqual(name, "deep")
        self.assertEqual(values["FAST_LLM"], "dashscope:qwen-plus")
        self.assertEqual(values["SMART_LLM"], "dashscope:qwen3.7-max")
        self.assertEqual(values["STRATEGIC_LLM"], "dashscope:qwen3.7-max")

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_model_profile("deep", "custom-model")
```

- [ ] **Step 2: 运行测试并确认失败原因是模块尚不存在**

Run: `python -m unittest tests.test_model_profiles -v`

Expected: `ModuleNotFoundError: No module named 'gpt_researcher.config.model_profiles'`

- [ ] **Step 3: 实现白名单解析器**

```python
from copy import deepcopy
from typing import Literal

ModelProfileName = Literal["simple", "deep"]

MODEL_PROFILE_OVERRIDES = {
    "simple": {
        "FAST_LLM": "dashscope:qwen-plus",
        "SMART_LLM": "dashscope:qwen-plus",
        "STRATEGIC_LLM": "dashscope:qwen-plus",
    },
    "deep": {
        "FAST_LLM": "dashscope:qwen-plus",
        "SMART_LLM": "dashscope:qwen3.7-max",
        "STRATEGIC_LLM": "dashscope:qwen3.7-max",
    },
}


def resolve_model_profile(report_type: str, requested: str | None):
    expected = "deep" if report_type == "deep" else "simple"
    profile = requested or expected
    if profile != expected or profile not in MODEL_PROFILE_OVERRIDES:
        raise ValueError(f"Unsupported model profile: {profile}")
    return profile, deepcopy(MODEL_PROFILE_OVERRIDES[profile])
```

- [ ] **Step 4: 给 `Config` 增加请求级覆盖方法**

在 `Config` 中增加 `apply_runtime_overrides(overrides)`：只允许覆盖 `FAST_LLM`、`SMART_LLM`、`STRATEGIC_LLM`，将键转换成小写属性后重新调用 `_set_llm_attributes()`。不得写入 `os.environ`。

- [ ] **Step 5: 再次运行测试**

Run: `python -m unittest tests.test_model_profiles -v`

Expected: 3 tests pass。

- [ ] **Step 6: 提交 Day 1 第一部分**

```bash
git add tests/test_model_profiles.py gpt_researcher/config/model_profiles.py gpt_researcher/config/config.py
git commit -m "feat: add request scoped model profiles"
```

### Task 2：把新字段贯穿请求链路

**Files:**
- Modify: `backend/server/app.py`
- Modify: `backend/server/server_utils.py`
- Modify: `backend/server/websocket_manager.py`
- Modify: `backend/report_type/basic_report/basic_report.py`
- Modify: `gpt_researcher/agent.py`
- Modify: `tests/test_websocket_manager.py`

- [ ] **Step 1: 在 WebSocket 解析测试中增加断言**

测试输入包含：

```json
{
  "task": "测试问题",
  "report_type": "deep",
  "model_profile": "deep",
  "reliability_enabled": true,
  "outline": []
}
```

断言 `extract_command_data()` 返回 `model_profile == "deep"`、`reliability_enabled is True`、`outline == []`。

- [ ] **Step 2: 运行目标测试并确认失败**

Run: `python -m unittest tests.test_websocket_manager -v`

Expected: 新字段断言失败。

- [ ] **Step 3: 扩展请求模型和调用签名**

在 `ResearchRequest`、`extract_command_data()`、`WebSocketManager.start_streaming()`、`run_agent()`、`BasicReport.__init__()` 和 `GPTResearcher.__init__()` 中增加：

```python
outline: list[dict] | None = None
model_profile: str | None = None
reliability_enabled: bool = True
```

`GPTResearcher.__init__()` 调用 `resolve_model_profile()`，再对当前实例的 `Config` 执行请求级覆盖。将解析后的 profile 名保存为 `self.model_profile`。

- [ ] **Step 4: REST `/report/` 与 WebSocket 使用同一字段语义**

REST 接口构造 `GPTResearcher` 时同样传入三项新字段，避免网页和 API 行为不一致。

- [ ] **Step 5: 运行后端回归测试**

Run: `python -m unittest tests.test_websocket_manager tests.test_model_profiles -v`

Expected: 全部通过。

- [ ] **Step 6: 提交 Day 1 第二部分**

```bash
git add backend/server/app.py backend/server/server_utils.py backend/server/websocket_manager.py backend/report_type/basic_report/basic_report.py gpt_researcher/agent.py tests/test_websocket_manager.py
git commit -m "feat: pass research execution options through backend"
```

**Day 1 验收：** `research_report` 解析为 `simple`，`deep` 解析为 `deep`；未知模型配置返回明确错误；现有普通报告测试不受影响。

---

## Day 2：实现深度模式提纲生成接口

**当天结果：** 后端可根据中文问题生成结构化的 3 至 5 节提纲；无效 JSON、重复标题和过少章节都能稳定处理。

### Task 3：实现提纲领域模型和解析器

**Files:**
- Create: `gpt_researcher/skills/outline.py`
- Create: `tests/test_outline.py`
- Modify: `backend/server/app.py`

- [ ] **Step 1: 写提纲解析失败测试**

覆盖以下行为：

- 合法 JSON 返回 3 至 5 个 `OutlineSection`。
- Markdown 代码围栏被清理。
- 空标题被拒绝。
- 重复标题去重。
- 超过 5 节时截断到 5 节。
- 少于 3 节时抛出 `OutlineParseError`。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest tests.test_outline -v`

Expected: outline 模块不存在。

- [ ] **Step 3: 实现稳定的数据结构**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class OutlineSection:
    id: str
    title: str
    description: str


def parse_outline_response(raw: str) -> list[OutlineSection]:
    """Parse and validate a model response into three to five sections."""
```

章节 `id` 使用稳定格式 `section-1` 至 `section-5`。解析器只负责校验，不在失败时偷偷使用原问题作为提纲。

- [ ] **Step 4: 实现 `OutlinePlanner.generate()`**

使用当前请求的 `STRATEGIC_LLM` 调用 `create_chat_completion()`，提示词要求只返回：

```json
{
  "sections": [
    {"title": "章节标题", "description": "本节调查范围和要回答的问题"}
  ]
}
```

系统提示明确：输出语言使用 `language`，章节不能重叠，每节必须可通过公开资料研究。

- [ ] **Step 5: 增加 `POST /api/outline`**

请求与响应：

```python
class OutlineRequest(BaseModel):
    task: str
    language: str = "zh-CN"


class OutlineResponse(BaseModel):
    sections: list[dict]
    model_profile: str = "deep"
```

接口始终使用 `deep` 模型配置。解析失败返回 HTTP 502 和可显示的中文错误；空问题返回 HTTP 422。

- [ ] **Step 6: 用 mock LLM 测试接口，不消耗真实额度**

Run: `python -m unittest tests.test_outline -v`

Expected: 全部通过。

- [ ] **Step 7: 提交 Day 2**

```bash
git add gpt_researcher/skills/outline.py tests/test_outline.py backend/server/app.py
git commit -m "feat: add deep research outline endpoint"
```

**Day 2 验收：** 本地接口测试返回 3 至 5 节中文结构化提纲；模型返回坏格式时用户能看到错误，而不是无限加载。

---

## Day 3：实现可编辑提纲确认界面

**当天结果：** 普通模式保持直接执行；深度模式先显示提纲，用户可以修改标题和说明，确认后才开始研究。

### Task 4：建立前端测试环境和纯类型接口

**Files:**
- Modify: `frontend/nextjs/package.json`
- Create: `frontend/nextjs/vitest.config.ts`
- Create: `frontend/nextjs/tests/setup.ts`
- Create: `frontend/nextjs/types/outline.ts`
- Create: `frontend/nextjs/actions/outlineActions.ts`
- Create: `frontend/nextjs/tests/outlineActions.test.ts`

- [ ] **Step 1: 固定 Node 18 可用的测试依赖**

在 `devDependencies` 增加 `vitest@1.6.1`、`@testing-library/react@14.3.1`、`@testing-library/jest-dom@6.4.6`、`jsdom@24.1.0`，并增加：

```json
"test": "vitest run"
```

- [ ] **Step 2: 定义前后端共享形状**

```typescript
export type OutlineSection = {
  id: string;
  title: string;
  description: string;
};

export type ModelProfile = "simple" | "deep";
```

- [ ] **Step 3: 先写 action 测试**

Mock `fetch`，断言 `generateOutline("问题", "zh-CN")` 请求 `/api/outline`、使用 POST、返回结构化章节；非 2xx 时抛出接口返回的信息。

- [ ] **Step 4: 实现 `generateOutline()` 并运行测试**

Run: `cd frontend/nextjs && npm test -- outlineActions.test.ts`

Expected: 测试通过。

### Task 5：提纲确认窗口和页面状态机

**Files:**
- Create: `frontend/nextjs/components/Settings/OutlineReview.tsx`
- Create: `frontend/nextjs/tests/OutlineReview.test.tsx`
- Modify: `frontend/nextjs/app/page.tsx`
- Modify: `frontend/nextjs/hooks/useWebSocket.ts`

- [ ] **Step 1: 写组件交互测试**

断言：

- 显示 3 个章节输入框。
- 修改标题后 `onChange` 收到新值。
- 任一标题为空时确认按钮禁用。
- 点击确认传回当前提纲。
- 点击取消关闭窗口且不启动研究。

- [ ] **Step 2: 实现 `OutlineReview`**

采用普通模态窗口，不实现拖拽。每节包含“标题”和“研究重点”两个输入；按钮只保留“取消”和“确认并开始研究”。所有文字使用中文。

- [ ] **Step 3: 将页面研究启动拆成两个阶段**

把当前 `handleDisplayResult()` 的直接启动逻辑抽成：

```typescript
const startResearch = async (
  question: string,
  outline?: OutlineSection[],
  modelProfile: ModelProfile = "simple",
) => { /* existing loading and WebSocket start */ };
```

新的分支：

```typescript
if (chatBoxSettings.report_type === "deep") {
  const sections = await generateOutline(newQuestion, chatBoxSettings.language);
  setPendingDeepResearch({ question: newQuestion, sections });
  return;
}
await startResearch(newQuestion, undefined, "simple");
```

- [ ] **Step 4: 扩展 WebSocket 启动载荷**

`initializeWebSocket()` 增加可选参数，并发送：

```typescript
{
  outline,
  model_profile: modelProfile,
  reliability_enabled: true,
}
```

- [ ] **Step 5: 运行前端测试和生产构建**

Run: `cd frontend/nextjs && npm test`

Expected: 所有 Vitest 测试通过。

Run: `cd frontend/nextjs && npm run build`

Expected: Next.js build 成功，无缺失模块。

- [ ] **Step 6: 提交 Day 3**

```bash
git add frontend/nextjs
git commit -m "feat: add editable deep research outline review"
```

**Day 3 验收：** 普通模式一次点击即开始；深度模式不会先进入空白 Agent Work，而是先出现可编辑提纲；取消后不产生模型研究调用。

---

## Day 4：让确认提纲真正控制深度研究

**当天结果：** 提纲不是装饰性 UI；每个章节都会进入研究规划和最终写作提示，嵌套研究实例继续使用 `deep` 模型配置。

### Task 6：提纲驱动深度研究和报告结构

**Files:**
- Modify: `gpt_researcher/agent.py`
- Modify: `gpt_researcher/skills/deep_research.py`
- Modify: `gpt_researcher/skills/writer.py`
- Create: `tests/test_deep_outline.py`

- [ ] **Step 1: 写行为测试**

Mock `generate_research_plan()`、`deep_research()` 和写作 LLM，断言：

- 有确认提纲时不再重新生成另一份提纲。
- 格式化后的每个标题和说明都进入 deep research 输入。
- 嵌套 `GPTResearcher` 收到 `model_profile="deep"`。
- 无提纲时保留现有 deep research 回退路径。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.test_deep_outline -v`

Expected: 当前 `DeepResearchSkill` 忽略 outline，断言失败。

- [ ] **Step 3: 增加统一提纲格式化函数**

```python
def format_outline_for_prompt(sections: list[OutlineSection]) -> str:
    return "\n".join(
        f"{index}. {section.title}: {section.description}"
        for index, section in enumerate(sections, start=1)
    )
```

- [ ] **Step 4: 调整 `DeepResearchSkill.run()`**

有提纲时，将确认内容作为研究目标，不调用原来的自动规划步骤；无提纲时仍调用 `generate_research_plan()`，保证 API 老用户兼容。

- [ ] **Step 5: 将提纲加入最终写作提示**

在 `writer.py` 生成 deep 报告时添加明确约束：一级章节顺序必须与确认提纲一致；允许增加“摘要”“结论”“参考资料”，不得替换用户确认的核心章节。

- [ ] **Step 6: 传播模型配置**

`deep_research.py` 创建嵌套 `GPTResearcher` 时传入：

```python
model_profile=self.researcher.model_profile,
reliability_enabled=self.researcher.reliability_enabled,
```

- [ ] **Step 7: 运行目标测试和相关回归**

Run: `python -m unittest tests.test_deep_outline tests.test_model_profiles -v`

Expected: 全部通过。

- [ ] **Step 8: 提交 Day 4**

```bash
git add gpt_researcher/agent.py gpt_researcher/skills/deep_research.py gpt_researcher/skills/writer.py tests/test_deep_outline.py
git commit -m "feat: drive deep research from confirmed outline"
```

**Day 4 验收：** 日志能显示 simple/deep profile；深度报告的核心章节标题与用户确认提纲一致；普通报告仍使用原流程。

---

## Day 5：来源校验、去重和单次补救

**当天结果：** 无效链接不再直接进入最终参考资料；来源不足会自动补检索一次，随后无论成功或失败都明确结束。

### Task 7：实现可独立测试的来源校验器

**Files:**
- Create: `gpt_researcher/skills/source_validator.py`
- Create: `tests/test_source_validator.py`

- [ ] **Step 1: 写 URL 归一化测试**

覆盖：移除 `utm_source`、`utm_medium`、`utm_campaign`、`fbclid` 和 fragment；保留影响页面内容的普通查询参数；去除默认端口；相同规范 URL 去重。

- [ ] **Step 2: 写 HTTP 状态测试**

使用 `httpx.MockTransport`，不访问公网。覆盖：

- 200 且正文至少 200 字节为 valid。
- 301 跳转到 200 为 valid，并保存最终 URL。
- 401、403、429 为 blocked。
- 404、410 为 invalid。
- 超时为 invalid，reason 为 timeout。
- 200 但正文过短为 invalid。
- 并发数不超过 5，每个请求 8 秒超时。

- [ ] **Step 3: 实现结果结构**

```python
@dataclass(frozen=True)
class SourceValidationResult:
    original_url: str
    normalized_url: str
    final_url: str | None
    status: Literal["valid", "invalid", "blocked"]
    http_status: int | None
    content_length: int
    reason: str
```

- [ ] **Step 4: 实现批量校验**

`SourceValidator.validate_many()` 使用 `asyncio.Semaphore(5)` 和 `httpx.AsyncClient(follow_redirects=True)`；GET 只读取判断有效性所需的前 4096 字节，避免把大文件全部下载到内存。

- [ ] **Step 5: 运行测试**

Run: `python -m unittest tests.test_source_validator -v`

Expected: 全部通过且不需要联网。

### Task 8：把校验器接入普通和深度研究

**Files:**
- Create: `gpt_researcher/skills/source_recovery.py`
- Modify: `gpt_researcher/agent.py`
- Modify: `gpt_researcher/skills/deep_research.py`
- Modify: `gpt_researcher/skills/writer.py`
- Create: `tests/test_source_recovery.py`

- [ ] **Step 1: 写补救策略测试**

```python
policy = SourceRecoveryPolicy(min_valid_sources=3, max_retries=1)
```

断言：0 至 2 个有效来源且 retry_count 为 0 时重试；3 个及以上不重试；retry_count 为 1 时永不再次重试。

- [ ] **Step 2: 实现普通报告校验流程**

研究完成后校验 `visited_urls`，只保留 valid URL。若有效来源少于 3 个且功能开启，基于原问题和失败原因生成一条更精确的查询，再调用一次现有检索流程。合并结果后重新校验，不再进行第三轮。

- [ ] **Step 3: 实现深度报告定向单次补救**

在 `DeepResearchSkill.process_query()` 中记录每个研究目标的来源。所有初始研究目标完成后，统计各章节有效来源数量，只选择有效来源最少的一个章节，用“章节标题 + 研究重点 + 权威来源”生成一条补救查询。整份报告共享 `retry_count`，达到 1 后不得为其他章节继续补检索。

- [ ] **Step 4: 在最终引用生成前过滤来源**

`writer.py` 只接收 valid URL 列表，并将 `source_validation_results` 和 `retry_count` 保存在研究实例上，供评测脚本读取。

- [ ] **Step 5: 增加结构化日志**

每次研究输出以下字段，但不得输出 API Key：

```text
source_validation total=8 valid=5 invalid=2 blocked=1
source_recovery attempted=1 recovered=2
```

- [ ] **Step 6: 运行来源相关测试**

Run: `python -m unittest tests.test_source_validator tests.test_source_recovery tests.test_deep_outline -v`

Expected: 全部通过。

- [ ] **Step 7: 提交 Day 5**

```bash
git add gpt_researcher/skills/source_validator.py gpt_researcher/skills/source_recovery.py gpt_researcher/agent.py gpt_researcher/skills/deep_research.py gpt_researcher/skills/writer.py tests/test_source_validator.py tests/test_source_recovery.py
git commit -m "feat: validate and recover research sources"
```

**Day 5 验收：** Mock 场景中失效来源被剔除；补救次数严格受限；真实运行日志能看到校验统计；报告不会因一个来源失败而无限等待。

---

## Day 6：固定题集评测和端到端联调

**当天结果：** 一条命令可运行基线或增强版评测，生成原始结果、汇总指标和可直接用于 README 的对比表。

### Task 9：建立可复现评测工具

**Files:**
- Create: `evals/chinese_reliability/queries.json`
- Create: `evals/chinese_reliability/metrics.py`
- Create: `evals/chinese_reliability/run_benchmark.py`
- Create: `evals/chinese_reliability/README.md`
- Create: `tests/test_reliability_metrics.py`

- [ ] **Step 1: 固定 10 个中文研究问题**

题集包含 5 个普通报告和 5 个深度报告，覆盖 AI 岗位、教育、消费、历史、产业和社会议题。每项固定 `id`、`question`、`report_type`，运行基线和增强版时不得改题。

- [ ] **Step 2: 先写指标测试**

指标定义固定为：

```text
有效引用率 = 可访问且正文有效的唯一引用数 / 唯一引用总数
报告成功 = 正文不少于 800 个字符且有效引用不少于 3 个
平均耗时 = 所有完成任务 duration_seconds 的平均值
平均重试次数 = retry_count 的平均值
平均成本 = total_cost 的平均值；无法取得时写 null，不估算
```

测试必须覆盖无引用时有效引用率为 0、重复链接只计一次、失败报告不计为成功。

- [ ] **Step 3: 实现报告链接提取和指标计算**

复用 Day 5 的 `normalize_url()` 和 `SourceValidator`，禁止评测脚本再写一套不同规则。

- [ ] **Step 4: 实现 benchmark CLI**

```bash
python evals/chinese_reliability/run_benchmark.py \
  --mode baseline \
  --output-dir evals/chinese_reliability/results/baseline

python evals/chinese_reliability/run_benchmark.py \
  --mode enhanced \
  --output-dir evals/chinese_reliability/results/enhanced
```

`baseline` 设置 `reliability_enabled=False`，深度模式不传用户确认提纲；`enhanced` 开启提纲和来源补救。两者使用同一模型 profile，防止把模型升级误算成功能收益。

- [ ] **Step 5: 保存可追溯输出**

每次运行生成：

- `runs.jsonl`：每题的模式、耗时、引用数、有效引用数、重试数、成功状态和错误。
- `summary.json`：聚合指标。
- `comparison.md`：基线与增强版表格及差值。

完整报告正文写入本地结果目录并加入 `.gitignore`；仓库只提交题集、脚本和去除敏感信息后的汇总文件。

- [ ] **Step 6: 运行单元测试和单题冒烟测试**

Run: `python -m unittest tests.test_reliability_metrics -v`

Expected: 全部通过。

Run: `python evals/chinese_reliability/run_benchmark.py --mode enhanced --limit 1 --output-dir /tmp/gptr-benchmark-smoke`

Expected: 生成一条 `runs.jsonl` 和 `summary.json`，错误时正常结束并记录 error 字段。

### Task 10：完整联调

**Files:**
- Modify: `.gitignore`
- Modify: `docker-compose.yml` only if a new non-secret environment variable must enter the container

- [ ] **Step 1: 运行全部 Python 测试**

Run: `python -m unittest discover -s tests -v`

Expected: 全部通过；已有环境依赖测试若跳过，记录具体名称和原因。

- [ ] **Step 2: 运行前端测试和构建**

Run: `cd frontend/nextjs && npm test && npm run build`

Expected: 全部通过。

- [ ] **Step 3: Docker 本地构建检查**

Run: `docker compose build gpt-researcher gptr-nextjs`

Expected: 两个镜像构建完成。

- [ ] **Step 4: 在服务器运行 10 题基线和增强版**

为避免 API 并发限制，题目串行执行；记录服务器配置、运行日期、模型名、搜索源和失败原因。不得删除失败样本后重新计算平均值。

- [ ] **Step 5: 检查量化门槛**

增强版必须满足：

- 有效引用率相对基线提高至少 15 个百分点。
- 报告成功率不低于基线。
- 深度模式平均耗时增长不超过 30%。

若首轮未达标，只允许调整来源有效阈值、补救查询提示和提纲提示；不得替换题集或只保留成功题。

- [ ] **Step 6: 提交 Day 6**

```bash
git add evals/chinese_reliability tests/test_reliability_metrics.py .gitignore docker-compose.yml
git commit -m "test: add Chinese research reliability benchmark"
```

**Day 6 验收：** `comparison.md` 有真实的基线、增强版和差值；任何未达到目标的指标都有原始记录支持，不写虚构数字。

---

## Day 7：部署、作品集材料和演示闭环

**当天结果：** 功能在腾讯云可访问，README 能解释 Agent 工作流和量化收益，具备 3 至 5 分钟面试演示路径。

### Task 11：部署前清理和文档

**Files:**
- Modify: `README-zh_CN.md`
- Create: `docs/portfolio/deep-research-improvement.md`
- Create: `docs/portfolio/demo-script.md`

- [ ] **Step 1: 在 README 增加项目改进摘要**

内容包括：问题背景、普通与深度模式流程、模型路由、来源校验、一次补救策略、运行方式和量化结果表。明确这是基于 GPT Researcher 的二次开发，不把上游能力描述成自己从零实现。

- [ ] **Step 2: 写技术说明**

`deep-research-improvement.md` 解释以下知识点：

- Agent 的规划、检索、写作和工具调用链。
- 为什么请求级配置不能修改全局环境变量。
- 为什么 URL 可访问性不等于事实正确性。
- 为什么限制一次补救。
- 基线和增强版如何公平对比。

- [ ] **Step 3: 写面试演示脚本**

演示顺序固定：普通问题直接执行；切换 Deep Research；生成并编辑提纲；确认；展示 Agent 日志；打开报告引用；最后展示 `comparison.md`。

### Task 12：服务器发布和现场验证

**Files:**
- No new source files expected

- [ ] **Step 1: 合并功能分支后在服务器备份运行配置**

```bash
cd ~/apps/gpt-researcher
cp .env ~/gpt-researcher-env-backup-$(date +%Y%m%d).env
git status --short
```

不得把 `.env` 加入 Git。

- [ ] **Step 2: 拉取用户 fork 的 main**

服务器 remote 应指向 `https://github.com/wulongchacc/gpt-researcher.git`。若服务器仍有镜像源等本地改动，先 `git stash push -u -m "server deployment overrides"`，拉取后只恢复确实需要的 Docker 镜像源配置。

```bash
git switch main
git pull --ff-only origin main
```

- [ ] **Step 3: 重建并更新匿名 volume**

```bash
sudo docker compose up -d --build --force-recreate --renew-anon-volumes
sudo docker compose ps
```

`--renew-anon-volumes` 用于避免旧的前端 `node_modules` volume 遮盖新依赖。

- [ ] **Step 4: 检查日志和健康状态**

```bash
sudo docker compose logs --tail=200 gpt-researcher
sudo docker compose logs --tail=100 gptr-nextjs
curl -I http://127.0.0.1:3000
curl -I http://127.0.0.1:8000
```

Expected: 容器为 Up；前端和后端返回 HTTP 响应；日志无缺失模块和无限重试。

- [ ] **Step 5: 浏览器执行三项验收**

1. Summary 问题直接开始，日志显示 `model_profile=simple`。
2. Deep 问题先出现中文提纲，修改后报告章节保持一致，日志显示 `model_profile=deep`。
3. 人为提供一个会失效的来源测试场景，最终引用中不保留失效 URL，日志中重试次数不超过 1。

- [ ] **Step 6: 提交文档**

```bash
git add README-zh_CN.md docs/portfolio
git commit -m "docs: document deep research reliability improvements"
```

**Day 7 验收：** 云端演示通过；README 有真实量化结果；仓库无密钥；可在 5 分钟内讲清“问题、设计、Agent 流程、工程取舍、指标结果”。

---

## 每日晚间检查

每天结束前执行：

```bash
git status --short
git log --oneline -5
```

并记录四项：当天完成内容、通过的测试、仍存在的错误、第二天第一条命令。任何 API Key、服务器公网 IP、完整 `.env` 不得出现在日志截图、README 或提交记录中。

## 一周内的降级顺序

如果进度落后，按以下顺序缩减，不能牺牲量化评测：

1. 取消提纲章节说明编辑，只保留标题编辑。
2. 来源补救查询不再调用 LLM 改写，直接使用“问题或最薄弱章节 + 权威来源”模板。
3. 前端只保留桌面端提纲确认，移动端沿用现有行为并在 README 说明。
4. 保留 10 题评测、请求级模型路由、普通/深度分流和有效引用率指标。

## 最终完成定义

- 普通模式不显示提纲并使用 `qwen-plus`。
- 深度模式显示可编辑提纲，确认提纲能控制报告章节。
- 深度模式 SMART 和 STRATEGIC 使用 `qwen3.7-max`，嵌套研究不丢失配置。
- 最终引用只包含通过校验的规范 URL，补救次数有硬上限。
- 固定 10 题基线与增强版结果可复现。
- 有效引用率提升至少 15 个百分点，成功率不下降，耗时增长不超过 30%。
- Python 测试、前端测试、Next.js 构建和 Docker 构建全部通过。
- README、技术说明、演示脚本和真实评测表齐全，仓库不包含任何密钥。
