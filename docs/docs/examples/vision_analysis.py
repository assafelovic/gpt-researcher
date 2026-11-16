"""Example: image understanding (VLM captions) during research.

Run with an OpenAI-compatible vision endpoint, e.g. DashScope/Qwen-VL:

    export VISION_ENABLED=true
    export VISION_MODEL=qwen2.5-vl-3b-instruct
    export VISION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    export VISION_API_KEY=sk-...
    python vision_analysis.py

Any OpenAI-compatible endpoint (OpenAI, DashScope, local vLLM) works.
"""

import asyncio

from gpt_researcher import GPTResearcher

QUERY = "What do recent trials show about sodium-glucose cotransporter-2 inhibitors and heart failure hospitalization?"


async def main() -> None:
    researcher = GPTResearcher(query=QUERY, report_type="research_report")
    context = await researcher.conduct_research()

    sources = researcher.research_sources
    enriched = [source for source in sources if source.get("image_captions")]
    print(f"Sources with visual evidence: {len(enriched)} / {len(sources)}")
    for source in enriched[:5]:
        print(f"- {source.get('url')}")
        for caption in source["image_captions"]:
            print(f"    caption: {caption['caption']}")
            if caption.get("text"):
                print(f"    ocr: {caption['text']}")

    report = await researcher.write_report()
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
