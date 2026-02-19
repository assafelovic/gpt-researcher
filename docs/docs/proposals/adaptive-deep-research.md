# RFC: 自适应深度研究 - 质量驱动的递归搜索

> **状态**: 提案
> **作者**: 社区贡献者
> **创建日期**: 2026-01-30
> **目标版本**: v4.x

## 概述

本提案引入**自适应深度研究**模式，使用基于 LLM 的质量评估来动态确定搜索深度，替代当前固定深度的递归方法。

## 动机

### 当前设计的局限性

现有的深度研究实现使用固定深度的递归策略：

```python
# 当前方法
depth = 2  # 固定值
breadth = 4

# 无论查询复杂度如何，始终执行恰好 2 轮研究
```

**这种方法的问题：**

| 问题 | 描述 |
|------|------|
| **资源浪费** | 简单查询仍然消耗完整的 2 轮研究 |
| **深度不足** | 复杂查询可能需要超过 2 轮 |
| **无质量保证** | 研究基于计数而非质量停止 |
| **不灵活** | 一刀切的方式不适合多样化的研究需求 |

### 提议的解决方案

实现**质量驱动的自适应循环**，让 LLM 评估器在每轮后评估研究质量，并决定是否继续或停止。

```
┌─────────────────────────────────────────────────────────────────┐
│                   当前设计 vs 提议设计                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  当前（固定深度）：                                              │
│  ────────────────                                               │
│  搜索 → 搜索 → 停止（始终 2 轮）                                 │
│                                                                 │
│  提议（自适应）：                                                │
│  ──────────────                                                 │
│  搜索 → 评估 → [质量达标?] → 是 → 停止                          │
│                    │                                            │
│                    └─→ 否 → 搜索 → 评估 → ...                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 详细设计

### 1. 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    自适应深度研究流程                             │
└─────────────────────────────────────────────────────────────────┘

                         用户查询
                            │
                            ▼
                   ┌────────────────┐
                   │   研究轮次      │
                   │ (conduct_research)
                   └────────┬───────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  质量评估器     │  ← LLM 评估节点
                   │ (assess_quality)│
                   └────────┬───────┘
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
    ┌────────────────┐           ┌────────────────┐
    │  分数 >= 7/10  │           │   分数 < 7/10  │
    │  或达到最大深度 │           │   且存在知识空白│
    └────────┬───────┘           └────────┬───────┘
             │                             │
             ▼                             ▼
    ┌────────────────┐           ┌────────────────┐
    │   生成         │           │  根据知识空白   │
    │   最终报告     │           │  构建下一轮查询 │
    │                │           │                │
    └────────────────┘           └────────┬───────┘
                                          │
                                          └──→ (循环回到研究)
```

### 2. 核心组件

#### 2.1 AdaptiveDeepResearchSkill 类

```python
# gpt_researcher/skills/adaptive_deep_research.py

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import asyncio
import json

from gpt_researcher.llm_provider import create_chat_completion
from gpt_researcher.config import Config


@dataclass
class QualityAssessment:
    """来自评估 LLM 的质量评估结果"""
    score: float                      # 总体分数 (1-10)
    dimensions: Dict[str, float]      # 各维度分数
    reasoning: str                    # 评分解释
    has_knowledge_gaps: bool          # 是否存在知识空白
    knowledge_gaps: List[str]         # 识别出的知识空白列表
    suggested_directions: List[str]   # 建议的研究方向


@dataclass
class AdaptiveResearchProgress:
    """自适应研究的进度跟踪"""
    current_depth: int
    quality_score: float
    total_queries: int
    knowledge_gaps_remaining: int
    status: str  # "researching", "evaluating", "completed"


class AdaptiveDeepResearchSkill:
    """
    自适应深度研究技能

    使用基于 LLM 的质量评估来动态确定何时停止研究，
    确保质量优先于任意深度。
    """

    def __init__(self, researcher):
        self.researcher = researcher
        self.cfg: Config = researcher.cfg

        # 自适应参数
        self.min_depth = 1                    # 最小研究轮次
        self.max_depth = 5                    # 最大轮次（安全限制）
        self.quality_threshold = 7.0          # 目标质量分数 (1-10)
        self.breadth = 4                      # 每轮查询数
        self.concurrency_limit = 2            # 并行查询限制

        # 累积数据
        self.learnings: List[str] = []
        self.context: List[str] = []
        self.citations: Dict[str, str] = {}
        self.visited_urls: Set[str] = set()

        # 进度跟踪
        self.current_depth = 0
        self.quality_history: List[QualityAssessment] = []

    async def run(
        self,
        query: str,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        自适应深度研究的主入口点。

        参数:
            query: 研究问题
            on_progress: 可选的进度回调函数

        返回:
            包含研究结果、学习成果和元数据的字典
        """
        self.original_query = query

        return await self._adaptive_research_loop(
            query=query,
            on_progress=on_progress
        )

    async def _adaptive_research_loop(
        self,
        query: str,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        核心自适应研究循环，带有质量驱动的终止条件。
        """

        while self.current_depth < self.max_depth:
            self.current_depth += 1

            # ═══════════════════════════════════════════════════════
            # 步骤 1: 执行研究轮次
            # ═══════════════════════════════════════════════════════
            if on_progress:
                on_progress(AdaptiveResearchProgress(
                    current_depth=self.current_depth,
                    quality_score=self._get_latest_score(),
                    total_queries=len(self.learnings),
                    knowledge_gaps_remaining=self._count_gaps(),
                    status="researching"
                ))

            round_results = await self._conduct_research_round(query)

            # 累积结果
            self.learnings.extend(round_results['learnings'])
            self.context.append(round_results['context'])
            self.citations.update(round_results.get('citations', {}))

            # ═══════════════════════════════════════════════════════
            # 步骤 2: 质量评估
            # ═══════════════════════════════════════════════════════
            if on_progress:
                on_progress(AdaptiveResearchProgress(
                    current_depth=self.current_depth,
                    quality_score=self._get_latest_score(),
                    total_queries=len(self.learnings),
                    knowledge_gaps_remaining=self._count_gaps(),
                    status="evaluating"
                ))

            assessment = await self._assess_quality()
            self.quality_history.append(assessment)

            # 记录评估结果
            await self._log_assessment(assessment)

            # ═══════════════════════════════════════════════════════
            # 步骤 3: 决策 - 继续或停止
            # ═══════════════════════════════════════════════════════
            should_stop = self._should_stop_research(assessment)

            if should_stop:
                break

            # 根据知识空白构建下一轮查询
            query = self._build_next_query(assessment)

        # ═══════════════════════════════════════════════════════════
        # 最终: 返回累积结果
        # ═══════════════════════════════════════════════════════════
        if on_progress:
            on_progress(AdaptiveResearchProgress(
                current_depth=self.current_depth,
                quality_score=self._get_latest_score(),
                total_queries=len(self.learnings),
                knowledge_gaps_remaining=0,
                status="completed"
            ))

        return {
            'learnings': list(set(self.learnings)),
            'context': '\n\n'.join(self.context),
            'citations': self.citations,
            'visited_urls': self.visited_urls,
            'metadata': {
                'final_depth': self.current_depth,
                'final_quality_score': assessment.score,
                'quality_history': [
                    {'depth': i+1, 'score': a.score}
                    for i, a in enumerate(self.quality_history)
                ],
                'termination_reason': self._get_termination_reason(assessment)
            }
        }

    async def _conduct_research_round(self, query: str) -> Dict[str, Any]:
        """
        执行单轮研究，包含多个查询。
        """
        # 为本轮生成搜索查询
        search_queries = await self._generate_search_queries(query)

        # 使用并发限制执行查询
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_single_query(sq: Dict) -> Dict:
            async with semaphore:
                return await self._execute_single_research(sq)

        tasks = [process_single_query(sq) for sq in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 聚合结果
        all_learnings = []
        all_context = []
        all_citations = {}

        for result in results:
            if isinstance(result, Exception):
                continue
            all_learnings.extend(result.get('learnings', []))
            all_context.append(result.get('context', ''))
            all_citations.update(result.get('citations', {}))

        return {
            'learnings': all_learnings,
            'context': '\n\n'.join(all_context),
            'citations': all_citations
        }

    async def _assess_quality(self) -> QualityAssessment:
        """
        使用 LLM 评估当前研究质量。

        这是核心评估节点，决定研究是否足以回答用户问题。
        """

        assessment_prompt = f"""
你是一个研究质量评估员。评估当前的研究结果是否足以全面回答用户的问题。

## 原始问题
{self.original_query}

## 当前研究发现
{self._format_learnings_for_assessment()}

## 研究上下文摘要
{self._get_context_summary()}

## 评估维度

请从以下维度评估研究质量（1-10分）：

1. **完整性**: 是否涵盖了问题的所有关键方面？
2. **深度**: 每个方面的分析是否足够详细？
3. **可靠性**: 来源是否可信？是否有交叉验证？
4. **可操作性**: 是否提供了实用、可用的见解？

## 输出格式 (JSON)

{{
    "score": <总体分数_1到10>,
    "dimensions": {{
        "completeness": <分数>,
        "depth": <分数>,
        "reliability": <分数>,
        "actionability": <分数>
    }},
    "reasoning": "<评分的简要解释>",
    "has_knowledge_gaps": <true或false>,
    "knowledge_gaps": [
        "<具体知识空白_1>",
        "<具体知识空白_2>"
    ],
    "suggested_directions": [
        "<建议的研究方向_1>",
        "<建议的研究方向_2>"
    ]
}}

请保持批判和诚实。只有当研究真正全面解答了问题时才给高分。
"""

        response = await create_chat_completion(
            model=self.cfg.strategic_llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的研究质量评估员。只用有效的 JSON 格式回复。"
                },
                {"role": "user", "content": assessment_prompt}
            ],
            temperature=0.3,
            llm_provider=self.cfg.strategic_llm_provider,
            response_format={"type": "json_object"},
            # 如果可用则使用推理模型
            reasoning_effort="medium" if "o1" in self.cfg.strategic_llm_model or "o3" in self.cfg.strategic_llm_model else None,
        )

        try:
            data = json.loads(response)
            return QualityAssessment(
                score=float(data.get('score', 5)),
                dimensions=data.get('dimensions', {}),
                reasoning=data.get('reasoning', ''),
                has_knowledge_gaps=data.get('has_knowledge_gaps', True),
                knowledge_gaps=data.get('knowledge_gaps', []),
                suggested_directions=data.get('suggested_directions', [])
            )
        except (json.JSONDecodeError, KeyError) as e:
            # 回退评估
            return QualityAssessment(
                score=5.0,
                dimensions={},
                reasoning=f"评估解析失败: {e}",
                has_knowledge_gaps=True,
                knowledge_gaps=["无法解析评估结果"],
                suggested_directions=["继续通用研究"]
            )

    def _should_stop_research(self, assessment: QualityAssessment) -> bool:
        """
        根据评估结果决定是否停止研究。

        停止条件:
        1. 质量分数 >= 阈值
        2. 达到最大深度（安全限制）
        3. 没有更多知识空白可探索
        4. 质量不再提升（收益递减）
        """

        # 条件 1: 达到质量阈值
        if assessment.score >= self.quality_threshold:
            return True

        # 条件 2: 达到最大深度
        if self.current_depth >= self.max_depth:
            return True

        # 条件 3: 没有知识空白
        if not assessment.has_knowledge_gaps or not assessment.knowledge_gaps:
            return True

        # 条件 4: 收益递减
        if len(self.quality_history) >= 2:
            recent_scores = [a.score for a in self.quality_history[-2:]]
            if recent_scores[-1] - recent_scores[-2] < 0.5:
                # 提升不足 0.5，可能是收益递减
                # 但只有在达到最小深度后才停止
                if self.current_depth >= self.min_depth:
                    return True

        return False

    def _build_next_query(self, assessment: QualityAssessment) -> str:
        """
        根据识别出的知识空白构建下一轮研究查询。
        """
        gaps = assessment.knowledge_gaps[:3]  # 聚焦前 3 个知识空白
        directions = assessment.suggested_directions[:2]

        return f"""
原始问题: {self.original_query}

当前研究已识别出以下知识空白:
{chr(10).join(f'- {gap}' for gap in gaps)}

建议的研究方向:
{chr(10).join(f'- {d}' for d in directions)}

请进行针对性研究以填补这些具体的知识空白。
"""

    # ═══════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════

    def _format_learnings_for_assessment(self) -> str:
        """格式化学习成果用于评估提示。"""
        if not self.learnings:
            return "尚未收集到学习成果。"
        return '\n'.join(f'- {learning}' for learning in self.learnings[-20:])

    def _get_context_summary(self) -> str:
        """获取研究上下文摘要。"""
        full_context = '\n\n'.join(self.context)
        # 截断以避免 token 限制
        return full_context[:4000] + "..." if len(full_context) > 4000 else full_context

    def _get_latest_score(self) -> float:
        """获取最新的质量分数。"""
        if not self.quality_history:
            return 0.0
        return self.quality_history[-1].score

    def _count_gaps(self) -> int:
        """统计剩余知识空白数量。"""
        if not self.quality_history:
            return -1  # 未知
        return len(self.quality_history[-1].knowledge_gaps)

    def _get_termination_reason(self, assessment: QualityAssessment) -> str:
        """获取可读的终止原因。"""
        if assessment.score >= self.quality_threshold:
            return f"达到质量阈值（分数: {assessment.score:.1f}）"
        if self.current_depth >= self.max_depth:
            return f"达到最大深度（{self.max_depth}）"
        if not assessment.has_knowledge_gaps:
            return "没有剩余知识空白"
        return "检测到收益递减"

    async def _log_assessment(self, assessment: QualityAssessment):
        """记录评估结果。"""
        log_msg = (
            f"[深度 {self.current_depth}] "
            f"质量: {assessment.score:.1f}/10 | "
            f"空白: {len(assessment.knowledge_gaps)} | "
            f"原因: {assessment.reasoning[:100]}..."
        )
        # 使用 researcher 的日志机制
        if hasattr(self.researcher, 'websocket') and self.researcher.websocket:
            await self.researcher.websocket.send_json({
                "type": "logs",
                "content": "quality_assessment",
                "output": log_msg
            })
```

#### 2.2 质量评估提示设计

质量评估器使用多维度评估：

| 维度 | 权重 | 描述 |
|------|------|------|
| **完整性** | 25% | 对问题所有方面的覆盖程度 |
| **深度** | 25% | 分析的详细程度 |
| **可靠性** | 25% | 来源可信度和验证情况 |
| **可操作性** | 25% | 见解的实用价值 |

#### 2.3 配置选项

```python
# 环境变量或配置文件

# 自适应模式开关
DEEP_RESEARCH_MODE = "adaptive"  # "fixed" 或 "adaptive"

# 质量设置
ADAPTIVE_QUALITY_THRESHOLD = 7      # 停止所需分数 (1-10)
ADAPTIVE_MIN_DEPTH = 1              # 最小轮次
ADAPTIVE_MAX_DEPTH = 5              # 安全限制

# 成本优化
EVALUATOR_MODEL = "gpt-4o-mini"     # 使用较便宜的模型进行评估
RESEARCH_MODEL = "gpt-4o"           # 使用更强的模型进行研究

# 收益递减检测
MIN_IMPROVEMENT_THRESHOLD = 0.5     # 继续研究所需的最小分数提升
```

### 3. 集成点

#### 3.1 修改 GPTResearcher

```python
# gpt_researcher/agent.py

class GPTResearcher:
    async def conduct_research(self, on_progress=None):
        if self.report_type == "deep":
            if self.cfg.deep_research_mode == "adaptive":
                # 使用新的自适应技能
                skill = AdaptiveDeepResearchSkill(self)
                return await skill.run(self.query, on_progress)
            else:
                # 使用现有的固定深度技能
                skill = DeepResearchSkill(self)
                return await skill.run(on_progress)
```

#### 3.2 WebSocket 进度更新

```typescript
// 前端: 处理自适应进度更新
interface AdaptiveProgress {
  current_depth: number;
  quality_score: number;
  total_queries: number;
  knowledge_gaps_remaining: number;
  status: 'researching' | 'evaluating' | 'completed';
}

// 实时显示质量分数
function handleProgress(progress: AdaptiveProgress) {
  updateUI({
    depth: `第 ${progress.current_depth} 轮`,
    quality: `质量: ${progress.quality_score.toFixed(1)}/10`,
    status: progress.status,
    gaps: `剩余 ${progress.knowledge_gaps_remaining} 个知识空白`
  });
}
```

### 4. 执行流程示例

#### 4.1 简单查询（快速完成）

```
查询: "如何做炒鸡蛋？"

第 1 轮:
  ├─ 研究: 基础烹饪说明
  ├─ 质量评估: 8.5/10
  │   - 完整性: 9/10 ✓
  │   - 深度: 8/10 ✓
  │   - 可靠性: 9/10 ✓
  │   - 可操作性: 8/10 ✓
  └─ 决策: 停止（达到阈值）

总计: 1 轮, 约 30 秒
```

#### 4.2 复杂查询（深度探索）

```
查询: "量子计算对加密货币安全性的影响"

第 1 轮:
  ├─ 研究: 量子计算 + 加密货币概述
  ├─ 质量评估: 4.0/10
  │   - 空白: ["后量子密码学", "迁移时间表"]
  └─ 决策: 继续

第 2 轮:
  ├─ 研究: 后量子密码学算法
  ├─ 质量评估: 5.5/10
  │   - 空白: ["实施成本", "行业准备情况"]
  └─ 决策: 继续

第 3 轮:
  ├─ 研究: 行业采用和成本
  ├─ 质量评估: 7.2/10
  │   - 没有关键空白剩余
  └─ 决策: 停止（达到阈值）

总计: 3 轮, 约 3 分钟
```

### 5. 成本分析

| 场景 | 固定模式 (depth=2) | 自适应模式 | 节省 |
|------|-------------------|------------|------|
| 简单查询 | 12 次 API 调用 | 4-6 次调用 | ~50% |
| 中等查询 | 12 次 API 调用 | 8-12 次调用 | ~0-30% |
| 复杂查询 | 12 次 API 调用 | 15-20 次调用 | -30%（但质量更好） |

**注意**: 自适应模式每轮增加 1 次评估调用，但对于简单查询可节省多次研究调用。

## 实施计划

### 阶段 1: 核心实现（第 1-2 周）

- [ ] 创建 `AdaptiveDeepResearchSkill` 类
- [ ] 实现质量评估逻辑
- [ ] 添加配置选项
- [ ] 编写单元测试

### 阶段 2: 集成（第 3 周）

- [ ] 与 `GPTResearcher` 集成
- [ ] 添加 WebSocket 进度更新
- [ ] 更新前端以显示质量指标
- [ ] 添加 CLI 自适应模式支持

### 阶段 3: 测试与优化（第 4 周）

- [ ] 与固定深度模式进行基准测试
- [ ] 调优质量阈值和提示
- [ ] 添加成本跟踪和报告
- [ ] 编写文档

### 阶段 4: 发布（第 5 周）

- [ ] 代码审查
- [ ] 更新文档
- [ ] 作为可选功能发布
- [ ] 收集社区反馈

## 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 无限循环 | 高 | `max_depth` 安全限制 |
| 评估不一致 | 中 | 多维度评估，明确评分标准 |
| 复杂查询成本更高 | 低 | 成本跟踪，用户警告 |
| 评估延迟 | 低 | 使用更快的模型 (gpt-4o-mini) 进行评估 |

## 考虑过的替代方案

1. **基于置信度的停止**: 使用模型的置信度而非质量分数
   - 拒绝: 置信度不能衡量研究完整性

2. **用户定义深度**: 让用户为每个查询指定深度
   - 拒绝: 用户无法预测最优深度

3. **混合方法**: 固定最小值 + 自适应扩展
   - 部分采用: `min_depth` 确保基线覆盖

## 成功指标

- **效率**: 简单查询 API 调用减少 30%+
- **质量**: 保持或提高报告质量分数
- **用户满意度**: 对自适应行为的积极反馈
- **成本**: 平均每查询成本增加不超过 10%

## 参考资料

- [当前深度研究实现](../gpt-researcher/gptr/deep_research.md)
- [LangGraph 文档](https://python.langchain.com/docs/langgraph)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

## 附录: 完整代码清单

请参阅以下文件中的实现:
- `gpt_researcher/skills/adaptive_deep_research.py`
- `gpt_researcher/config/config.py`（新配置选项）
- `frontend/nextjs/components/AdaptiveProgress.tsx`
