"""Unit tests for the industry-grade native Concept-Diff Ingestion Gatekeeper."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from gpt_researcher.config.config import Config
from gpt_researcher.context.concept_diff.knowledge_graph import (
    FactAssertion,
    SessionKnowledgeGraph,
)
from gpt_researcher.context.concept_diff.extractor import FactExtractor
from gpt_researcher.context.concept_diff.diff_engine import ConceptDiffEngine


class TestKnowledgeGraph:
    def test_fact_assertion_keys(self):
        fact1 = FactAssertion(
            subject="Solid-State Battery",
            predicate="achieves",
            object_val="500 Wh/kg",
            is_numeric=True,
        )
        fact2 = FactAssertion(
            subject="solid state battery",
            predicate="achieves",
            object_val="500 Wh/kg",
            is_numeric=True,
        )
        assert fact1.canonical_key() == fact2.canonical_key()
        assert fact1.subject_predicate_key() == fact2.subject_predicate_key()

    def test_exact_duplicate_detection(self):
        graph = SessionKnowledgeGraph()
        fact = FactAssertion(
            subject="QuantumScape",
            predicate="announced",
            object_val="QSE-5 cell B-samples",
            is_numeric=False,
        )

        assert graph.add_fact(fact) is True
        assert graph.is_exact_duplicate(fact) is True
        # Adding exact duplicate again should return False
        assert graph.add_fact(fact) is False
        assert len(graph.facts) == 1

    def test_conflict_detection(self):
        graph = SessionKnowledgeGraph()
        fact1 = FactAssertion(
            subject="Battery Pack Cost",
            predicate="targets",
            object_val="$100/kWh",
            is_numeric=True,
        )
        fact2 = FactAssertion(
            subject="Battery Pack Cost",
            predicate="targets",
            object_val="$140/kWh",
            is_numeric=True,
        )

        graph.add_fact(fact1)
        conflict = graph.find_conflict(fact2)
        assert conflict is not None
        assert conflict.object_val == "$100/kWh"

    def test_graph_statistics(self):
        graph = SessionKnowledgeGraph()
        fact1 = FactAssertion(subject="Tesla", predicate="produces", object_val="4680 cells")
        fact2 = FactAssertion(subject="CATL", predicate="develops", object_val="Qilin battery")

        graph.add_fact(fact1)
        graph.add_fact(fact2)
        stats = graph.get_stats()
        assert stats["total_facts"] == 2
        assert stats["total_entities"] == 4


class TestFactExtractor:
    def test_missing_model_raises_error(self):
        extractor = FactExtractor(llm_model=None)
        with pytest.raises(ValueError, match="FactExtractor requires an active LLM model"):
            import asyncio
            asyncio.run(extractor.extract_facts(raw_text="Some text"))

    @pytest.mark.asyncio
    async def test_clean_text(self):
        extractor = FactExtractor(llm_model="test-model")
        raw = "<script>var x = 1;</script><p>Real technical content here.</p>"
        cleaned = extractor.clean_text(raw)
        assert "<script>" not in cleaned
        assert "Real technical content here." in cleaned

    @pytest.mark.asyncio
    async def test_llm_structured_extraction(self):
        extractor = FactExtractor(llm_model="gemini-2.5-flash", llm_provider="google")
        mock_llm_response = (
            '```json\n'
            '[\n'
            '  {"subject": "Amprius", "predicate": "achieves", "object_val": "450 Wh/kg", "is_numeric": true, "context_snippet": "Amprius achieves 450 Wh/kg."}\n'
            ']\n'
            '```'
        )

        with patch("gpt_researcher.context.concept_diff.extractor.create_chat_completion", AsyncMock(return_value=mock_llm_response)):
            facts = await extractor.extract_facts(
                raw_text="Amprius announced battery cells achieving 450 Wh/kg in testing.",
                source_url="https://amprius.com",
                source_title="Amprius Breakthrough",
            )
            assert len(facts) == 1
            assert facts[0].subject == "Amprius"
            assert facts[0].object_val == "450 Wh/kg"
            assert facts[0].is_numeric is True

    @pytest.mark.asyncio
    async def test_rate_limit_retry_backoff(self):
        extractor = FactExtractor(
            llm_model="gemini-2.5-flash",
            llm_provider="google",
            max_retries=2,
            retry_base_delay=0.01,
        )
        mock_llm_response = '[{"subject": "QuantumScape", "predicate": "ships", "object_val": "B-samples", "is_numeric": false}]'

        # First call fails with 429 RateLimit, second call succeeds
        mock_call = AsyncMock(side_effect=[Exception("429 Too Many Requests: Rate Limit"), mock_llm_response])

        with patch("gpt_researcher.context.concept_diff.extractor.create_chat_completion", mock_call):
            facts = await extractor.extract_facts(
                raw_text="QuantumScape started shipping B-samples to automotive partners.",
                source_url="https://qs.com",
            )
            assert len(facts) == 1
            assert facts[0].subject == "QuantumScape"
            assert mock_call.call_count == 2

    def test_error_diagnostics(self):
        extractor = FactExtractor(llm_model="gpt-4o", llm_provider="openai")
        
        diag_429 = extractor._diagnose_error(Exception("429 rate limit exceeded"))
        assert "Rate limit / Quota threshold reached" in diag_429

        diag_401 = extractor._diagnose_error(Exception("401 invalid api key provided"))
        assert "Authentication failed" in diag_401

        diag_404 = extractor._diagnose_error(Exception("404 model not found"))
        assert "not found" in diag_404


class TestConceptDiffEngine:
    @pytest.mark.asyncio
    async def test_process_observation_diff_flow(self):
        mock_extractor = MagicMock()
        mock_extractor.extract_facts = AsyncMock(side_effect=[
            # Source 1 facts
            [
                FactAssertion(subject="CompanyA", predicate="achieves", object_val="400 Wh/kg", is_numeric=True),
                FactAssertion(subject="CompanyA", predicate="targets", object_val="$100/kWh", is_numeric=True),
            ],
            # Source 2 facts (exact duplicates)
            [
                FactAssertion(subject="CompanyA", predicate="achieves", object_val="400 Wh/kg", is_numeric=True),
                FactAssertion(subject="CompanyA", predicate="targets", object_val="$100/kWh", is_numeric=True),
            ],
        ])

        engine = ConceptDiffEngine(extractor=mock_extractor)

        text1 = (
            "Electric vehicle batteries have evolved rapidly since commercialization in 1991. "
            "Lithium-ion batteries were pioneered decades ago for consumer electronics. "
            "Historically, nickel-manganese-cobalt chemistries dominated automotive applications. "
            "Many analysts believe the next frontier lies in solid-state electrolytes replacing liquid solvents. "
            "CompanyA achieves 400 Wh/kg in 2026 solid-state battery testing. "
            "The manufacturing scale targets $100/kWh cost across all gigafactories. "
            "Global supply chains continue to expand across Europe and North America with substantial investments."
        )

        payload1 = await engine.process_observation(
            raw_text=text1,
            source_url="https://source1.com",
            source_title="Source 1",
        )
        assert "🟢 NEW FACTS ADDED:" in payload1
        assert "CONCEPT DIFF PAYLOAD" in payload1

        payload2 = await engine.process_observation(
            raw_text=text1,
            source_url="https://source2.com",
            source_title="Source 2",
        )
        telemetry = engine.get_telemetry()
        assert telemetry["total_discarded_facts"] == 2
        assert telemetry["total_added_facts"] == 2
        assert telemetry["raw_words_processed"] > telemetry["payload_words_emitted"]
        assert telemetry["word_reduction_pct"] > 0

    @pytest.mark.asyncio
    async def test_conflict_surfacing_in_payload(self):
        mock_extractor = MagicMock()
        mock_extractor.extract_facts = AsyncMock(side_effect=[
            [FactAssertion(subject="Battery Cost", predicate="targets", object_val="$100/kWh", is_numeric=True)],
            [FactAssertion(subject="Battery Cost", predicate="targets", object_val="$150/kWh", is_numeric=True)],
        ])

        engine = ConceptDiffEngine(extractor=mock_extractor)

        text1 = "Battery Cost targets $100/kWh by 2026."
        await engine.process_observation(text1, source_url="https://source1.com")

        text2 = "Battery Cost targets $150/kWh according to analyst report."
        payload2 = await engine.process_observation(text2, source_url="https://source2.com")

        assert "⚠️ CONFLICTS DETECTED:" in payload2
        assert "Current claims **'$150/kWh'**, contradicting prior **'$100/kWh'**" in payload2


class TestConfigIntegration:
    def test_config_enable_concept_diff_default(self):
        config = Config()
        assert hasattr(config, "enable_concept_diff")
        assert config.enable_concept_diff is False
