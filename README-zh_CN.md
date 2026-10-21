<div align="center" id="top">

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord](https://img.shields.io/discord/1127851779011391548?logo=discord&logoColor=white&label=Discord&color=34b76a&style=for-the-badge)](https://discord.gg/QgZXvJAccX)


[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Skill](https://img.shields.io/badge/Claude%20Skill-skills.sh-blueviolet?style=flat&logo=anthropic&logoColor=white)](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

[English](README.md) | [中文](README-zh_CN.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md) | [Русский](README-ru_RU.md)

</div>

# 🔎 GPT Researcher

**GPT Researcher 是首个开放的深度研究代理，可针对任意任务开展网络与本地研究。**

代理可以生成详细、正式且客观的研究报告，并提供自定义选项，专注于相关资源、结构框架和经验报告。GPT Researcher 早已不止于 RAG：规划代理与执行代理将每个任务拆解为研究问题，[决策模型](https://docs.gptr.dev/docs/gpt-researcher/gptr/context-filter)只保留真正有助于回答问题的上下文，[多代理](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)工作流协调各专业代理完成从规划到发布的全过程，[递归深度研究](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research)则从广度和深度两方面探索主题。研究并行执行，因此快速、稳定、可靠，并能减少错误信息。

**我们的使命是利用人工智能的力量，为个人和组织提供准确、客观和事实的信息。**

## 为什么选择GPT Researcher?

- 人工研究要形成客观结论可能需要数周时间，耗费大量资源和精力。
- 基于过时信息训练的 LLM 会产生幻觉，难以胜任当下的研究任务。
- 当前的 LLM 存在 token 限制，不足以生成长篇研究报告。
- 现有服务的网络资源有限，容易导致错误信息和肤浅的结果。
- 只选用部分网络资源可能给研究任务带来偏见。

## 演示
<a href="https://www.youtube.com/watch?v=f60rlc_QCxE" target="_blank" rel="noopener">
  <img src="https://github.com/user-attachments/assets/ac2ec55f-b487-4b3f-ae6f-b8743ad296e4" alt="Demo video" width="800" target="_blank" />
</a>

## 作为 Claude Skill 安装

通过将 GPT Researcher 安装为 [Claude Skill](https://skills.sh/assafelovic/gpt-researcher/gpt-researcher)，扩展 Claude 的深度研究能力：

```bash
npx skills add assafelovic/gpt-researcher
```

安装后，Claude 即可在对话中直接使用 GPT Researcher 的深度研究能力。

## 架构

核心思想是使用“计划者”和“执行”代理：计划者生成研究问题，执行代理收集相关信息，最后由发布者将所有发现汇总为一份完整的研究报告。

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527">
</div>

步骤：
* 根据研究查询创建特定任务的代理。
* 生成一组研究问题，共同形成对该任务的客观意见。
* 使用爬虫代理为每个问题收集信息。
* 对每个资源进行汇总并跟踪其来源。
* 过滤并聚合所有摘要，生成最终研究报告。

## 教程
 - [运行原理](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [如何安装](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [现场演示](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## 特性

- 📝 基于网络与本地文档生成详细的研究报告。
- 🖼️ 智能抓取并筛选报告配图。
- 🍌 使用 Google Gemini（Nano Banana）**生成 AI 内联配图**。
- 📜 生成超过 2,000 字的详细报告。
- 🌐 汇总 20 多个网络资源，形成客观结论。
- 🎯 通过 [Jev](https://docs.gptr.dev/docs/gpt-researcher/gptr/context-filter) 进行智能上下文过滤，默认无需 API 密钥或 embeddings。
- 🖥️ 提供轻量（HTML/CSS/JS）与生产级（NextJS + Tailwind）两种前端。
- 🔍 支持 JavaScript 渲染的网页抓取。
- 📂 在整个研究过程中维护记忆与上下文。
- 📄 将报告导出为 PDF、Word 等格式。

## 📖 文档

请参阅[文档](https://docs.gptr.dev/docs/gpt-researcher/getting-started)了解：
- 安装与设置指南
- 配置与自定义选项
- 操作指南示例
- 完整 API 参考

## ⚙️ 快速开始

### 安装

1. 安装 Python 3.12 或更高版本。[指南](https://www.tutorialsteacher.com/python/install-python)。
2. 克隆项目并进入目录：

    ```bash
    git clone https://github.com/assafelovic/gpt-researcher.git
    cd gpt-researcher
    ```

3. 通过导出或写入 `.env` 文件设置 API 密钥。

    ```bash
    export OPENAI_API_KEY={Your OpenAI API Key here}
    export TAVILY_API_KEY={Your Tavily API Key here}
    ```

    （可选）如需增强追踪与可观测性，还可以设置：
    
    ```bash
    # export LANGCHAIN_TRACING_V2=true
    # export LANGCHAIN_API_KEY={Your LangChain API Key here}
    ```

    如使用自定义的 OpenAI 兼容 API（如本地模型、其他提供商），还可以设置：
    
    ```bash
    export OPENAI_BASE_URL={Your custom API base URL here}
    ```

4. 安装依赖并启动服务器：

    ```bash
    pip install -r requirements.txt
    python -m uvicorn main:app --reload
    ```

访问 [http://localhost:8000](http://localhost:8000) 即可开始。

其他安装方式（如 Poetry 或虚拟环境）请参阅[快速开始页面](https://docs.gptr.dev/docs/gpt-researcher/getting-started)。

## 以 PIP 包运行
```bash
pip install gpt-researcher

```
### 示例用法：
```python
...
from gpt_researcher import GPTResearcher

query = "why is Nvidia stock going up?"
researcher = GPTResearcher(query=query)
# Conduct research on the given query
research_result = await researcher.conduct_research()
# Write the report
report = await researcher.write_report()
...
```

**更多示例与配置请参阅 [PIP 文档](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)页面。**

### 🔧 MCP 客户端
GPT Researcher 支持 MCP 集成，可连接 GitHub 仓库、数据库和自定义 API 等专用数据源，让数据源研究与网络搜索结合使用。

```bash
export RETRIEVER=tavily,mcp  # Enable hybrid web + MCP research
```

```python
from gpt_researcher import GPTResearcher
import asyncio
import os

async def mcp_research_example():
    # Enable MCP with web search
    os.environ["RETRIEVER"] = "tavily,mcp"
    
    researcher = GPTResearcher(
        query="What are the top open source web research agents?",
        mcp_configs=[
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
            }
        ]
    )
    
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    return report
```

> 完整的 MCP 文档与高级示例请访问 [MCP 集成指南](https://docs.gptr.dev/docs/gpt-researcher/retrievers/mcp-configs)。

## 🍌 内联图像生成

GPT Researcher 可使用 Google 的 Gemini 模型（Nano Banana）自动生成并在研究报告中嵌入 AI 创建的插图。

```bash
# Enable in your .env file
IMAGE_GENERATION_ENABLED=true
GOOGLE_API_KEY=your_google_api_key
IMAGE_GENERATION_MODEL=models/gemini-2.5-flash-image
```

启用后，系统将：
1. 分析研究上下文，识别可视化机会
2. 在研究阶段预生成 2-3 张相关图像
3. 在撰写报告时将它们内联嵌入

图像以与 GPT Researcher UI 一致的深色模式风格生成，呈现带青色点缀的专业信息图美学。

详情请参阅文档中的[图像生成](https://docs.gptr.dev/docs/gpt-researcher/gptr/image_generation)。

## ✨ 深度研究

GPT Researcher 现已包含深度研究（Deep Research）——一种高级递归研究工作流，以智能体的方式在深度和广度上探索主题。该功能采用树状探索模式，在深入研究子主题的同时保持对研究主题的全局视野。

- 🌳 树状探索，深度与广度可配置
- ⚡️ 并发处理，更快出结果
- 🤝 跨研究分支的智能上下文管理
- ⏱️ 每次深度研究约 5 分钟
- 💰 每次研究成本约 $0.4（使用 o3-mini、reasoning effort 设为 "high"）

详情请参阅文档中的[深度研究](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research)。

## 🎯 使用 Jev 的智能上下文过滤

每次研究都会抓取数十个页面，而每个页面中只有一部分内容有助于回答问题。在内容进入 LLM 之前，GPT Researcher 会决定保留哪些段落。默认使用 TypeSafe 的 **[Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)**——该模型评估的是每个段落对问题的实际用处，而不是词语或 embedding 的相似度。

**在相同成本下，Jev 的上下文相关性比 embeddings 高 59%**（保留段落相关率 73% vs 46%）。我们在 28 个研究任务上对各种方案做了基准测试：重放同一批抓取来源，只更换过滤器：

| 上下文过滤器 | 保留的相关段落 | 与 embeddings 正面对比 | 过滤耗时 | 每份报告成本 | 依赖 |
|---|---|---|---|---|---|
| **Jev**（默认） | **73%** | **15 胜 · 10 平 · 3 负** | 1.7s | $0.115 | `TYPESAFE_API_KEY` |
| 关键词（回退） | 51% | 14 胜 · 8 平 · 6 负 | 0.02s | $0.116 | 无 |
| Embeddings | 46% | — | 1.0s | $0.117 | 一个 embedding 提供商 |
| 不过滤 | — | 13 胜 · 11 平 · 4 负 | — | $0.192 | 无 |

无论使用哪种过滤器，撰写报告约需 45 秒，因此过滤器只影响总耗时中的过滤环节。对开放式问题不做过滤会写出覆盖面最广的报告，但成本高出 65%。

**无需任何配置。** 设置了 `TYPESAFE_API_KEY` 时使用 Jev；未设置或 Jev 调用失败时，GPT Researcher 回退到本地运行的关键词（BM25）排序，无需 API 密钥、模型或 embeddings。Embeddings 仍可作为选项使用。

```bash
export TYPESAFE_API_KEY=...   # use Jev (the default when a key is set)
export CONTEXT_FILTER=auto    # auto | jev | keyword | embeddings | none
```

方法论、注意事项与复现方式请参阅 [Context Filter 文档](https://docs.gptr.dev/docs/gpt-researcher/gptr/context-filter)与[完整基准测试](evals/context_filter)。

## 使用 Docker 运行

> **步骤 1** - [安装 Docker](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started-with-docker)

> **步骤 2** - 复制 `.env.example` 文件，在其中填入你的 API 密钥，并将文件保存为 `.env`

> **步骤 3** - 在 docker-compose 文件中注释掉你不想通过 Docker 运行的服务。

```bash
docker-compose up --build
```

如果不行，尝试去掉连字符运行：
```bash
docker compose up --build
```

> **步骤 4** - 默认情况下（如果你没有修改 docker-compose 文件），此流程将启动 2 个进程：
 - 运行在 localhost:8000 的 Python 服务器<br>
 - 运行在 localhost:3000 的 React 应用<br>

在任何浏览器访问 localhost:3000，开始研究吧！


## 📄 基于本地文档的研究

你可以让 GPT Researcher 基于本地文档执行研究任务。目前支持的文件格式有：PDF、纯文本、CSV、Excel、Markdown、PowerPoint 和 Word 文档。

步骤 1：设置环境变量 `DOC_PATH`，指向文档所在的文件夹。

```bash
export DOC_PATH="./my-docs"
```

步骤 2： 
 - 如果你运行的是 localhost:8000 上的前端应用，只需在 "Report Source" 下拉选项中选择 "My Documents"。
 - 如果你通过 [PIP 包](https://docs.tavily.com/guides/gpt-researcher/gpt-researcher#pip-package)运行 GPT Researcher，在实例化 `GPTResearcher` 类时将 `report_source` 参数设为 "local"（[代码示例见此](https://docs.gptr.dev/docs/gpt-researcher/context/tailored-research)）。


## 🤖 MCP 服务器

我们的 MCP 服务器已迁移至独立仓库：[gptr-mcp](https://github.com/assafelovic/gptr-mcp)。

GPT Researcher MCP 服务器让 Claude 等 AI 应用能够执行深度研究。虽然 LLM 应用可以通过 MCP 访问网络搜索工具，但 GPT Researcher MCP 能带来更深入、更可靠的研究结果。

特性：
- 为 AI 助手提供深度研究能力
- 优化上下文使用，信息质量更高
- 推理更完善，结果更全面
- 集成 Claude Desktop

详细的安装与使用说明请访问[官方仓库](https://github.com/assafelovic/gptr-mcp)。


## 👪 多代理助手
随着 AI 从提示工程和 RAG 演进到多代理系统，我们很高兴推出基于 [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/) 和 [AG2](https://github.com/ag2ai/ag2) 构建的多代理助手。

借助多代理框架，通过多个具备专业技能的代理协作，研究过程的深度与质量都能显著提升。本项目展示了由多个 AI 代理组成的团队如何就给定主题协同开展研究，从规划到发布。

一次运行平均可生成 5-6 页的研究报告，支持 PDF、Docx 和 Markdown 等多种格式。

请点击[这里](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents)查看，或前往我们的文档了解 [LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph) 与 [AG2](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/ag2) 的更多信息。

## 🔍 可观测性

GPT Researcher 支持 **LangSmith** 以增强链路追踪和可观测性，特别适用于调试和优化复杂的多智能体工作流。

要开启追踪：
1. 设置以下环境变量：
   ```bash
   export LANGCHAIN_TRACING_V2=true
   export LANGCHAIN_API_KEY=您的_API_KEY
   export LANGCHAIN_PROJECT="gpt-researcher"
   ```
2. 正常运行研究任务。所有基于 LangGraph 的智能体交互将自动被追踪，并可在您的 LangSmith 控制台中查看可视化结果。

## 🖥️ 前端应用

GPT Researcher 现已提供增强版前端，改善用户体验并简化研究流程。前端提供：

- 直观的研究查询输入界面
- 研究任务实时进度跟踪
- 研究结果的交互式展示
- 可自定义设置，打造个性化研究体验

提供两种部署方式：
1. 由 FastAPI 提供服务的轻量静态前端
2. 功能丰富的 NextJS 应用

详细的设置说明与前端功能信息请参阅[文档页面](https://docs.gptr.dev/docs/gpt-researcher/frontend/introduction)。

## 🚀 贡献
我们非常欢迎贡献！如果你有兴趣，请查看[贡献指南](https://github.com/assafelovic/gpt-researcher/blob/master/CONTRIBUTING.md)。

如果你有兴趣加入我们的使命，请查看我们的 [路线图](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) 页面，并通过我们的 [Discord 社区](https://discord.gg/QgZXvJAccX) 联系我们。
<a href="https://github.com/assafelovic/gpt-researcher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=assafelovic/gpt-researcher&max=1000" />
</a>
## ✉️ 支持 / 联系我们
- [社区 Discord](https://discord.gg/spBgZmm3Xe)
- 作者邮箱: assaf.elovic@gmail.com

## 🛡 免责声明

本项目 GPT Researcher 是一个实验性应用程序，按“现状”提供，不含任何明示或暗示的保证。我们基于 Apache 2 许可证共享代码，仅用于学术目的。本文内容不构成任何学术建议，也不建议在学术或研究论文中使用。

我们对客观研究主张的看法：
1. GPT Researcher 的主要目标是减少错误和有偏见的事实。如何做到？我们假设抓取的网站越多，出现错误数据的可能性就越小。通过在每次研究中抓取多个网站并选择出现频率最高的信息，这些信息全部出错的概率极低。
2. 我们的目标不是消除偏见，而是尽可能减少偏见。**作为一个社区，我们在这里探索最有效的人机/LLM 交互方式**。
3. 在研究过程中，人们也容易产生偏见，因为大多数人对自己研究的课题已有自己的看法。这个工具会搜罗多种观点，并均匀地解释各种不同的视角，而有偏见的人是绝对读不到这些观点的。

---

<p align="center">
<a href="https://star-history.com/#assafelovic/gpt-researcher">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=assafelovic/gpt-researcher&type=Date" />
  </picture>
</a>
</p>


<p align="right">
  <a href="#top">⬆️ 返回顶部</a>
</p>
