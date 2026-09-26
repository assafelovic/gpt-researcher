# -*- coding: utf-8 -*-
# Copyright (c) 2026 Shanlun. MIT License.
"""
SmartPruner — Map-Expand two-pass web content pruner (stdlib-only).

Inspired by the DOM-pruning approach explored in gpt-researcher PR #2099;
this backend adds three pieces on top to close the quality gap left by
aggressive pruning, at ~5% extra tokens:
    1. Content Map   : a tiny per-section map (title + BM25 key sentence)
                       so the model knows "what else is on the page";
    2. Expand store  : pruned sections are kept in a local store and can
                       be expanded on demand (pay per expanded section);
    3. Coverage guard: when BM25 coverage drops below a threshold, the
                       top candidate section is auto-expanded instead of
                       silently losing the answer.

管线：HTML → DOM AST 去噪 → 结构化分节 → BM25 查询感知裁剪
      → 主上下文(top-k节+地图) + 旁路索引(全节) + 质量守卫
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable

# ---------------------------------------------------------------------------
# token 估算（可替换为真实 tokenizer；~4 字符/token 的启发式，中英混排皆可）
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """粗略 token 估算：CJK 按 1 字≈1 token，其他按 4 字符≈1 token。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if unicodedata.east_asian_width(ch) in ("W", "F"))
    other = len(text) - cjk
    return cjk + math.ceil(other / 4)


# ---------------------------------------------------------------------------
# 1) DOM AST 解析 + 噪声去除（HTMLParser，结构级而非正则）
# ---------------------------------------------------------------------------

_NOISE_TAGS = {"script", "style", "noscript", "svg", "iframe", "form",
               "nav", "footer", "aside", "template", "button"}
# 启发式噪声 class/id 关键词（广告/导航/页脚特征）
_NOISE_HINTS = ("nav", "menu", "sidebar", "footer", "advert",
                "banner", "cookie", "breadcrumb", "pagination", "comment",
                "social", "share", "related", "promo", "sponsor", "signup")
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
_BLOCK_TAGS = {"p", "li", "tr", "pre", "blockquote", "dt", "dd", "figcaption",
               "td", "th", "div", "section", "article"}
# void 元素无闭合标签，永不入跳过栈（否则一次命中即吞掉整页）
_VOID_TAGS = {"img", "br", "hr", "input", "meta", "link", "source", "area",
              "base", "col", "embed", "track", "wbr", "param"}
# 结构性标签永不判噪（真实案例：Wikipedia <html> 的功能开关 class 含
# "…-in-header-enabled"，"header" 子串命中即从根吞掉整页——2026-09-27 实测）
_STRUCTURAL_TAGS = {"html", "body"}
_SKIP_BAILOUT_CHARS = 100_000   # 单个噪声区吞掉超此字符数 → 强制放弃跳过（防坏 HTML 全灭）


@dataclass
class Block:
    """最小内容单元：一行文本 / 一段代码 / 一张表格。"""
    kind: str          # "text" | "code" | "table"
    text: str
    in_code: bool = False


class _DOMParser(HTMLParser):
    """把 HTML 解析为 Block 流，同时剥离噪声节点。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        # 噪声区栈：每项 [tag, pending]；pending=该区内已打开、未闭合的嵌套元素数。
        # 区闭合判定：endtag 到达且 pending==0 → 该 endtag 就是本区闭合标签。
        self._skip_stack: list[list] = []
        self._pre_depth = 0           # 处于 <pre>/<code> 内的深度
        self._table_depth = 0
        self._buf: list[str] = []
        self._code_buf: list[str] = []
        self._skip_chars = 0          # 当前噪声区累计吞掉字符数（bail-out 用）

    # -- 工具 --
    @staticmethod
    def _is_noisy(attrs: dict) -> bool:
        sig = " ".join(attrs.get(k, "") for k in ("class", "id", "role", "aria-label")).lower()
        return any(h in sig for h in _NOISE_HINTS)

    def _flush_text(self) -> None:
        text = re.sub(r"\s+", " ", " ".join(self._buf)).strip()
        self._buf = []
        if text and not self._skip_stack:
            kind = "table" if self._table_depth else "text"
            self.blocks.append(Block(kind=kind, text=text))

    # -- 事件 --
    def handle_starttag(self, tag, attrs):
        if tag in _VOID_TAGS:
            return                      # void 元素无闭合，永不参与跳过/缓冲
        if not self._skip_stack:
            ad = dict(attrs)
            if tag not in _STRUCTURAL_TAGS and (tag in _NOISE_TAGS or self._is_noisy(ad)):
                self._flush_text()
                self._skip_stack.append([tag, 0])
                self._skip_chars = 0
                return
        else:
            # 跳过区内：非 void 嵌套元素计入 pending；同时更新 bail-out 字符数
            self._skip_stack[-1][1] += 1
            if tag in _NOISE_TAGS or self._is_noisy(dict(attrs)):
                # 嵌套噪声区独立入栈（其闭合标签由它自己的 pending 消化）
                self._skip_stack.append([tag, 0])
            self._skip_chars += len(str(attrs))
            return
        if tag == "pre":
            self._flush_text()
            self._pre_depth += 1
        elif tag == "code" and not self._pre_depth:
            # 行内代码不单独成块，随文本保留
            pass
        elif tag == "code":
            self._pre_depth += 1
        elif tag == "table":
            self._flush_text()
            self._table_depth += 1
        elif tag in _BLOCK_TAGS or tag in _HEADINGS:
            self._flush_text()

    def handle_endtag(self, tag):
        if self._skip_stack:
            top = self._skip_stack[-1]
            if top[1] > 0:
                top[1] -= 1             # 还有未闭合的嵌套元素，该 endtag 属于它们
            else:
                self._skip_stack.pop()  # pending==0 → 这就是本噪声区的闭合标签
                if self._skip_stack:
                    self._skip_stack[-1][1] -= 1   # 内层区闭合，外层 pending 相应减一
            # bail-out：单个噪声区吞掉过多字符（坏 HTML/误判），放弃跳过保住内容
            if self._skip_chars > _SKIP_BAILOUT_CHARS:
                self._skip_stack.clear()
                self._skip_chars = 0
            return
        if tag == "pre":
            self._flush_code()
        elif tag == "code" and self._pre_depth:
            self._flush_code()
        elif tag == "table":
            self._flush_text()
            self._table_depth = max(0, self._table_depth - 1)
        elif tag in _BLOCK_TAGS or tag in _HEADINGS:
            self._flush_text()

    def handle_data(self, data):
        if self._skip_stack:
            self._skip_chars += len(data)
            return
        if self._pre_depth:
            self._code_buf.append(data)
        else:
            self._buf.append(data)

    def _flush_code(self) -> None:
        text = "\n".join(line.rstrip() for line in
                         "".join(self._code_buf).strip().splitlines())
        self._code_buf = []
        self._pre_depth = max(0, self._pre_depth - 1)
        if text and not self._skip_stack:
            self.blocks.append(Block(kind="code", text=text, in_code=True))


# ---------------------------------------------------------------------------
# 2) 结构化分节：按标题切，把 Block 归到节
#    （解析器在 _DOMParser 基础上把 h1-h6 文本标记为 headN 块）

@dataclass
class Section:
    sec_id: str
    title: str            # 所属标题（含文档主标题回填）
    level: int
    blocks: list[Block] = field(default_factory=list)

    @property
    def text(self) -> str:
        parts = []
        for b in self.blocks:
            if b.kind == "code":
                parts.append("```\n" + b.text + "\n```")
            else:
                parts.append(b.text)
        return "\n\n".join(parts)

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.text)


class _SectionParser(_DOMParser):
    """在 _DOMParser 基础上，把 h1-h6 文本行标记为标题块。"""

    def handle_starttag(self, tag, attrs):
        if tag in _HEADINGS and not self._skip_stack:
            self._flush_text()
            self._heading_tag = tag
            self._heading_buf: list[str] = []
            return
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in _HEADINGS and not self._skip_stack:
            text = re.sub(r"\s+", " ", " ".join(getattr(self, "_heading_buf", []))).strip()
            if text:
                lvl = _HEADINGS[tag]
                self.blocks.append(Block(kind=f"head{lvl}", text=text))
            self._heading_tag = None
            return
        super().handle_endtag(tag)

    def handle_data(self, data):
        if getattr(self, "_heading_tag", None) and not self._skip_stack:
            self._heading_buf.append(data)
            return
        super().handle_data(data)


def parse_sections_v2(html: str, doc_title: str = "") -> list[Section]:
    parser = _SectionParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as e:
        # 容错：坏 HTML 也尽量榨出已解析的块；但解析器自身 bug 必须暴露，静默吞掉会掩盖错误
        import sys
        print(f"[SmartPruner] parse warning: {e!r}", file=sys.stderr)
    parser._flush_text()

    sections: list[Section] = []
    counter = 0
    cur_title = doc_title or "(intro)"
    cur_level = 1

    def new_section() -> Section:
        nonlocal counter
        counter += 1
        return Section(sec_id=f"S{counter:03d}", title=cur_title, level=cur_level)

    sec = new_section()
    sections.append(sec)
    for b in parser.blocks:
        if b.kind.startswith("head"):
            cur_title = b.text
            cur_level = int(b.kind[4])
            sec = new_section()
            sections.append(sec)
        else:
            sec.blocks.append(b)
    # 清理空节（无内容且非首节）
    return [s for s in sections if s.blocks or s is sections[0]]


# ---------------------------------------------------------------------------
# 3) BM25 查询感知打分（纯 Python 实现，无依赖）
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", re.UNICODE)
_STOP = {"the", "a", "an", "of", "to", "in", "is", "are", "and", "or", "for",
         "on", "with", "as", "by", "at", "from", "this", "that", "it", "be",
         "can", "will", "how", "what", "when", "do", "does", "use", "using"}


def tokenize(text: str) -> list[str]:
    toks = [t.lower() for t in _TOKEN_RE.findall(text)]
    return [t for t in toks if t not in _STOP and len(t) > 1] or toks


class BM25:
    """Okapi BM25 (k1=1.5, b=0.75)。"""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.N = max(len(docs), 1)
        self.avgdl = sum(len(d) for d in docs) / self.N
        self.docs = docs
        self.tf = [{} for _ in docs]
        self.df: dict[str, int] = {}
        for i, d in enumerate(docs):
            for t in d:
                self.tf[i][t] = self.tf[i].get(t, 0) + 1
            for t in set(d):
                self.df[t] = self.df.get(t, 0) + 1

    def score(self, q_tokens: list[str], i: int) -> float:
        s = 0.0
        dl = len(self.docs[i]) or 1
        for t in q_tokens:
            f = self.tf[i].get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (self.N - self.df.get(t, 0) + 0.5) /
                           (self.df.get(t, 0) + 0.5))
            s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s


# ---------------------------------------------------------------------------
# 4) SmartPruner 主类：裁剪 + 内容地图 + 展开索引 + 覆盖率守卫
# ---------------------------------------------------------------------------

@dataclass
class ContentMapEntry:
    """内容地图条目：节标题 + 该节与查询最相关的 1 句话。"""
    sec_id: str
    title: str
    tokens: int
    hint: str            # 关键句（截断至 ~160 字符）


@dataclass
class PruneResult:
    context: str               # 送入主 LLM 的文本（选中节 + 内容地图）
    selected: list[str]        # 选中节 id
    context_tokens: int
    raw_tokens: int
    reduction: float           # 压缩率 0~1
    map_entries: list[ContentMapEntry]
    coverage: float            # BM25 覆盖分（0~1），< 阈值判 degraded
    degraded: bool
    auto_expanded: list[str]   # 守卫自动展开的节 id
    final_tokens: int          # 主上下文 + 自动展开后的实际 token
    warnings: list[str] = field(default_factory=list)


class ExpansionStore:
    """旁路索引：保存全部节，供按需展开（函数调用模式）。"""

    def __init__(self, sections: list[Section]):
        self._sections = {s.sec_id: s for s in sections}

    def expand(self, sec_id: str) -> str:
        sec = self._sections.get(sec_id)
        if sec is None:
            return f"[expand error] 未知节 {sec_id}"
        return f"### {sec.title}\n\n{sec.text}"

    def list_ids(self) -> list[str]:
        return sorted(self._sections)

    def section(self, sec_id: str) -> Section | None:
        return self._sections.get(sec_id)


class SmartPruner:
    """Map-Expand 两段式裁剪器。

    用法::

        pruner = SmartPruner(budget_tokens=1500)
        res = pruner.prune(html, query="how to run a coroutine")
        store = pruner.store                 # 挂到 LLM 的 expand() 工具上
        print(res.context)
    """

    def __init__(self, budget_tokens: int = 1500,
                 coverage_threshold: float = 0.70,
                 auto_expand_top: int = 1):
        self.budget = budget_tokens
        self.coverage_threshold = coverage_threshold
        self.auto_expand_top = auto_expand_top
        self.store: ExpansionStore | None = None

    # -- 主流程 --
    def prune(self, html: str, query: str, doc_title: str = "",
              with_map: bool = True) -> PruneResult:
        """with_map=False 时退化为纯裁剪（对标 DomPruner 基线：无地图、无守卫展开）。"""
        sections = parse_sections_v2(html, doc_title)
        self.store = ExpansionStore(sections)
        raw_tokens = sum(s.tokens for s in sections) or 1

        q = tokenize(query)
        docs = [tokenize(s.title + " " + s.text) for s in sections]
        bm25 = BM25(docs)
        scores = [bm25.score(q, i) for i in range(len(sections))]

        # 选节：贪心装入预算（保序拼接），代码块整块保留不腰斩
        warnings: list[str] = []
        order = sorted(range(len(sections)), key=lambda i: -scores[i])
        chosen: list[int] = []
        used = 0
        for i in order:
            t = sections[i].tokens
            if used + t <= self.budget:
                chosen.append(i)
                used += t
        # 保底：一个都装不下 → 截取最高分节头部到预算内（真正截断，不整节塞入）
        if not chosen and sections:
            i = order[0]
            s = sections[i]
            # 按预算裁字符（latin ≈4 字符/token，保守取 3.5 防止溢出）
            max_chars = max(int(self.budget * 3.5), 40)
            head = s.text[:max_chars].rsplit(" ", 1)[0]
            sections[i] = Section(sec_id=s.sec_id, title=s.title, level=s.level,
                                  blocks=[Block(kind="text", text=head + " …[截断]")])
            chosen = [i]
            used = min(s.tokens, self.budget)
            warnings.append(f"预算过小，仅截取最高分节 {s.sec_id} 头部")

        selected_ids = [sections[i].sec_id for i in chosen]

        # 归一化覆盖分 = 查询词召回率：查询 token 有多少比例被选中节覆盖
        # （可解释、可校准：1.0=查询词全部命中选中内容，0=完全没摸到）
        qset = set(q)
        sel_tokens: set[str] = set()
        for i in chosen:
            sel_tokens |= set(docs[i])
        coverage = (len(qset & sel_tokens) / max(len(qset), 1)) if qset else 1.0

        if not with_map:
            # 纯裁剪基线：只拼选中节，无地图无守卫
            parts = [f"# {doc_title or 'PAGE'}（已裁剪）"]
            for i in sorted(chosen):
                s = sections[i]
                parts.append(f"### {s.sec_id} {s.title}\n\n{s.text}")
            context = "\n\n".join(parts)
            ctx_tok = estimate_tokens(context)
            return PruneResult(
                context=context, selected=selected_ids,
                context_tokens=ctx_tok, raw_tokens=raw_tokens,
                reduction=1 - ctx_tok / raw_tokens,
                map_entries=[], coverage=coverage,
                degraded=False, auto_expanded=[],
                final_tokens=ctx_tok, warnings=warnings)

        # 内容地图：全部节的 标题+token数+关键句（这是消除盲区的关键，~5% 开销）
        map_entries = self._build_map(sections, scores, q)
        map_tokens = sum(estimate_tokens(f"- {e.sec_id} {e.title} ({e.tokens}tok): {e.hint}")
                         for e in map_entries)

        # 覆盖率守卫：覆盖分过低 → 自动展开最高分的未选中节
        auto_expanded: list[str] = []
        expanded_tokens = 0
        if coverage < self.coverage_threshold:
            warnings.append(f"覆盖率 {coverage:.2f} < {self.coverage_threshold}，"
                            "守卫触发：自动展开未选中节")
            for i in order:
                sid = sections[i].sec_id
                if sid in selected_ids or len(auto_expanded) >= self.auto_expand_top:
                    continue
                auto_expanded.append(sid)
                expanded_tokens += sections[i].tokens
                if used + expanded_tokens > self.budget * 1.25:   # 守卫预算上限 1.25x
                    break

        # 拼装主上下文
        parts = [f"# {doc_title or 'PAGE'}（已裁剪：{len(sections)} 节中选中 {len(selected_ids)} 节）"]
        for i in sorted(chosen):
            s = sections[i]
            parts.append(f"### {s.sec_id} {s.title}\n\n{s.text}")
        if auto_expanded:
            parts.append("## [守卫自动展开]")
            for sid in auto_expanded:
                s = self.store.section(sid)
                parts.append(f"### {s.sec_id} {s.title}\n\n{s.text}")
        parts.append("## 内容地图（其余未展开节：可调用 expand(sec_id) 获取全文）")
        for e in map_entries:
            mark = " [已含]" if e.sec_id in selected_ids + auto_expanded else ""
            hint = f": {e.hint}" if e.hint else ""
            parts.append(f"- {e.sec_id} {e.title}{mark} ({e.tokens}tok){hint}")

        context = "\n\n".join(parts)
        context_tokens = estimate_tokens(context)
        return PruneResult(
            context=context,
            selected=selected_ids,
            context_tokens=context_tokens,
            raw_tokens=raw_tokens,
            reduction=1 - context_tokens / raw_tokens,
            map_entries=map_entries,
            coverage=coverage,
            degraded=coverage < self.coverage_threshold,
            auto_expanded=auto_expanded,
            final_tokens=context_tokens,
            warnings=warnings,
        )

    # -- 内容地图构造 --
    def _build_map(self, sections: list[Section], scores: list[float],
                   q: list[str], hint_top: int = 4) -> list[ContentMapEntry]:
        """只给 top-N 高分节配关键句 hint，其余节只留标题+token 数（控制地图开销）。"""
        top_idx = set(sorted(range(len(sections)), key=lambda i: -scores[i])[:hint_top])
        entries = []
        for i, s in enumerate(sections):
            hint = self._key_sentence(s, q) if i in top_idx else ""
            entries.append(ContentMapEntry(
                sec_id=s.sec_id, title=s.title, tokens=s.tokens, hint=hint))
        return entries

    @staticmethod
    def _key_sentence(sec: Section, q: list[str]) -> str:
        """取该节中与查询词重叠最多的一句（无重叠则取首句），截 ~90 字符。"""
        text = re.split(r"(?<=[.!?。！？])\s+", sec.text.replace("\n", " "))
        best, best_overlap = "", -1
        qset = set(q)
        for sent in text:
            overlap = len(qset & set(tokenize(sent)))
            if overlap > best_overlap:
                best, best_overlap = sent, overlap
        if not best and text:
            best = text[0]
        return (best[:87] + "...") if len(best) > 90 else best


# ---------------------------------------------------------------------------
# CLI 快速自测
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_html = """
    <html><head><title>asyncio — Asynchronous I/O</title></head>
    <body>
    <nav class="main-nav"><a>Docs</a><a>Tutorial</a><a>GitHub</a></nav>
    <div class="breadcrumb">Home > Library > asyncio</div>
    <h1>asyncio — Asynchronous I/O</h1>
    <p>asyncio is a library to write concurrent code using the async/await syntax.</p>
    <h2>Coroutines and Tasks</h2>
    <p>Coroutines declared with async/await syntax is the preferred way of writing
    asyncio applications. To run a coroutine, call asyncio.run(main()).</p>
    <pre><code>import asyncio

    async def main():
        await asyncio.sleep(1)
        print("hello")

    asyncio.run(main())</code></pre>
    <p>The asyncio.create_task() function schedules a coroutine to run soon.</p>
    <h2>Event Loop</h2>
    <p>The event loop is the core of every asyncio application. Event loops run
    asynchronous tasks and callbacks, perform network IO operations.</p>
    <aside class="promo">Subscribe to our newsletter!</aside>
    <footer>© 2026 Example Docs. All rights reserved.</footer>
    </body></html>
    """
    p = SmartPruner(budget_tokens=180)
    r = p.prune(demo_html, "how to run a coroutine with asyncio.run", "asyncio docs")
    print(f"raw={r.raw_tokens} tok -> ctx={r.context_tokens} tok "
          f"(reduction {r.reduction:.1%}), coverage={r.coverage:.2f}")
    print("selected:", r.selected, "| map entries:", len(r.map_entries))
    print("-" * 60)
    print(r.context)
