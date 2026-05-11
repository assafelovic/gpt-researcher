import os
import re
import asyncio
from collections import Counter
from typing import List, Dict, Any
from ..config.config import Config
from ..utils.llm import create_chat_completion
from ..utils.logger import get_formatted_logger
from ..utils.language import is_german_language, normalize_german_technical_terms, strip_source_boilerplate
from ..prompts import PromptFamily, get_prompt_by_report_type
from ..utils.enum import Tone
from .verification import build_verification_bundle, render_verification_section
from .reasoning_critic import build_reasoning_critic_bundle, render_reasoning_critic_section

logger = get_formatted_logger()

_REPORT_PRELUDE_PATTERNS = (
    re.compile(r"^\$prelude\$\s*$", re.IGNORECASE),
    re.compile(r"^includes all source images\b", re.IGNORECASE),
    re.compile(r"^```(?:markdown)?\s*$", re.IGNORECASE),
)


def _normalize_context_text(context: Any) -> str:
    if context is None:
        return ""
    if isinstance(context, str):
        return strip_source_boilerplate(_strip_context_metadata(context))
    if isinstance(context, bytes):
        return strip_source_boilerplate(_strip_context_metadata(context.decode("utf-8", errors="ignore")))
    if isinstance(context, dict):
        for key in ("content", "text", "body", "summary"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return strip_source_boilerplate(_strip_context_metadata(value.strip()))
        return strip_source_boilerplate(
            _strip_context_metadata(
                " ".join(
                    str(value).strip()
                    for value in context.values()
                    if isinstance(value, str) and value.strip()
                )
            )
        )
    if isinstance(context, (list, tuple, set)):
        parts: list[str] = []
        for item in context:
            item_text = _normalize_context_text(item)
            if item_text:
                parts.append(item_text.strip())
        return strip_source_boilerplate(_strip_context_metadata("\n\n".join(parts)))
    return strip_source_boilerplate(_strip_context_metadata(str(context)))


def _strip_context_metadata(text: str) -> str:
    if not text:
        return ""

    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            lines.append("")
            continue

        cleaned = re.sub(r"(?i)\b(source|title|content)\s*:\s*", "", stripped)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned or cleaned.lower() in {"none", "null"}:
            continue
        lines.append(cleaned)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _extract_urls_from_text(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    urls: list[str] = []
    for match in re.findall(r"https?://[^\s)\]>,]+", text):
        url = match.rstrip(".,;:")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _render_reference_section(visited_urls: list[str] | None, context: str, language: str | None = None) -> str:
    urls: list[str] = []
    if visited_urls:
        urls.extend(visited_urls)
    urls.extend(_extract_urls_from_text(context))

    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            unique_urls.append(url)

    text = _report_language_text(language)
    if not unique_urls:
        return f"{text['references_missing']}\n{text['references_text']}"

    return f"{text['references_missing']}\n" + "\n".join(f"- [{url}]({url})" for url in unique_urls[:10])


def _is_report_noise_line(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", line).strip()
    if not normalized:
        return True
    lowered = normalized.lower()
    if "source images" in lowered and "videos" in lowered:
        return True
    if normalized.startswith("[http") or normalized.startswith("http://") or normalized.startswith("https://"):
        return len(normalized) > 80 or normalized.count("/") > 8
    return any(pattern.match(normalized) for pattern in _REPORT_PRELUDE_PATTERNS)


def _strip_report_prelude(report_markdown: str) -> str:
    lines = report_markdown.splitlines()
    stripped_lines: list[str] = []
    skipping_prelude = True

    for line in lines:
        if skipping_prelude:
            if _is_report_noise_line(line):
                continue
            skipping_prelude = False
        stripped_lines.append(line)

    return "\n".join(stripped_lines).strip()


def _ensure_report_heading(report_markdown: str, question: str) -> str:
    report_markdown = report_markdown.strip()
    if not report_markdown:
        return f"# {question}".strip()

    for line in report_markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#(?!#)\s*", stripped):
            return report_markdown
        break

    return f"# {question}\n\n{report_markdown}".strip()


def _strip_leading_noise_after_heading(report_markdown: str) -> str:
    lines = report_markdown.splitlines()
    if len(lines) <= 1:
        return report_markdown.strip()

    cleaned_lines = [lines[0]]
    index = 1

    while index < len(lines) and not lines[index].strip():
        index += 1

    while index < len(lines) and _is_report_noise_line(lines[index]):
        index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1

    cleaned_lines.extend(lines[index:])
    return "\n".join(cleaned_lines).strip()


def _looks_like_corrupt_body_line(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", line).strip()
    if not normalized:
        return True
    if _is_report_noise_line(normalized):
        return True

    lowered = normalized.lower()
    if len(normalized) > 200 and ("vibes" in lowered or "超" in normalized or normalized.count("/") > 8):
        return True

    tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", lowered)
    if len(tokens) >= 12:
        counts = Counter(tokens)
        most_common = counts.most_common(1)[0][1]
        if most_common / len(tokens) >= 0.35 and len(counts) <= len(tokens) / 2:
            return True

    if re.search(r"(.{3,12})\1{4,}", normalized):
        return True

    return False


def _report_needs_deterministic_fallback(report_markdown: str) -> bool:
    lines = [line.strip() for line in report_markdown.splitlines() if line.strip()]
    if not lines:
        return True

    if not re.match(r"^#(?!#)\s*", lines[0]):
        return True

    body_lines = lines[1:4]
    if body_lines and any(_looks_like_corrupt_body_line(line) for line in body_lines[:2]):
        return True

    if "##" not in report_markdown[:800]:
        return True

    return False


def _report_language_text(language: str | None) -> dict[str, str]:
    if is_german_language(language):
        return {
            "overview": "## Überblick",
            "key_findings": "## Zentrale Erkenntnisse",
            "caveats": "## Einschränkungen",
            "deterministic_summary": "- Dieser Bericht ist eine deterministische Synthese des live erfassten Recherchekontexts.",
            "missing_source": "- Wenn eine Quell-URL im Kontext fehlt, kann sie trotzdem in den Rechercheprotokollen erscheinen, aber nicht im extrahierten Text.",
            "no_context": "Der verfügbare Recherchekontext enthielt nicht genug strukturierten Text, um eine detaillierte Zusammenfassung zu erstellen.",
            "references_missing": "## Quellen",
            "references_text": "- Keine expliziten Quell-URLs wurden im Recherchekontext erhalten.",
            "title": "# {question}",
        }

    return {
        "overview": "## Overview",
        "key_findings": "## Key Findings",
        "caveats": "## Caveats",
        "deterministic_summary": "- This report is a deterministic synthesis of the live research context.",
        "missing_source": "- If a source URL is missing from the context, it may still appear in the research logs but not in the extracted text.",
        "no_context": "The available research context did not contain enough structured text to build a detailed summary.",
        "references_missing": "## References",
        "references_text": "- No explicit source URLs were preserved in the research context.",
        "title": "# {question}",
    }


def _translate_report_prompt(report_markdown: str, language: str) -> str:
    target_language = "German" if is_german_language(language) else language
    return f"""Translate the following markdown report into {target_language}.

Rules:
- Preserve the markdown structure, including headings, lists, tables, links, citations, and blank lines.
- Preserve URLs, inline code, code fences, file paths, identifiers, and product names exactly.
- Translate all prose and section labels into {language}.
- Prefer natural German technical terms where they read better, for example "vs" -> "gegenüber", "Best Practices" -> "bewährte Vorgehensweisen", "Open Source" -> "Open-Source", "use case" -> "Anwendungsfall", and "trade-off" -> "Abwägung".
- Do not add commentary, summaries, or new sections.
- Return only the translated markdown.

REPORT:
{report_markdown}
"""


async def _translate_final_report(
    report_markdown: str,
    language: str,
    cfg: Config,
    websocket=None,
    cost_callback: callable = None,
    **kwargs,
) -> str:
    if not report_markdown.strip() or not is_german_language(language):
        return report_markdown

    appendix_match = re.search(
        r"(?im)^\s*##\s*(verifikationsprüfung|verification review|begründungskritik|reasoning critic)\b",
        report_markdown,
    )
    appendix_markdown = ""
    body_markdown = report_markdown
    if appendix_match:
        body_markdown = report_markdown[: appendix_match.start()].rstrip()
        appendix_markdown = report_markdown[appendix_match.start() :].strip()
        if not body_markdown.strip():
            body_markdown = report_markdown

    try:
        translated = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise translation engine. Return only the translated markdown.",
                },
                {"role": "user", "content": _translate_report_prompt(body_markdown, language)},
            ],
            temperature=0.0,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs,
        )
    except Exception as exc:
        logger.warning("Unable to translate final report to %s: %s", language, exc, exc_info=True)
        return normalize_german_technical_terms(report_markdown) if is_german_language(language) else report_markdown

    translated = re.sub(r"^\s*```(?:markdown|md|text)?\s*|\s*```\s*$", "", translated or "", flags=re.IGNORECASE | re.DOTALL).strip()
    if not translated:
        return normalize_german_technical_terms(report_markdown) if is_german_language(language) else report_markdown

    if is_german_language(language):
        translated = normalize_german_technical_terms(translated)
        appendix_markdown = normalize_german_technical_terms(appendix_markdown)

    if appendix_markdown:
        return f"{translated.rstrip()}\n\n{appendix_markdown}".strip()
    return translated


def _normalize_report_markdown(
    report_markdown: str,
    question: str,
    context: str,
    visited_urls: list[str] | None = None,
    language: str | None = None,
) -> str:
    report_markdown = _strip_report_prelude(report_markdown or "")
    report_markdown = _ensure_report_heading(report_markdown, question)
    report_markdown = _strip_leading_noise_after_heading(report_markdown)

    source_urls = list(visited_urls or [])
    if not source_urls:
        source_urls = _extract_urls_from_text(context)

    if is_german_language(language):
        references_pattern = r"(?im)^\s*##?\s*(references|quellen)\b"
    else:
        references_pattern = r"(?im)^\s*##?\s*references\b"

    if source_urls and not re.search(references_pattern, report_markdown):
        report_markdown = f"{report_markdown.rstrip()}\n\n{_render_reference_section(source_urls, context, language=language)}"

    return report_markdown.strip()


def _append_verification_review(
    report_markdown: str,
    question: str,
    context: str,
    visited_urls: list[str] | None,
    cfg: Config,
    verification_sink: Any | None = None,
    return_bundle: bool = False,
) -> tuple[str, dict[str, Any] | None] | str:
    if not getattr(cfg, "enable_verification_review", True):
        return (report_markdown, None) if return_bundle else report_markdown

    if re.search(r"(?im)^\s*##\s*verification review\b", report_markdown):
        bundle = (
            getattr(verification_sink, "verification_bundle", None)
            if verification_sink is not None
            else None
        )
        return (report_markdown, bundle) if return_bundle else report_markdown

    bundle = build_verification_bundle(
        query=question,
        context=context,
        report_markdown=report_markdown,
        visited_urls=visited_urls,
        language=getattr(cfg, "language", None),
    )

    if verification_sink is not None:
        try:
            setattr(verification_sink, "verification_bundle", bundle)
        except Exception:
            logger.debug("Unable to store verification bundle on sink", exc_info=True)

    verification_section = render_verification_section(bundle, language=getattr(cfg, "language", "english"))
    rendered = f"{report_markdown.rstrip()}\n\n{verification_section}".strip()
    return (rendered, bundle) if return_bundle else rendered


async def _append_reasoning_critic_review(
    report_markdown: str,
    question: str,
    context: str,
    visited_urls: list[str] | None,
    cfg: Config,
    verification_bundle: dict[str, Any] | None = None,
    verification_sink: Any | None = None,
    cost_callback: callable = None,
    agent_role_prompt: str = "",
    websocket=None,
    return_bundle: bool = False,
    **kwargs,
) -> tuple[str, dict[str, Any] | None] | str:
    if not getattr(cfg, "enable_reasoning_critic", True):
        if return_bundle:
            return report_markdown, None
        return report_markdown

    if re.search(r"(?im)^\s*##\s*reasoning critic\b", report_markdown):
        critic_bundle = None
        if verification_sink is not None:
            critic_bundle = getattr(verification_sink, "reasoning_critic_bundle", None)
        if return_bundle:
            return report_markdown, critic_bundle
        return report_markdown

    critic_bundle = await build_reasoning_critic_bundle(
        query=question,
        context=context,
        report_markdown=report_markdown,
        verification_bundle=verification_bundle,
        cfg=cfg,
        agent_role_prompt=agent_role_prompt,
        language=getattr(cfg, "language", None),
        websocket=websocket,
        cost_callback=cost_callback,
        visited_urls=visited_urls,
        **kwargs,
    )

    if verification_bundle is not None:
        verification_bundle["critic"] = critic_bundle
        if verification_sink is not None:
            try:
                setattr(verification_sink, "verification_bundle", verification_bundle)
            except Exception:
                logger.debug("Unable to update verification bundle with critic", exc_info=True)

    if verification_sink is not None:
        try:
            setattr(verification_sink, "reasoning_critic_bundle", critic_bundle)
        except Exception:
            logger.debug("Unable to store reasoning critic bundle on sink", exc_info=True)

    critic_section = render_reasoning_critic_section(critic_bundle, language=getattr(cfg, "language", "english"))
    rendered = f"{report_markdown.rstrip()}\n\n{critic_section}".strip()
    if return_bundle:
        return rendered, critic_bundle
    return rendered


async def _generate_local_report(
    question: str,
    context: str,
    language: str,
    tone: Tone | None,
    cfg: Config,
    llm_provider: str,
    llm_kwargs: dict[str, Any],
    agent_role_prompt: str,
    cost_callback: callable = None,
    visited_urls: list[str] | None = None,
    websocket=None,
    **kwargs,
) -> str:
    del tone, cfg, llm_provider, llm_kwargs, agent_role_prompt, cost_callback, websocket, kwargs
    context = _normalize_context_text(context)

    def split_sentences(text: str) -> list[str]:
        chunks = re.split(r"(?<=[.!?])\s+|\n{2,}", text or "")
        cleaned: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            sentence = re.sub(r"\s+", " ", chunk).strip()
            if len(sentence) < 40:
                continue
            if sentence in seen:
                continue
            seen.add(sentence)
            cleaned.append(sentence)
        return cleaned

    def shorten(text: str, max_length: int = 220) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    keywords = [word for word in re.findall(r"[A-Za-z0-9]+", question.lower()) if len(word) > 3]
    sentences = split_sentences(context)

    if keywords:
        matched = [
            sentence
            for sentence in sentences
            if any(keyword in sentence.lower() for keyword in keywords) or re.search(r"\d", sentence)
        ]
    else:
        matched = []

    if not matched:
        matched = sentences

    text = _report_language_text(language)
    overview_parts = matched[:3] if matched else [context[:600].strip()]
    overview = " ".join(part for part in overview_parts if part).strip()
    if not overview:
        overview = text["no_context"]

    key_findings = matched[:5] if matched else []
    if not key_findings:
        key_findings = [overview]

    references = _render_reference_section(visited_urls, context, language=language)

    report_lines = [
        text["title"].format(question=question),
        "",
        text["overview"],
        overview,
        "",
        text["key_findings"],
    ]

    for item in key_findings[:5]:
        report_lines.append(f"- {shorten(item)}")

    report_lines.extend([
        "",
        text["caveats"],
        text["deterministic_summary"],
        text["missing_source"],
        "",
        references,
    ])

    return _normalize_report_markdown(
        "\n".join(report_lines).strip(),
        question=question,
        context=context,
        visited_urls=visited_urls,
        language=language,
    )


async def write_report_introduction(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket=None,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> str:
    """
    Generate an introduction for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        str: The generated introduction.
    """
    try:
        context = _normalize_context_text(context)
        introduction = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": prompt_family.generate_report_introduction(
                    question=query,
                    research_summary=context,
                    language=config.language
                )},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )
        return introduction
    except Exception as e:
        logger.error(f"Error in generating report introduction: {e}")
    return ""


async def write_conclusion(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket=None,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> str:
    """
    Write a conclusion for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        str: The generated conclusion.
    """
    try:
        context = _normalize_context_text(context)
        conclusion = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {
                    "role": "user",
                    "content": prompt_family.generate_report_conclusion(query=query,
                                                                        report_content=context,
                                                                        language=config.language),
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )
        return conclusion
    except Exception as e:
        logger.error(f"Error in writing conclusion: {e}")
    return ""


async def summarize_url(
    url: str,
    content: str,
    role: str,
    config: Config,
    websocket=None,
    cost_callback: callable = None,
    **kwargs
) -> str:
    """
    Summarize the content of a URL.

    Args:
        url (str): The URL to summarize.
        content (str): The content of the URL.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.

    Returns:
        str: The summarized content.
    """
    try:
        summary = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": f"Summarize the following content from {url}:\n\n{content}"},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )
        return summary
    except Exception as e:
        logger.error(f"Error in summarizing URL: {e}")
    return ""


async def generate_draft_section_titles(
    query: str,
    current_subtopic: str,
    context: str,
    role: str,
    config: Config,
    websocket=None,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> List[str]:
    """
    Generate draft section titles for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        List[str]: A list of generated section titles.
    """
    try:
        context = _normalize_context_text(context)
        section_titles = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": prompt_family.generate_draft_titles_prompt(
                    current_subtopic, query, context)},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=None,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )
        return section_titles.split("\n")
    except Exception as e:
        logger.error(f"Error in generating draft section titles: {e}")
    return []


async def generate_report(
    query: str,
    context,
    agent_role_prompt: str,
    report_type: str,
    tone: Tone,
    report_source: str,
    websocket,
    cfg,
    main_topic: str = "",
    existing_headers: list = [],
    relevant_written_contents: list = [],
    cost_callback: callable = None,
    custom_prompt: str = "", # This can be any prompt the user chooses with the context
    headers=None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    available_images: list = None,
    visited_urls: list[str] | None = None,
    **kwargs
):
    """
    generates the final report
    Args:
        query:
        context:
        agent_role_prompt:
        report_type:
        websocket:
        tone:
        cfg:
        main_topic:
        existing_headers:
        relevant_written_contents:
        cost_callback:
        prompt_family: Family of prompts
        available_images: Pre-generated images to embed in the report

    Returns:
        report:

    """
    available_images = available_images or []
    verification_sink = kwargs.pop("verification_sink", None)
    context_text = _normalize_context_text(context)
    generate_prompt = get_prompt_by_report_type(report_type, prompt_family)
    report = ""

    if report_type == "subtopic_report":
        content = f"{generate_prompt(query, existing_headers, relevant_written_contents, main_topic, context_text, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words, language=cfg.language)}"
    elif custom_prompt:
        content = f"{custom_prompt}\n\nContext: {context_text}"
    else:
        content = f"{generate_prompt(query, context_text, report_source, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words, language=cfg.language)}"

    # Add available images instruction if images were pre-generated
    if available_images:
        images_info = "\n".join([
            f"- Image {i+1}: ![{img.get('title', img.get('alt_text', 'Illustration'))}]({img['url']}) - {img.get('section_hint', 'General')}"
            for i, img in enumerate(available_images)
        ])
        content += f"""

AVAILABLE IMAGES:
You have the following pre-generated images available. Embed them in relevant sections of your report using the exact markdown syntax provided:

{images_info}

Place each image on its own line after the relevant section header or paragraph. Use all available images where they add value to the content."""
    try:
        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": content},
            ],
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )
    except Exception:
        try:
            report = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=[
                    {"role": "user", "content": f"{agent_role_prompt}\n\n{content}"},
                ],
                temperature=0.35,
                llm_provider=cfg.smart_llm_provider,
                stream=True,
                websocket=websocket,
                max_tokens=cfg.smart_token_limit,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
                **kwargs
            )
        except Exception as e:
            print(f"Error in generate_report: {e}")

    report = _normalize_report_markdown(
        report,
        question=query,
        context=context_text,
        visited_urls=visited_urls,
        language=cfg.language,
    )

    if _report_needs_deterministic_fallback(report):
        logger.warning(
            "Model report looked corrupted or unstructured; falling back to deterministic synthesis."
        )
        report = await _generate_local_report(
            question=query,
            context=context_text,
            language=cfg.language,
            tone=tone,
            cfg=cfg,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            agent_role_prompt=agent_role_prompt,
            cost_callback=cost_callback,
            visited_urls=visited_urls,
            websocket=websocket,
            **kwargs,
        )

    report, verification_bundle = _append_verification_review(
        report,
        question=query,
        context=context_text,
        visited_urls=visited_urls,
        cfg=cfg,
        verification_sink=verification_sink,
        return_bundle=True,
    )

    report, critic_bundle = await _append_reasoning_critic_review(
        report,
        question=query,
        context=context_text,
        visited_urls=visited_urls,
        cfg=cfg,
        verification_bundle=verification_bundle,
        verification_sink=verification_sink,
        cost_callback=cost_callback,
        agent_role_prompt=agent_role_prompt,
        websocket=websocket,
        return_bundle=True,
        **kwargs,
    )

    report = await _translate_final_report(
        report,
        language=cfg.language,
        cfg=cfg,
        websocket=websocket,
        cost_callback=cost_callback,
    )

    if verification_sink is not None and verification_bundle is not None:
        try:
            setattr(verification_sink, "verification_bundle", verification_bundle)
        except Exception:
            logger.debug("Unable to update verification bundle on sink", exc_info=True)
        if critic_bundle is not None:
            try:
                setattr(verification_sink, "reasoning_critic_bundle", critic_bundle)
            except Exception:
                logger.debug("Unable to update reasoning critic bundle on sink", exc_info=True)

    return report
