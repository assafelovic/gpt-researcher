<div align="center">

# 🔎 GPT Researcher

**[🇨🇳 中文](README-zh_CN.md) | [English](README.md) | [日本語](README-ja_JP.md) | [한국어](README-ko_KR.md)]**

---

<img src="https://github.com/assafelovic/gpt-researcher/assets/13554167/20af8286-b386-44a5-9a83-3be1365139c3" alt="Logo" width="80">

####

[![Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white&color=0891b2)](https://gptr.dev)
[![Documentation](https://img.shields.io/badge/Documentation-DOCS-f472b6?logo=googledocs&logoColor=white&style=for-the-badge)](https://docs.gptr.dev)
[![Discord Follow](https://img.shields.io/discord/1127851779011391548?style=for-the-badge&logo=discord&label=Chat%20on%20Discord)](https://discord.gg/QgZXvJAccX)

[![PyPI version](https://img.shields.io/pypi/v/gpt-researcher?logo=pypi&logoColor=white&style=flat)](https://badge.fury.io/py/gpt-researcher)
![GitHub Release](https://img.shields.io/github/v/release/assafelovic/gpt-researcher?style=flat&logo=github)
[![Open In Colab](https://img.shields.io/static/v1?message=Open%20in%20Colab&logo=googlecolab&labelColor=grey&color=yellow&label=%20&style=flat&logoSize=40)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)
[![Docker Image Version](https://img.shields.io/docker/v/elestio/gpt-researcher/latest?arch=amd64&style=flat&logo=docker&logoColor=white&color=1D63ED)](https://hub.docker.com/r/gptresearcher/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)

</div>

# 🔎 GPT Researcher

**GPT Researcher 是一个智能体代理，专为各种任务的综合在线研究而设计。**

代理可以生成详细、正式且客观的研究报告，并提供自定义选项，专注于相关资源、结构框架和经验报告。受最近发表的[Plan-and-Solve](https://arxiv.org/abs/2305.04091) 和[RAG](https://arxiv.org/abs/2005.11401) 论文的启发，GPT Researcher 解决了速度、确定性和可靠性等问题，通过并行化的代理运行，而不是同步操作，提供了更稳定的性能和更高的速度。

**我们的使命是利用人工智能的力量，为个人和组织提供准确、客观和事实的信息。**

## 为什么选择GPT Researcher?

- 因为人工研究任务形成客观结论可能需要时间和经历，有时甚至需要数周才能找到正确的资源和信息。
- 目前的LLM是根据历史和过时的信息进行训练的，存在严重的幻觉风险，因此几乎无法胜任研究任务。
- 网络搜索的解决方案（例如 ChatGPT + Web 插件）仅考虑有限的资源和内容，在某些情况下会导致肤浅的结论或不客观的答案。
- 只使用部分资源可能会在确定研究问题或任务的正确结论时产生偏差。

## 架构
主要思想是运行"**计划者**"和"**执行**"代理，而**计划者**生成问题进行研究，"**执行**"代理根据每个生成的研究问题寻找最相关的信息。最后，"**计划者**"过滤和聚合所有相关信息并创建研究报告。<br /> <br /> 
代理同时利用 gpt-40-mini 和 gpt-4o（128K 上下文）来完成一项研究任务。我们仅在必要时使用这两种方法对成本进行优化。**研究任务平均耗时约 3 分钟，成本约为 ~0.1 美元**。

<div align="center">
<img align="center" height="500" src="https://cowriter-images.s3.amazonaws.com/architecture.png">
</div>

详细说明:
* 根据研究搜索或任务创建特定领域的代理。
* 生成一组研究问题，这些问题共同形成答案对任何给定任务的客观意见。
* 针对每个研究问题，触发一个爬虫代理，从在线资源中搜索与给定任务相关的信息。
* 对于每一个抓取的资源，根据相关信息进行汇总，并跟踪其来源。
* 最后，对所有汇总的资料来源进行过滤和汇总，并生成最终研究报告。

---

**💡 查看完整的中文文档：[README-zh_CN.md](README-zh_CN.md)**

