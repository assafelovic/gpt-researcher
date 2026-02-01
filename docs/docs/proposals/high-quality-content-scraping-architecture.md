# RFC: 高质量内容与图片抓取架构

> **状态**: 提案
> **作者**: 社区贡献者
> **创建日期**: 2026-01-31
> **目标版本**: v4.x

## 概述

本提案分析 GPT-Researcher 当前的抓取能力，并推荐从网络来源获取高质量文本内容和相关图片的最优架构。

---

## 目录

1. [当前架构分析](#1-当前架构分析)
2. [内置工具与外部工具对比](#2-内置工具与外部工具对比)
3. [推荐的混合架构](#3-推荐的混合架构)
4. [实施指南](#4-实施指南)
5. [决策矩阵：何时使用何种工具](#5-决策矩阵何时使用何种工具)
6. [成本分析](#6-成本分析)

---

## 1. 当前架构分析

### 1.1 当前数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     当前 GPT-Researcher 流程                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用户查询                                                               │
│       │                                                                 │
│       ▼                                                                 │
│   Tavily 搜索（Basic 模式）                                              │
│   - 返回: URL + 简短摘要                                                 │
│   - 成本: 每次查询 1 个积分                                               │
│   - 不返回: raw_content, 图片                                            │
│       │                                                                 │
│       ▼                                                                 │
│   URL 列表提取                                                           │
│   - 只使用 href                                                          │
│   - 摘要内容 (body) 被丢弃 ❌                                             │
│       │                                                                 │
│       ▼                                                                 │
│   BeautifulSoup 抓取（默认）                                             │
│   - 重新抓取每个 URL                                                     │
│   - 从 HTML 提取文本 + 图片                                               │
│   - JS 渲染页面可能失败                                                   │
│       │                                                                 │
│       ▼                                                                 │
│   上下文压缩                                                             │
│   - 向量相似度过滤                                                       │
│   - 返回相关片段                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 当前配置

```python
# gpt_researcher/config/variables/default.py 中的默认设置
{
    "SCRAPER": "bs",                    # BeautifulSoup（基础 HTML 解析器）
    "MAX_SCRAPER_WORKERS": 15,          # 并行抓取工作线程
    "SCRAPER_RATE_LIMIT_DELAY": 0.0,    # 无速率限制
}

# retrievers/tavily/tavily_search.py 中的 Tavily 搜索设置
results = self._search(
    self.query,
    search_depth="basic",           # 仅 Basic 模式
    include_raw_content=False,      # 无完整内容
    include_images=False,           # 无图片
)
```

### 1.3 当前方法的问题

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| Tavily 摘要被丢弃 | 浪费 API 响应数据 | 中 |
| Tavily 不返回 raw_content | 必须重新抓取每个 URL | 高 |
| Tavily 不返回图片 | 缺失搜索相关图片 | 中 |
| BS 对 JS 页面失败 | React/Vue 站点内容缺失 | 高 |
| 无反爬虫处理 | 被许多站点屏蔽 | 中 |

---

## 2. 内置工具与外部工具对比

### 2.1 可用抓取工具

#### 内置工具（免费）

| 工具 | 文件位置 | 能力 | 限制 |
|------|----------|------|------|
| **BeautifulSoup** | `scraper/beautiful_soup/` | 基础 HTML 解析，快速 | 无 JS 渲染，被反爬阻挡 |
| **WebBaseLoader** | `scraper/web_base_loader/` | LangChain 集成 | 与 BS 相同 |
| **Browser (Selenium)** | `scraper/browser/` | JS 渲染，截图 | 慢，资源消耗大 |
| **NoDriver** | `scraper/browser/nodriver_scraper.py` | 无头浏览器，隐蔽 | 配置复杂 |
| **PyMuPDF** | `scraper/pymupdf/` | PDF 提取 | 仅 PDF |
| **ArXiv** | `scraper/arxiv/` | 学术论文 | 仅 ArXiv |

#### 外部 API 工具（付费）

| 工具 | 文件位置 | 能力 | 成本 |
|------|----------|------|------|
| **Tavily Extract** | `scraper/tavily_extract/` | 专业提取，干净内容 | 每 5 个 URL 1 积分 |
| **FireCrawl** | `scraper/firecrawl/` | LLM 优化，处理 JS | 约 $0.001/页 |
| **Tavily Search Advanced** | `retrievers/tavily/` | 搜索中包含原始内容+图片 | 每查询 2 积分 |

### 2.2 详细能力矩阵

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            抓取器能力矩阵                                            │
├──────────────────┬───────┬───────┬─────────┬─────────┬──────────┬──────────────────┤
│ 能力              │  BS   │Browser│NoDriver │ Tavily  │ FireCrawl│ Tavily Search Adv│
│                  │       │       │         │ Extract │          │                  │
├──────────────────┼───────┼───────┼─────────┼─────────┼──────────┼──────────────────┤
│ 静态 HTML        │  ✅   │  ✅   │   ✅    │   ✅    │    ✅    │       ✅         │
│ JS 渲染          │  ❌   │  ✅   │   ✅    │   ✅    │    ✅    │       ✅         │
│ 反爬虫绕过       │  ❌   │  ⚠️   │   ✅    │   ✅    │    ✅    │       ✅         │
│ 干净内容         │  ⚠️   │  ⚠️   │   ⚠️    │   ✅    │    ✅    │       ✅         │
│ 图片提取         │  ✅   │  ✅   │   ✅    │   ⚠️    │    ✅    │       ✅         │
│ 速度             │  ⚡⚡⚡ │  ⚡   │   ⚡⚡   │   ⚡⚡   │    ⚡⚡   │       ⚡⚡⚡       │
│ 成本             │ 免费  │ 免费  │  免费   │  付费   │   付费   │      付费        │
│ 可靠性           │  ⚠️   │  ⚠️   │   ✅    │   ✅    │    ✅    │       ✅         │
│ 配置复杂度       │  低   │  高   │   中    │   低    │   低     │       低         │
└──────────────────┴───────┴───────┴─────────┴─────────┴──────────┴──────────────────┘

图例: ✅ = 完全支持, ⚠️ = 部分/有限, ❌ = 不支持
```

### 2.3 内容质量对比

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      各工具内容质量                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   BeautifulSoup 输出:                                                   │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ "首页 关于 联系 登录                                              │  │
│   │  文章标题                                                        │  │
│   │  作者 | 日期                                                      │  │
│   │  分享 转发                                                        │  │
│   │  正文内容从这里开始，但混杂着导航...                               │  │
│   │  订阅 新闻简报 页脚链接 版权..."                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│   质量: ⭐⭐（包含噪音）                                                │
│                                                                         │
│   Tavily Extract / FireCrawl 输出:                                     │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ "文章标题                                                        │  │
│   │                                                                  │  │
│   │  正文内容从这里开始。这是干净、格式良好的文本，                    │  │
│   │  经过智能提取，移除了所有导航、广告和无关元素..."                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│   质量: ⭐⭐⭐⭐⭐（干净，LLM 友好）                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.4 图片来源对比

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        两种类型的图片                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   类型 1: 搜索相关图片（Tavily include_images）                          │
│   ════════════════════════════════════════════                          │
│   来源: 搜索引擎图片结果                                                 │
│   内容: 与查询相关的通用图片                                             │
│   示例: 搜索 "特斯拉" → 特斯拉汽车照片、Logo、马斯克                     │
│   质量: 适合通用插图                                                     │
│   限制: 可能与特定文章内容不匹配                                         │
│                                                                         │
│   类型 2: 页面嵌入图片（HTML <img> 抓取）                                │
│   ════════════════════════════════════════                               │
│   来源: 从网页 HTML 提取                                                 │
│   内容: 文章图表、图形、信息图                                           │
│   示例: 分析文章中的销售图表                                             │
│   质量: 与文章内容直接相关                                               │
│   限制: 需要页面抓取，可能漏掉懒加载图片                                 │
│                                                                         │
│   🎯 建议: 同时获取两种类型以获得全面结果                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 推荐的混合架构

### 3.1 架构概述

```
┌─────────────────────────────────────────────────────────────────────────┐
│                推荐: 混合抓取架构                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         用户查询                                         │
│                            │                                            │
│                            ▼                                            │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  阶段 1: Tavily Search Advanced                                │   │
│   │  ═══════════════════════════════                               │   │
│   │  参数:                                                         │   │
│   │    search_depth: "advanced"                                    │   │
│   │    include_raw_content: true                                   │   │
│   │    include_images: true                                        │   │
│   │    include_image_descriptions: true                            │   │
│   │                                                                │   │
│   │  返回:                                                         │   │
│   │    ├─ results[].url           (URL 列表)                       │   │
│   │    ├─ results[].content       (摘要)                           │   │
│   │    ├─ results[].raw_content   (完整页面内容) ✅                 │   │
│   │    └─ images[]                (搜索相关图片) ✅                 │   │
│   └──────────────────────────────┬─────────────────────────────────┘   │
│                                  │                                      │
│                    ┌─────────────┴─────────────┐                       │
│                    │                           │                       │
│                    ▼                           ▼                       │
│   ┌──────────────────────────┐   ┌──────────────────────────┐         │
│   │  raw_content 存在        │   │  raw_content 为空/太短   │         │
│   │  且长度 > 500 字符       │   │  或为 JS 渲染页面        │         │
│   └────────────┬─────────────┘   └────────────┬─────────────┘         │
│                │                              │                        │
│                ▼                              ▼                        │
│   ┌──────────────────────────┐   ┌──────────────────────────┐         │
│   │  直接使用 Tavily 内容    │   │  阶段 2: 回退抓取        │         │
│   │  (无需重新抓取)          │   │  ═══════════════════════ │         │
│   │                          │   │  Browser/NoDriver/       │         │
│   │  成本: 0 额外             │   │  FireCrawl 处理 JS 页面  │         │
│   └────────────┬─────────────┘   └────────────┬─────────────┘         │
│                │                              │                        │
│                │                              ├─→ 页面内容              │
│                │                              └─→ 页面图片 (<img>)      │
│                │                                       │               │
│                └──────────────┬────────────────────────┘               │
│                               │                                        │
│                               ▼                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  阶段 3: 内容与图片聚合                                         │   │
│   │  ═══════════════════════                                        │   │
│   │                                                                 │   │
│   │  文本内容:                                                      │   │
│   │    - 首选: Tavily raw_content                                   │   │
│   │    - 回退: 浏览器抓取内容                                        │   │
│   │                                                                 │   │
│   │  图片（合并去重）:                                               │   │
│   │    - Tavily 搜索图片（通用相关性）                               │   │
│   │    - 页面嵌入图片（文章专属）                                    │   │
│   │                                                                 │   │
│   │  图片排序:                                                      │   │
│   │    1. 带 featured/hero/main 类的页面图片（分数: 4）              │   │
│   │    2. 大尺寸页面图片 > 800x500（分数: 3）                        │   │
│   │    3. Tavily 搜索图片（分数: 2）                                 │   │
│   │    4. 中等尺寸页面图片 > 500x300（分数: 1）                      │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 质量层级

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        三个质量层级                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   层级 1: 预算模式（当前默认）                                           │
│   ══════════════════════════                                            │
│   搜索: Tavily Basic（1 积分）                                          │
│   抓取: BeautifulSoup（免费）                                           │
│   图片: 仅页面 <img>                                                    │
│   成本: 约 1 积分/查询                                                   │
│   质量: ⭐⭐⭐                                                           │
│   适用: 预算有限，简单静态网站                                           │
│                                                                         │
│   层级 2: 平衡模式（推荐）                                               │
│   ═════════════════════                                                 │
│   搜索: Tavily Advanced（2 积分）                                       │
│   抓取: 选择性（仅在 raw_content 缺失时）                                │
│   图片: Tavily 图片 + 页面 <img>                                        │
│   成本: 约 2-3 积分/查询                                                 │
│   质量: ⭐⭐⭐⭐                                                          │
│   适用: 一般研究，混合网站类型                                           │
│                                                                         │
│   层级 3: 最高质量模式                                                   │
│   ═══════════════════                                                   │
│   搜索: Tavily Advanced（2 积分）                                       │
│   抓取: 所有 URL 使用 Tavily Extract 或 FireCrawl                       │
│   图片: 所有来源 + 图片描述                                              │
│   成本: 约 5-10 积分/查询                                                │
│   质量: ⭐⭐⭐⭐⭐                                                         │
│   适用: 关键研究，复杂 JS 密集型站点                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 实施指南

### 4.1 配置更改

#### 选项 A: 环境变量

```bash
# .env 文件

# ═══════════════════════════════════════════════════════════════
# 层级 1: 预算模式（当前默认）
# ═══════════════════════════════════════════════════════════════
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=basic
SCRAPER=bs

# ═══════════════════════════════════════════════════════════════
# 层级 2: 平衡模式（推荐）
# ═══════════════════════════════════════════════════════════════
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=browser  # JS 页面回退

# ═══════════════════════════════════════════════════════════════
# 层级 3: 最高质量模式
# ═══════════════════════════════════════════════════════════════
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=tavily_extract  # 或 firecrawl
FIRECRAWL_API_KEY=your_key  # 如果使用 firecrawl
```

#### 选项 B: 代码修改

```python
# gpt_researcher/retrievers/tavily/tavily_search.py

# 之前（当前）
results = self._search(
    self.query,
    search_depth="basic",
    include_raw_content=False,
    include_images=False,
)

# 之后（推荐）
results = self._search(
    self.query,
    search_depth=os.getenv("TAVILY_SEARCH_DEPTH", "advanced"),
    include_raw_content=os.getenv("TAVILY_INCLUDE_RAW_CONTENT", "true").lower() == "true",
    include_images=os.getenv("TAVILY_INCLUDE_IMAGES", "true").lower() == "true",
    include_image_descriptions=True,
)

# 同时修改返回以包含 raw_content
search_response = [
    {
        "href": obj["url"],
        "body": obj.get("raw_content") or obj["content"],  # 优先使用 raw_content
        "title": obj.get("title", ""),
        "images": obj.get("images", []),
    }
    for obj in sources
]
```

### 4.2 新混合抓取器实现

```python
# gpt_researcher/skills/hybrid_content_fetcher.py

"""
用于高质量文本和图片的混合内容获取器。
结合 Tavily Advanced 搜索与选择性回退抓取。
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContentResult:
    """结构化内容结果。"""
    url: str
    content: str
    title: str
    images: List[Dict[str, Any]]
    source: str  # 'tavily_raw', 'browser_scrape', 'tavily_extract'
    quality_score: float


@dataclass
class ImageResult:
    """结构化图片结果。"""
    url: str
    description: str
    source: str  # 'tavily_search', 'page_embedded'
    score: float


class HybridContentFetcher:
    """
    使用混合方法获取高质量内容和图片：
    1. Tavily Advanced 获取 raw_content + 搜索图片
    2. 对 JS 页面或缺失内容选择性使用浏览器抓取
    3. 从多个来源智能聚合图片
    """

    def __init__(self, researcher):
        self.researcher = researcher
        self.cfg = researcher.cfg
        self.min_content_length = 500
        self.max_images = 15

        # 图片集合
        self.tavily_images: List[ImageResult] = []
        self.page_images: List[ImageResult] = []

    async def fetch(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        混合内容获取的主入口点。

        参数:
            query: 搜索查询
            max_results: 最大结果数

        返回:
            包含内容和图片的字典
        """
        # 阶段 1: Tavily Advanced 搜索
        search_results = await self._tavily_advanced_search(query, max_results)

        # 收集 Tavily 搜索图片
        self._collect_tavily_images(search_results.get('images', []))

        # 阶段 2: 处理每个结果
        contents = await self._process_search_results(search_results['results'])

        # 阶段 3: 聚合和去重图片
        all_images = self._aggregate_images()

        return {
            'contents': contents,
            'images': all_images,
            'metadata': {
                'total_contents': len(contents),
                'tavily_images_count': len(self.tavily_images),
                'page_images_count': len(self.page_images),
                'final_images_count': len(all_images),
            }
        }

    async def _tavily_advanced_search(
        self,
        query: str,
        max_results: int
    ) -> Dict[str, Any]:
        """执行 Tavily Advanced 搜索。"""
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

            return client.search(
                query=query,
                search_depth="advanced",
                include_raw_content=True,
                include_images=True,
                include_image_descriptions=True,
                max_results=max_results,
            )
        except Exception as e:
            logger.error(f"Tavily 搜索失败: {e}")
            return {'results': [], 'images': []}

    async def _process_search_results(
        self,
        results: List[Dict]
    ) -> List[ContentResult]:
        """处理搜索结果，必要时使用回退抓取。"""
        contents = []

        for result in results:
            url = result.get('url', '')
            raw_content = result.get('raw_content', '')

            # 检查 raw_content 是否充足
            if raw_content and len(raw_content) >= self.min_content_length:
                # 直接使用 Tavily raw_content
                contents.append(ContentResult(
                    url=url,
                    content=raw_content,
                    title=result.get('title', ''),
                    images=[],
                    source='tavily_raw',
                    quality_score=0.9
                ))
                logger.info(f"使用 Tavily raw_content: {url}")
            else:
                # 回退: 抓取页面
                scraped = await self._fallback_scrape(url)
                if scraped:
                    contents.append(scraped)
                    # 收集页面图片
                    for img in scraped.images:
                        self.page_images.append(ImageResult(
                            url=img.get('url', ''),
                            description=img.get('alt', ''),
                            source='page_embedded',
                            score=img.get('score', 1)
                        ))

        return contents

    async def _fallback_scrape(self, url: str) -> Optional[ContentResult]:
        """对没有 raw_content 的页面进行回退抓取。"""
        try:
            scraper_type = self.cfg.scraper

            if scraper_type == 'browser':
                from gpt_researcher.scraper import BrowserScraper
                scraper = BrowserScraper(url)
            elif scraper_type == 'nodriver':
                from gpt_researcher.scraper import NoDriverScraper
                scraper = NoDriverScraper(url)
            elif scraper_type == 'tavily_extract':
                from gpt_researcher.scraper import TavilyExtract
                scraper = TavilyExtract(url)
            else:
                from gpt_researcher.scraper import BeautifulSoupScraper
                scraper = BeautifulSoupScraper(url)

            if hasattr(scraper, 'scrape_async'):
                content, images, title = await scraper.scrape_async()
            else:
                content, images, title = await asyncio.get_running_loop().run_in_executor(
                    None, scraper.scrape
                )

            if content and len(content) >= 100:
                logger.info(f"回退抓取成功: {url}")
                return ContentResult(
                    url=url,
                    content=content,
                    title=title,
                    images=images,
                    source=f'{scraper_type}_scrape',
                    quality_score=0.7
                )
        except Exception as e:
            logger.error(f"回退抓取失败 {url}: {e}")

        return None

    def _collect_tavily_images(self, images: List) -> None:
        """从 Tavily 搜索结果收集图片。"""
        for img in images:
            if isinstance(img, str):
                self.tavily_images.append(ImageResult(
                    url=img,
                    description='',
                    source='tavily_search',
                    score=2.0
                ))
            elif isinstance(img, dict):
                self.tavily_images.append(ImageResult(
                    url=img.get('url', ''),
                    description=img.get('description', ''),
                    source='tavily_search',
                    score=2.0
                ))

    def _aggregate_images(self) -> List[Dict[str, Any]]:
        """从所有来源聚合和去重图片。"""
        seen_urls: Set[str] = set()
        aggregated: List[Dict[str, Any]] = []

        # 合并所有图片，优先页面图片
        all_images = self.page_images + self.tavily_images

        # 按分数排序（高优先）
        all_images.sort(key=lambda x: x.score, reverse=True)

        for img in all_images:
            if img.url and img.url not in seen_urls:
                seen_urls.add(img.url)
                aggregated.append({
                    'url': img.url,
                    'description': img.description,
                    'source': img.source,
                    'score': img.score,
                })

                if len(aggregated) >= self.max_images:
                    break

        return aggregated
```

---

## 5. 决策矩阵：何时使用何种工具

### 5.1 抓取器选择指南

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      抓取器决策树                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   目标站点是否为 JS 密集型（React/Vue/Angular）？                         │
│       │                                                                 │
│       ├─ 是 ──→ 是否有 API 预算？                                        │
│       │              │                                                  │
│       │              ├─ 是 ──→ 使用 Tavily Extract 或 FireCrawl         │
│       │              │          （最佳质量，可靠）                        │
│       │              │                                                  │
│       │              └─ 否 ───→ 使用 Browser 或 NoDriver                │
│       │                         （免费，但较慢）                          │
│       │                                                                 │
│       └─ 否 ───→ 站点是否有反爬虫保护？                                   │
│                      │                                                  │
│                      ├─ 是 ──→ 使用 NoDriver 或 Tavily Extract           │
│                      │          （隐蔽能力）                              │
│                      │                                                  │
│                      └─ 否 ───→ 内容质量是否关键？                        │
│                                     │                                   │
│                                     ├─ 是 ──→ 使用 Tavily Advanced       │
│                                     │          （包含 raw_content）       │
│                                     │                                   │
│                                     └─ 否 ───→ 使用 BeautifulSoup        │
│                                                （免费、快速、足够）        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 使用场景建议

| 使用场景 | 推荐配置 | 成本 | 备注 |
|----------|----------|------|------|
| **快速研究，简单站点** | Tavily Basic + BS | $ | 默认，适用于大多数博客 |
| **一般研究** | Tavily Advanced + Browser 回退 | $$ | 最佳平衡 |
| **学术研究** | Tavily Advanced + ArXiv 抓取器 | $$ | 论文特殊处理 |
| **新闻聚合** | Tavily Advanced (topic=news) | $$ | 新闻优化 |
| **电商研究** | Tavily Advanced + NoDriver | $$$ | 处理 JS 商城 |
| **技术文档** | Tavily Extract | $$$ | 干净提取 |
| **社交媒体内容** | Browser + 自定义认证 | $$ | 可能需要登录 |
| **最高质量** | Tavily Advanced + FireCrawl | $$$$ | 最佳可能质量 |

### 5.3 图片来源选择

| 场景 | 图片来源 | 配置 |
|------|----------|------|
| **通用插图** | Tavily 搜索图片 | `include_images=true` |
| **文章图表/图形** | 页面 `<img>` 抓取 | `SCRAPER=browser` |
| **两者都要** | 混合（推荐） | Advanced + Browser |
| **不需要图片** | 禁用 | `include_images=false` |

---

## 6. 成本分析

### 6.1 Tavily 积分成本

| 操作 | 积分 | 备注 |
|------|------|------|
| Search Basic | 1 | 仅摘要 |
| Search Advanced | 2 | 包含 raw_content |
| Extract | 每 5 个 URL 1 积分 | 专用提取 |
| 包含图片 | +0 | 搜索免费附带 |

### 6.2 各层级成本对比

假设每次研究 5 个子查询，每个查询 10 个 URL：

| 层级 | 搜索 | 抓取 | 总计/研究 | 每月（100 次研究）|
|------|------|------|-----------|-------------------|
| **预算** | 5×1 = 5 | 免费 (BS) | 约 5 积分 | 500 积分 |
| **平衡** | 5×2 = 10 | 选择性 | 约 12 积分 | 1,200 积分 |
| **最高** | 5×2 = 10 | 50/5 = 10 | 约 20 积分 | 2,000 积分 |

### 6.3 质量与成本权衡

```
质量 ▲
     │
 ⭐⭐⭐⭐⭐ │                              ● 最高质量 (FireCrawl)
     │                         ●
 ⭐⭐⭐⭐ │               ● 平衡模式（推荐）
     │          ●
 ⭐⭐⭐ │    ● 预算模式（当前默认）
     │
 ⭐⭐ │
     │
     └────────────────────────────────────────► 成本
           $      $$      $$$      $$$$
```

---

## 7. 总结与建议

### 对于大多数用户（平衡模式）

```bash
# .env
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=browser
```

**优势：**
- 来自 Tavily raw_content 的高质量文本
- 来自 Tavily 的搜索相关图片
- 来自浏览器抓取的页面嵌入图片
- 通过浏览器回退处理 JS 页面
- 合理成本（约 2 积分/查询）

### 对于预算敏感用户

保持当前默认，但考虑：
- 升级到 `SCRAPER=nodriver` 以获得更好的 JS 处理（仍然免费）
- 对重要研究任务使用 `SCRAPER=browser`

### 对于最高质量需求

```bash
# .env
RETRIEVER=tavily
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_RAW_CONTENT=true
TAVILY_INCLUDE_IMAGES=true
SCRAPER=firecrawl
FIRECRAWL_API_KEY=your_key
```

---

## 参考资料

- [Tavily Search API 文档](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [Tavily Extract API 文档](https://docs.tavily.com/documentation/api-reference/endpoint/extract)
- [FireCrawl 文档](https://docs.firecrawl.dev/)
- [Tavily Search vs Extract API](https://medium.com/@sofia_51582/tavilys-search-vs-extract-apis-and-when-to-use-each-67cc70edd610)
- [Basic vs Advanced 搜索](https://help.tavily.com/articles/6938147944-basic-vs-advanced-search-what-s-the-difference)
