# 报告语言切换功能实施计划

> **供执行 Agent 使用：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项实施；使用本文的复选框记录进度。

**目标：** 在 Preference 中提供“中文（简体）/ English”选择，使每个新研究任务按所选语言生成报告，并保持旧调用兼容。

**架构：** 前端把语言作为 `ChatBoxSettings` 的强类型字段保存到现有 localStorage，并在 WebSocket 启动消息中发送。后端在请求边界统一规范化语言，然后沿 `WebSocket/REST -> run_agent -> Report runner -> GPTResearcher` 传递；`GPTResearcher` 只覆盖当前实例的 `cfg.language`，不修改环境变量，因此并发任务互不影响。详细报告和深度研究创建子研究员时显式继承父研究员语言。

**技术栈：** Next.js 14、React 18、TypeScript、FastAPI、Pydantic v2、Python 3.12、pytest、Docker Compose。

## 全局约束

- 唯一允许的请求值为 `Chinese (Simplified)` 和 `English`。
- 默认值为 `Chinese (Simplified)`。
- 缺失、空白或不支持的值必须回退到 `.env`/`Config` 的 `LANGUAGE`，不得导致任务失败。
- 任务级语言优先于环境级 `LANGUAGE`，但不得修改 `os.environ`。
- 语言变更只影响之后新建的任务。
- 标准报告、深度研究和详细报告必须支持任务级语言。
- 独立的 `multi_agents` 流程继续使用环境级 `LANGUAGE`，不在本次修改范围内。
- 不翻译整个页面，不增加 PDF 中文字体，不修改搜索地区或搜索语言。

---

### 任务 1：核心语言规范化与研究员实例覆盖

**文件：**
- 新建：`gpt_researcher/utils/language.py`
- 修改：`gpt_researcher/agent.py:52-145`
- 新建测试：`tests/test_report_language.py`

**接口：**
- 产出：`SUPPORTED_REPORT_LANGUAGES: frozenset[str]`
- 产出：`normalize_report_language(language: object) -> str | None`
- 产出：`GPTResearcher.__init__(..., language: str | None = None, ...)`
- 规则：合法任务值覆盖当前 `self.cfg.language`；非法或空值不覆盖配置。

- [ ] **步骤 1：编写语言规范化和实例覆盖的失败测试**

```python
import pytest

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.language import normalize_report_language


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Chinese (Simplified)", "Chinese (Simplified)"),
        (" English ", "English"),
        (None, None),
        ("", None),
        ("French", None),
        (123, None),
    ],
)
def test_normalize_report_language(raw, expected):
    assert normalize_report_language(raw) == expected


def test_task_language_overrides_researcher_config():
    researcher = GPTResearcher(
        query="测试报告语言",
        language="Chinese (Simplified)",
        verbose=False,
    )
    assert researcher.cfg.language == "Chinese (Simplified)"


def test_invalid_task_language_keeps_config_language(monkeypatch):
    monkeypatch.setenv("LANGUAGE", "English")
    researcher = GPTResearcher(query="fallback", language="French", verbose=False)
    assert researcher.cfg.language == "English"
```

- [ ] **步骤 2：运行测试并确认失败原因正确**

运行：

```bash
pytest tests/test_report_language.py -v
```

预期：测试收集阶段因 `gpt_researcher.utils.language` 不存在而失败。

- [ ] **步骤 3：实现集中式语言规范化函数**

在 `gpt_researcher/utils/language.py` 中加入：

```python
SUPPORTED_REPORT_LANGUAGES = frozenset({"Chinese (Simplified)", "English"})


def normalize_report_language(language: object) -> str | None:
    if not isinstance(language, str):
        return None
    normalized = language.strip()
    return normalized if normalized in SUPPORTED_REPORT_LANGUAGES else None
```

- [ ] **步骤 4：让 `GPTResearcher` 支持实例级语言覆盖**

在 `gpt_researcher/agent.py` 中：

```python
from gpt_researcher.utils.language import normalize_report_language
```

在构造函数的 `prompt_family` 后加入显式参数：

```python
language: str | None = None,
```

在 `self.cfg = Config(config_path)` 后、初始化各技能前加入：

```python
task_language = normalize_report_language(language)
if task_language:
    self.cfg.language = task_language
```

同时在构造函数 docstring 中说明 `language` 是可选的任务级报告语言。

- [ ] **步骤 5：运行核心测试**

运行：

```bash
pytest tests/test_report_language.py -v
```

预期：全部通过，且测试期间不发起模型或搜索网络请求。

- [ ] **步骤 6：提交本任务**

```bash
git add gpt_researcher/utils/language.py gpt_researcher/agent.py tests/test_report_language.py
git commit -m "feat: support per-task report language"
```

---

### 任务 2：WebSocket 与 REST 请求传递语言

**文件：**
- 修改：`backend/server/server_utils.py:126-173,398-412`
- 修改：`backend/server/websocket_manager.py:101-177`
- 修改：`backend/server/app.py:18,53-61,287-301`
- 修改测试：`tests/test_websocket_manager.py:87-110`
- 新建测试：`tests/test_report_language_requests.py`

**接口：**
- 消费：`normalize_report_language(language: object) -> str | None`
- 产出：`extract_command_data()` 返回元组最后一项 `language: str | None`
- 产出：`WebSocketManager.start_streaming(..., language: str | None = None)`
- 产出：`run_agent(..., language: str | None = None)`
- 产出：`ResearchRequest.language: str | None`

- [ ] **步骤 1：为请求边界编写失败测试**

在 `tests/test_report_language_requests.py` 中加入：

```python
from backend.server.app import ResearchRequest
from backend.server.server_utils import extract_command_data


def request_payload(language=None):
    payload = {
        "task": "测试",
        "report_type": "research_report",
        "report_source": "web",
        "tone": "Objective",
        "repo_name": "",
        "branch_name": "",
    }
    if language is not None:
        payload["language"] = language
    return payload


def test_websocket_language_is_normalized():
    values = extract_command_data({"language": " Chinese (Simplified) "})
    assert values[-1] == "Chinese (Simplified)"


def test_websocket_invalid_language_falls_back():
    values = extract_command_data({"language": "French"})
    assert values[-1] is None


def test_rest_request_normalizes_language():
    request = ResearchRequest(**request_payload(" English "))
    assert request.language == "English"


def test_rest_request_invalid_language_falls_back():
    request = ResearchRequest(**request_payload("French"))
    assert request.language is None
```

在 `tests/test_websocket_manager.py` 的现有测试中给 `start_streaming` 增加：

```python
language="Chinese (Simplified)",
```

并断言：

```python
self.assertEqual(call_kwargs["language"], "Chinese (Simplified)")
```

- [ ] **步骤 2：运行请求流测试并确认失败**

```bash
pytest tests/test_report_language_requests.py tests/test_websocket_manager.py -v
```

预期：`ResearchRequest` 尚无 `language`，或调用链没有把 `language` 传给 `run_agent`，测试失败。

- [ ] **步骤 3：扩展 WebSocket 参数解析和传递**

在 `backend/server/server_utils.py` 导入规范化函数，并在 `extract_command_data()` 元组末尾加入：

```python
normalize_report_language(json_data.get("language")),
```

`handle_start_command()` 解包 `language`，并使用关键字参数传给 manager，避免继续扩大位置参数风险：

```python
report = await manager.start_streaming(
    task=task,
    report_type=report_type,
    report_source=report_source,
    source_urls=source_urls,
    document_urls=document_urls,
    tone=tone,
    websocket=websocket,
    headers=headers,
    query_domains=query_domains,
    mcp_enabled=mcp_enabled,
    mcp_strategy=mcp_strategy,
    mcp_configs=mcp_configs,
    max_search_results=max_search_results,
    language=language,
)
```

给 `start_streaming()` 和 `run_agent()` 增加末尾可选参数 `language=None`，并从前者传给后者。

- [ ] **步骤 4：扩展 REST 请求模型**

在 `backend/server/app.py` 中导入 `field_validator` 和规范化函数：

```python
from pydantic import BaseModel, ConfigDict, field_validator
from gpt_researcher.utils.language import normalize_report_language
```

在 `ResearchRequest` 中加入：

```python
language: str | None = None

@field_validator("language", mode="before")
@classmethod
def normalize_language(cls, value):
    return normalize_report_language(value)
```

`write_report()` 调用 `run_agent()` 时加入：

```python
language=research_request.language,
```

- [ ] **步骤 5：运行请求流测试**

```bash
pytest tests/test_report_language_requests.py tests/test_websocket_manager.py -v
```

预期：全部通过；缺失和非法语言均返回 `None`，合法值被规范化并传给 `run_agent`。

- [ ] **步骤 6：提交本任务**

```bash
git add backend/server/server_utils.py backend/server/websocket_manager.py backend/server/app.py tests/test_websocket_manager.py tests/test_report_language_requests.py
git commit -m "feat: pass report language through API requests"
```

---

### 任务 3：报告执行器与子研究员继承语言

**文件：**
- 修改：`backend/server/websocket_manager.py:133-177`
- 修改：`backend/report_type/basic_report/basic_report.py:10-64`
- 修改：`backend/report_type/detailed_report/detailed_report.py:11-71,138-158`
- 修改：`gpt_researcher/skills/deep_research.py:415-435`
- 新建测试：`tests/test_report_language_propagation.py`

**接口：**
- 消费：`run_agent(..., language: str | None = None)`
- 产出：`BasicReport(..., language: str | None = None)`
- 产出：`DetailedReport(..., language: str | None = None)`
- 规则：所有非 multi-agent 的 `GPTResearcher` 实例均获得任务语言；内部子研究员继承父实例最终生效的 `cfg.language`。

- [ ] **步骤 1：编写 BasicReport 和 DetailedReport 的失败测试**

在 `tests/test_report_language_propagation.py` 中用 `unittest.mock.patch` 替换构造器内的 `GPTResearcher`，分别构造 `BasicReport` 和 `DetailedReport`：

```python
from unittest.mock import patch

from backend.report_type.basic_report.basic_report import BasicReport
from backend.report_type.detailed_report.detailed_report import DetailedReport


COMMON = {
    "query": "测试",
    "query_domains": [],
    "report_type": "research_report",
    "report_source": "web",
    "source_urls": [],
    "document_urls": [],
    "tone": "Objective",
    "config_path": "default",
    "websocket": None,
}


def test_basic_report_passes_language_to_researcher():
    with patch("backend.report_type.basic_report.basic_report.GPTResearcher") as researcher:
        BasicReport(**COMMON, language="Chinese (Simplified)")
    assert researcher.call_args.kwargs["language"] == "Chinese (Simplified)"


def test_detailed_report_passes_language_to_main_researcher():
    with patch("backend.report_type.detailed_report.detailed_report.GPTResearcher") as researcher:
        DetailedReport(**COMMON, language="Chinese (Simplified)")
    assert researcher.call_args.kwargs["language"] == "Chinese (Simplified)"
```

再增加以下异步测试所需的导入：

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt_researcher.skills.deep_research import DeepResearchSkill
```

详细报告测试使用两个 mock，分别代表主研究员和子研究员：

```python
@pytest.mark.asyncio
async def test_detailed_report_subtopic_inherits_effective_language():
    main = MagicMock()
    main.cfg.language = "Chinese (Simplified)"
    main.agent = "agent"
    main.role = "role"
    main.mcp_configs = None
    main.mcp_strategy = None
    main.extract_headers.return_value = []
    main.extract_sections.return_value = []

    child = MagicMock()
    child.context = []
    child.visited_urls = set()
    child.conduct_research = AsyncMock()
    child.get_draft_section_titles = AsyncMock(return_value="")
    child.get_similar_written_contents_by_draft_section_titles = AsyncMock(return_value=[])
    child.write_report = AsyncMock(return_value="section")

    with patch(
        "backend.report_type.detailed_report.detailed_report.GPTResearcher",
        side_effect=[main, child],
    ) as researcher:
        report = DetailedReport(**COMMON, language="Chinese (Simplified)")
        await report._get_subtopic_report({"task": "子主题"})

    assert researcher.call_args_list[1].kwargs["language"] == "Chinese (Simplified)"
```

深度研究测试将查询生成、结果处理和嵌套研究员全部替换为本地 mock，因此不会联网：

```python
@pytest.mark.asyncio
async def test_deep_research_child_inherits_effective_language():
    parent = SimpleNamespace(
        cfg=SimpleNamespace(
            language="Chinese (Simplified)",
            deep_research_breadth=1,
            deep_research_depth=1,
            deep_research_concurrency=1,
            config_path="default",
        ),
        websocket=None,
        tone="Objective",
        headers={},
        visited_urls=set(),
        mcp_configs=None,
        mcp_strategy=None,
    )
    skill = DeepResearchSkill(parent)
    skill.generate_search_queries = AsyncMock(
        return_value=[{"query": "子查询", "researchGoal": "验证语言"}]
    )
    skill.process_research_results = AsyncMock(
        return_value={"learnings": [], "followUpQuestions": [], "citations": {}}
    )

    child = MagicMock()
    child.conduct_research = AsyncMock(return_value=[])
    child.visited_urls = set()
    child.research_sources = []

    with patch("gpt_researcher.GPTResearcher", return_value=child) as researcher:
        await skill.deep_research("根问题", breadth=1, depth=1)

    assert researcher.call_args.kwargs["language"] == "Chinese (Simplified)"
```

- [ ] **步骤 2：运行传播测试并确认失败**

```bash
pytest tests/test_report_language_propagation.py -v
```

预期：报告执行器当前不接受 `language`，测试以 `unexpected keyword argument` 或缺少调用参数失败。

- [ ] **步骤 3：把语言传入标准和详细报告执行器**

在 `run_agent()` 中，仅在 `DetailedReport` 和 `BasicReport` 分支加入：

```python
language=language,
```

不要把语言传入 `run_multi_agent_task()`。

给 `BasicReport.__init__()` 增加末尾参数 `language=None`，并在 `gpt_researcher_params` 中加入：

```python
"language": language,
```

给 `DetailedReport.__init__()` 做相同修改。

- [ ] **步骤 4：让详细报告和深度研究的子研究员继承语言**

在 `DetailedReport._get_subtopic_report()` 创建子研究员时加入：

```python
language=self.gpt_researcher.cfg.language,
```

在 `DeepResearchSkill` 创建嵌套 `GPTResearcher` 时加入：

```python
language=self.researcher.cfg.language,
```

使用父实例最终生效的语言，而不是原始请求值，这样环境回退也能正确继承。

- [ ] **步骤 5：运行传播与核心测试**

```bash
pytest tests/test_report_language.py tests/test_report_language_requests.py tests/test_report_language_propagation.py tests/test_websocket_manager.py -v
```

预期：全部通过；标准、详细、深度研究链路均保持同一语言，multi-agent 代码未发生改变。

- [ ] **步骤 6：提交本任务**

```bash
git add backend/server/websocket_manager.py backend/report_type/basic_report/basic_report.py backend/report_type/detailed_report/detailed_report.py gpt_researcher/skills/deep_research.py tests/test_report_language_propagation.py
git commit -m "feat: propagate report language to nested research"
```

---

### 任务 4：Preference 语言控件、默认值和前端请求

**文件：**
- 修改：`frontend/nextjs/types/data.ts:41-51`
- 新建：`frontend/nextjs/components/Settings/LanguageSelector.tsx`
- 修改：`frontend/nextjs/components/Task/ResearchForm.tsx:1-176`
- 修改：`frontend/nextjs/components/layouts/MobileLayout.tsx:225-285`
- 修改：`frontend/nextjs/hooks/useWebSocket.ts:73-89`
- 修改：`frontend/nextjs/app/page.tsx:36-65`
- 修改：`frontend/nextjs/app/research/[id]/page.tsx:36-65`
- 修改：`frontend/nextjs/src/GPTResearcher.tsx:40-50`

**接口：**
- 产出：`ReportLanguage = "Chinese (Simplified)" | "English"`
- 产出：`ChatBoxSettings.language: ReportLanguage`
- 产出：`LanguageSelector` 接收 `language` 和 `onLanguageChange`
- 产出：WebSocket 启动载荷包含 `language`

- [ ] **步骤 1：先建立强类型契约并验证现有默认对象会失败**

在 `frontend/nextjs/types/data.ts` 中加入：

```typescript
export type ReportLanguage = "Chinese (Simplified)" | "English";
```

并给 `ChatBoxSettings` 增加：

```typescript
language: ReportLanguage;
```

运行：

```bash
cd frontend/nextjs
npx tsc --noEmit
```

预期：至少 `app/page.tsx`、`app/research/[id]/page.tsx`、`src/GPTResearcher.tsx` 的默认设置缺少 `language`，类型检查失败。这是本任务的失败验证。

- [ ] **步骤 2：实现语言选择组件**

新建 `LanguageSelector.tsx`：

```tsx
import { ReportLanguage } from "@/types/data";

interface LanguageSelectorProps {
  language: ReportLanguage;
  onLanguageChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
}

export default function LanguageSelector({
  language,
  onLanguageChange,
}: LanguageSelectorProps) {
  return (
    <div className="form-group">
      <label htmlFor="language" className="agent_question">
        报告语言
      </label>
      <select
        id="language"
        name="language"
        value={language}
        onChange={onLanguageChange}
        className="form-control-static"
      >
        <option value="Chinese (Simplified)">中文（简体）</option>
        <option value="English">English</option>
      </select>
    </div>
  );
}
```

- [ ] **步骤 3：接入桌面 Preference 和移动端设置**

在 `ResearchForm.tsx` 中导入组件，从 `chatBoxSettings` 解构 `language`，并在“Report Source”后渲染：

```tsx
<LanguageSelector
  language={language}
  onLanguageChange={onFormChange}
/>
```

在 `MobileLayout.tsx` 的现有设置区增加相同的“报告语言”下拉框，更新时保持其他设置：

```tsx
onChange={(event) =>
  setChatBoxSettings({
    ...chatBoxSettings,
    language: event.target.value as ReportLanguage,
  })
}
```

- [ ] **步骤 4：给三个入口补齐中文默认值**

在以下默认设置对象中都加入：

```typescript
language: "Chinese (Simplified)",
```

目标文件：

- `frontend/nextjs/app/page.tsx`
- `frontend/nextjs/app/research/[id]/page.tsx`
- `frontend/nextjs/src/GPTResearcher.tsx`

由于前两个入口先展开默认值、再展开 localStorage 中的旧设置，旧用户没有 `language` 字段时会自然获得中文默认值；已有选择则继续保留。

- [ ] **步骤 5：把语言加入 WebSocket 启动消息**

在 `useWebSocket.ts` 中从设置解构 `language`，并在 `dataToSend` 中加入：

```typescript
language,
```

不要修改聊天 `/api/chat` 请求，因为该请求不是报告生成入口。

- [ ] **步骤 6：运行前端类型检查和构建**

```bash
cd frontend/nextjs
npx tsc --noEmit
npm run build
```

预期：类型检查和生产构建均成功；没有引入新的前端测试依赖。

- [ ] **步骤 7：提交本任务**

```bash
git add frontend/nextjs/types/data.ts frontend/nextjs/components/Settings/LanguageSelector.tsx frontend/nextjs/components/Task/ResearchForm.tsx frontend/nextjs/components/layouts/MobileLayout.tsx frontend/nextjs/hooks/useWebSocket.ts frontend/nextjs/app/page.tsx 'frontend/nextjs/app/research/[id]/page.tsx' frontend/nextjs/src/GPTResearcher.tsx
git commit -m "feat: add report language preference"
```

---

### 任务 5：端到端回归和可视化检查

**文件：**
- 不新增业务文件
- 如验证中发现缺陷，只修改前四个任务列出的文件及其对应测试

**接口：**
- 验证完整链路：Preference -> localStorage -> WebSocket -> 后端校验 -> `cfg.language` -> 报告提示词。

- [ ] **步骤 1：运行后端聚焦测试**

```bash
pytest tests/test_report_language.py tests/test_report_language_requests.py tests/test_report_language_propagation.py tests/test_websocket_manager.py -v
```

预期：全部通过。

- [ ] **步骤 2：运行前端静态验证**

```bash
cd frontend/nextjs
npx tsc --noEmit
npm run build
```

预期：两个命令退出码均为 0。

- [ ] **步骤 3：运行代码质量检查**

从仓库根目录运行：

```bash
git diff --check
git status --short
```

预期：`git diff --check` 无输出；`git status` 只显示本功能相关文件和用户已有变更。

- [ ] **步骤 4：使用浏览器验证 Preference 和持久化**

启动应用后检查桌面和移动视口：

1. Preference 中显示“报告语言”。
2. 默认选中“中文（简体）”。
3. 切换到 `English`，关闭并重新打开 Preference 后仍为 `English`。
4. 刷新页面后仍保留已选语言。
5. 控件文字不溢出、不与相邻设置重叠。

- [ ] **步骤 5：验证两种报告语言**

分别新建两个短报告：

```text
中文：请简要说明云端部署 AI 应用的三个优点。
English: Summarize three benefits of deploying AI applications in the cloud.
```

验证中文任务的后端研究员配置为 `Chinese (Simplified)` 且正文为中文；英文任务配置为 `English` 且正文为英文。两次任务之间不得重启容器，以证明语言是任务级而非全局配置。

- [ ] **步骤 6：检查最终差异并提交修正**

```bash
git diff --stat
git diff --check
git status --short
```

如果验证阶段产生修正，只暂存本功能涉及的明确文件：

```bash
git add gpt_researcher/utils/language.py gpt_researcher/agent.py gpt_researcher/skills/deep_research.py backend/server/server_utils.py backend/server/websocket_manager.py backend/server/app.py backend/report_type/basic_report/basic_report.py backend/report_type/detailed_report/detailed_report.py frontend/nextjs/types/data.ts frontend/nextjs/components/Settings/LanguageSelector.tsx frontend/nextjs/components/Task/ResearchForm.tsx frontend/nextjs/components/layouts/MobileLayout.tsx frontend/nextjs/hooks/useWebSocket.ts frontend/nextjs/app/page.tsx 'frontend/nextjs/app/research/[id]/page.tsx' frontend/nextjs/src/GPTResearcher.tsx tests/test_report_language.py tests/test_report_language_requests.py tests/test_report_language_propagation.py tests/test_websocket_manager.py
git commit -m "fix: complete report language preference"
```

不要提交 `.env`、API Key、构建产物或与本功能无关的文件。
