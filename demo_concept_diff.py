"""Interactive Terminal Demo for GPT Researcher Concept-Diff Engine.

Run this script directly in your terminal to see how the Concept-Diff Engine
ingests raw web pages, extracts atomic assertions, discards redundant fluff,
detects numerical conflicts, and tracks real token reduction.

Usage:
    python demo_concept_diff.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from gpt_researcher.context.concept_diff import ConceptDiffEngine, SessionKnowledgeGraph, FactAssertion


# Sample raw scraped web pages simulating a deep research task
SAMPLE_SOURCE_1 = {
    "title": "QuantumScape QSE-5 Solid-State Battery Commercialization Roadmap 2026",
    "url": "https://battery-tech-insights.com/quantumscape-qse5-2026",
    "content": """
    Electric vehicle batteries have evolved rapidly since Sony first commercialized lithium-ion cells in 1991. 
    Traditional lithium-ion batteries rely on liquid organic electrolytes, which pose flammability risks and have 
    approached their theoretical energy density ceiling of approximately 250 to 300 Wh/kg. 
    Decades of research have explored alternative anode materials and solid electrolytes.
    
    QuantumScape achieved a major milestone in 2026 by shipping first commercial B-samples of its QSE-5 solid-state cell.
    The QSE-5 cell demonstrates an energy density of 450 Wh/kg and achieves an 80% fast charge in under 12 minutes.
    The company announced an initial manufacturing cost target of $110/kWh at gigafactory scale with Volkswagen Group.
    Production is scheduled to begin scaling in late 2026 across joint venture facilities in Germany and North America.
    
    All rights reserved. Privacy Policy. Terms of Service. Subscribe to our newsletter for more battery updates.
    """
}

SAMPLE_SOURCE_2 = {
    "title": "Solid State Battery Market Overview & Competitor Cost Breakdown",
    "url": "https://clean-energy-analyst.org/ssb-market-analysis",
    "content": """
    Electric vehicle batteries have evolved rapidly since Sony first commercialized lithium-ion cells in 1991. 
    Traditional lithium-ion batteries rely on liquid organic electrolytes, which pose flammability risks and have 
    approached their theoretical energy density ceiling. 
    As the automotive industry transitions away from internal combustion engines, battery chemistry remains critical.
    
    QuantumScape shipped B-samples of its QSE-5 solid-state cell to automotive OEM partners in 2026.
    However, industry analysts report that initial QuantumScape QSE-5 manufacturing cost targets $145/kWh,
    higher than the $110/kWh cited in official press materials due to ceramic separator yield constraints.
    Meanwhile, CATL announced mass production of its condensed battery achieving 500 Wh/kg for aviation applications.
    CATL targets full automotive delivery starting in Q4 2026.
    
    Accept All Cookies to continue browsing. Copyright 2026 Clean Energy Analyst.
    """
}


async def run_demo():
    print("=" * 80)
    print("⚡ GPT RESEARCHER: CONCEPT-DIFF INGESTION GATEKEEPER DEMO")
    print("=" * 80)

    # Check for active LLM API keys
    google_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    mistral_key = os.getenv("MISTRAL_API_KEY")

    api_key_available = bool(google_key or openai_key or anthropic_key or groq_key or mistral_key)

    print(f"\n🔑 LLM Environment Check:")
    if api_key_available:
        if google_key:
            provider = "google_genai"
            default_model = "gemini-2.5-flash"
        elif openai_key:
            provider = "openai"
            default_model = "gpt-4o-mini"
        elif anthropic_key:
            provider = "anthropic"
            default_model = "claude-3-5-haiku-latest"
        elif groq_key:
            provider = "groq"
            default_model = "llama-3.1-8b-instant"
        else:
            provider = "mistralai"
            default_model = "mistral-small-latest"

        raw_fast_llm = os.getenv("FAST_LLM", default_model)
        if ":" in raw_fast_llm:
            provider, llm_model = raw_fast_llm.split(":", 1)
        else:
            llm_model = raw_fast_llm

        print(f"   ✅ Active LLM detected: Provider '{provider}' | Model '{llm_model}'")
        engine = ConceptDiffEngine(llm_model=llm_model, llm_provider=provider)
    else:
        print("   ℹ️ No API Key found in .env. Running demonstration with sample structured facts.")
        from unittest.mock import AsyncMock, MagicMock
        mock_extractor = MagicMock()
        mock_extractor.extract_facts = AsyncMock(side_effect=[
            # Source 1 Facts
            [
                FactAssertion(subject="QuantumScape", predicate="shipped", object_val="QSE-5 B-samples in 2026", is_numeric=True),
                FactAssertion(subject="QuantumScape QSE-5", predicate="achieves", object_val="450 Wh/kg", is_numeric=True),
                FactAssertion(subject="QuantumScape QSE-5", predicate="reaches", object_val="80% charge in 12 min", is_numeric=True),
                FactAssertion(subject="QuantumScape QSE-5 cost", predicate="targets", object_val="$110/kWh", is_numeric=True),
            ],
            # Source 2 Facts (Contains 1 duplicate, 1 conflict, and 2 new facts)
            [
                FactAssertion(subject="QuantumScape", predicate="shipped", object_val="QSE-5 B-samples in 2026", is_numeric=True),  # Exact duplicate -> DISCARD
                FactAssertion(subject="QuantumScape QSE-5 cost", predicate="targets", object_val="$145/kWh", is_numeric=True),      # Conflict with $110 -> DIFF_CONFLICT
                FactAssertion(subject="CATL condensed battery", predicate="achieves", object_val="500 Wh/kg", is_numeric=True),     # New fact -> DIFF_ADD
                FactAssertion(subject="CATL", predicate="targets", object_val="delivery in Q4 2026", is_numeric=True),              # New fact -> DIFF_ADD
            ]
        ])
        engine = ConceptDiffEngine(extractor=mock_extractor)

    # -------------------------------------------------------------
    # Ingest Source 1
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"📥 [STEP 1] Ingesting Web Source #1: '{SAMPLE_SOURCE_1['title']}'")
    print(f"   Raw Word Count: {len(SAMPLE_SOURCE_1['content'].split())} words")
    print("-" * 80)
    
    payload_1 = await engine.process_observation(
        raw_text=SAMPLE_SOURCE_1["content"],
        source_url=SAMPLE_SOURCE_1["url"],
        source_title=SAMPLE_SOURCE_1["title"]
    )
    print(payload_1)

    # -------------------------------------------------------------
    # Ingest Source 2
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"📥 [STEP 2] Ingesting Web Source #2: '{SAMPLE_SOURCE_2['title']}'")
    print(f"   Raw Word Count: {len(SAMPLE_SOURCE_2['content'].split())} words (contains overlapping background fluff)")
    print("-" * 80)
    
    payload_2 = await engine.process_observation(
        raw_text=SAMPLE_SOURCE_2["content"],
        source_url=SAMPLE_SOURCE_2["url"],
        source_title=SAMPLE_SOURCE_2["title"]
    )
    print(payload_2)

    # -------------------------------------------------------------
    # Telemetry & Performance Summary
    # -------------------------------------------------------------
    telemetry = engine.get_telemetry()
    print("\n" + "=" * 80)
    print("📊 GATEKEEPER TELEMETRY & TOKEN SAVINGS SUMMARY")
    print("=" * 80)
    print(f"  • Total Raw Words Ingested:   {telemetry['raw_words_processed']} words")
    print(f"  • Total Dense Words Emitted:   {telemetry['payload_words_emitted']} words")
    print(f"  • Redundant Facts Discarded:   {telemetry['total_discarded_facts']} ($0 tokens spent on 1991 history fluff)")
    print(f"  • Novel Facts Preserved:       {telemetry['total_added_facts']}")
    print(f"  • Conflicting Specs Flagged:   {telemetry['total_conflicts_detected']} ($110/kWh vs $145/kWh)")
    print(f"  • Ingestion Token Reduction:   ⚡ {telemetry['word_reduction_pct']}% Token Savings")
    print("=" * 80 + "\n")

    print("💡 How to run full GPT Researcher with Concept-Diff in your terminal:")
    print("   1. Enable it in your .env: ENABLE_CONCEPT_DIFF=True")
    print('   2. Run: python cli.py "latest solid-state battery breakthroughs 2026" --report_type research_report\n')


if __name__ == "__main__":
    asyncio.run(run_demo())
