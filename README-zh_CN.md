# 🔎 GPT Researcher
[![Official Website](https://img.shields.io/badge/Official%20Website-gptr.dev-blue?style=for-the-badge&logo=world&logoColor=white)](https://gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/MN9M86kb?style=for-the-badge)](https://discord.gg/MN9M86kb)

[![GitHub Repo stars](https://img.shields.io/github/stars/assafelovic/gpt-researcher?style=social)](https://github.com/assafelovic/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)

-  [English](README.md)
-  [中文](README-zh_CN.md)
-  [日本語](README-ja_JP.md)


**GPT Researcher 是一个智能体代理，专为各种任务的综合在线研究而设计。**

代理可以生成详细、正式且客观的研究报告，并提供自定义选项，专注于相关资源、结构框架和经验报告。受最近发表的[Plan-and-Solve](https://arxiv.org/abs/2305.04091) 和[RAG](https://arxiv.org/abs/2005.11401) 论文的启发，GPT Researcher 解决了速度、确定性和可靠性等问题，通过并行化的代理运行，而不是同步操作，提供了更稳定的性能和更高的速度。

**我们的使命是利用人工智能的力量，为个人和组织提供准确、客观和事实的信息。**

## 为什么选择GPT Researcher?

- 因为人工研究任务形成客观结论可能需要时间和经历，有时甚至需要数周才能找到正确的资源和信息。
- 目前的LLM是根据历史和过时的信息进行训练的，存在严重的幻觉风险，因此几乎无法胜任研究任务。
- 网络搜索的解决方案（例如 ChatGPT + Web 插件）仅考虑有限的资源和内容，在某些情况下会导致肤浅的结论或不客观的答案。
- 只使用部分资源可能会在确定研究问题或任务的正确结论时产生偏差。

## 架构
主要思想是运行“**计划者**”和“**执行**”代理，而**计划者**生成问题进行研究，“**执行**”代理根据每个生成的研究问题寻找最相关的信息。最后，“**计划者**”过滤和聚合所有相关信息并创建研究报告。<br /> <br /> 
代理同时利用 gpt3.5-turbo 和 gpt-4o（128K 上下文）来完成一项研究任务。我们仅在必要时使用这两种方法对成本进行优化。**研究任务平均耗时约 3 分钟，成本约为 ~0.1 美元**。

<div align="center">
<img align="center" height="500" src="https://cowriter-images.s3.amazonaws.com/architecture.png">
</div>


详细说明:
* 根据研究搜索或任务创建特定领域的代理。
* 生成一组研究问题，这些问题共同形成答案对任何给定任务的客观意见。
* 针对每个研究问题，触发一个爬虫代理，从在线资源中搜索与给定任务相关的信息。
* 对于每一个抓取的资源，根据相关信息进行汇总，并跟踪其来源。
* 最后，对所有汇总的资料来源进行过滤和汇总，并生成最终研究报告。

## 演示
https://github.com/assafelovic/gpt-researcher/assets/13554167/a00c89a6-a295-4dd0-b58d-098a31c40fda

## 教程
 - [运行原理](https://docs.gptr.dev/blog/building-gpt-researcher)
 - [如何安装](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [现场演示](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)

## 特性
- 📝 生成研究问题、大纲、资源和课题报告
- 🌐 每项研究汇总超过20个网络资源，形成客观和真实的结论
- 🖥️ 包括易于使用的web界面 (HTML/CSS/JS)
- 🔍 支持JavaScript网络资源抓取功能
- 📂 追踪访问过和使用过的网络资源和来源
- 📄 将研究报告导出为PDF或其他格式...

## 📖 文档

请参阅[此处](https://docs.gptr.dev/docs/gpt-researcher/getting-started)，了解完整文档：

- 入门（安装、设置环境、简单示例）
- 操作示例（演示、集成、docker 支持）
- 参考资料（API完整文档）
- Tavily 应用程序接口集成（核心概念的高级解释）

## 快速开始
> **步骤 0** - 安装 Python 3.11 或更高版本。[参见此处](https://www.tutorialsteacher.com/python/install-python) 获取详细指南。

<br />

> **步骤 1** - 下载项目

```bash
$ git clone https://github.com/assafelovic/gpt-researcher.git
$ cd gpt-researcher
```

<br />

> **步骤2** -安装依赖项
```bash
$ pip install -r requirements.txt
```
<br />

> **第 3 步** - 使用 OpenAI 密钥和 Tavily API 密钥创建 .env 文件，或直接导出该文件

```bash
$ export OPENAI_API_KEY={Your OpenAI API Key here}
```
```bash
$ export TAVILY_API_KEY={Your Tavily API Key here}
```

- **LLM，我们推荐使用 [OpenAI GPT](https://platform.openai.com/docs/guides/gpt)**，但您也可以使用 [Langchain Adapter](https://python.langchain.com/docs/guides/adapters/openai) 支持的任何其他 LLM 模型（包括开源），只需在 config/config.py 中更改 llm 模型和提供者即可。请按照 [这份指南](https://python.langchain.com/docs/integrations/llms/) 学习如何将 LLM 与 Langchain 集成。
- **对于搜索引擎，我们推荐使用 [Tavily Search API](https://app.tavily.com)（已针对 LLM 进行优化）**，但您也可以选择其他搜索引擎，只需将 config/config.py 中的搜索提供程序更改为 "duckduckgo"、"googleAPI"、"googleSerp "或 "searx "即可。然后在 config.py 文件中添加相应的 env API 密钥。
- **我们强烈建议使用 [OpenAI GPT](https://platform.openai.com/docs/guides/gpt) 模型和 [Tavily Search API](https://app.tavily.com) 以获得最佳性能。**
<br />

> **第 4 步** - 使用 FastAPI 运行代理

```bash
$ uvicorn main:app --reload
```
<br />

> **第 5 步** - 在任何浏览器上访问 http://localhost:8000，享受研究乐趣！

要了解如何开始使用 Docker 或了解有关功能和服务的更多信息，请访问 [documentation](https://docs.gptr.dev) 页面。

## 🚀 贡献
我们非常欢迎您的贡献！如果您感兴趣，请查看 [contributing](CONTRIBUTING.md)。

如果您有兴趣加入我们的任务，请查看我们的 [路线图](https://trello.com/b/3O7KBePw/gpt-researcher-roadmap) 页面，并通过我们的 [Discord 社区](https://discord.gg/QgZXvJAccX) 联系我们。

## ✉️ 支持 / 联系我们
- [社区讨论区](https://discord.gg/spBgZmm3Xe)
- 我们的邮箱: support@tavily.com

## 🛡 免责声明

本项目 "GPT Researcher "是一个实验性应用程序，按 "现状 "提供，不做任何明示或暗示的保证。我们根据 MIT 许可分享用于学术目的的代码。本文不提供任何学术建议，也不建议在学术或研究论文中使用。

我们对客观研究主张的看法：
1.  我们抓取系统的全部目的是减少不正确的事实。如何解决？我们抓取的网站越多，错误数据的可能性就越小。我们每项研究都会收集20条信息，它们全部错误的可能性极低。
2. 我们的目标不是消除偏见，而是尽可能减少偏见。**作为一个社区，我们在这里探索最有效的人机互动**。
3. 在研究过程中，人们也容易产生偏见，因为大多数人对自己研究的课题都有自己的看法。这个工具可以搜罗到许多观点，并均匀地解释各种不同的观点，而有偏见的人是绝对读不到这些观点的。

**请注意，使用 GPT-4 语言模型可能会因使用令牌而产生高昂费用**。使用本项目即表示您承认有责任监控和管理自己的令牌使用情况及相关费用。强烈建议您定期检查 OpenAI API 的使用情况，并设置任何必要的限制或警报，以防止发生意外费用。

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
