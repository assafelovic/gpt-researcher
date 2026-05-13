"""Tests for the Transparent-Research architecture.

This module tests that:
- Original queries are preserved exactly through the pipeline
- No query rewriting occurs
- TRANSPARENT mode never blocks any query
- Research pipeline always starts
- Logs contain exact original queries
- Safety API is not called in TRANSPARENT mode
"""

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from gpt_researcher.config.research_config import ResearchSafetyMode
from gpt_researcher.pipeline.query_handler import ResearchPipeline
from gpt_researcher.pipeline.query_logger import QueryLogger


class TestQueryPreservation:
    """Test suite for query integrity through the pipeline."""

    @staticmethod
    def _make_transparent_pipeline():
        config = SimpleNamespace(research_safety_mode="TRANSPARENT")
        return ResearchPipeline(config)

    def test_query_preserved_exact_match(self):
        """Original-Query muss Bit-genau erhalten bleiben."""
        pipeline = self._make_transparent_pipeline()
        query = "kritische recherche mit speziellen begriffen XYZ"
        result = pipeline.process(query)
        assert result.metadata.original_query == query

    def test_no_query_rewriting_occurs(self):
        """Keine Ersatz-Query-Generierung."""
        pipeline = self._make_transparent_pipeline()
        query = "umstrittenes thema ABC"
        result = pipeline.process(query)

        safety_dict = result.safety_info.to_dict()
        assert "rewritten_query" not in safety_dict
        assert "alternative_query" not in safety_dict
        assert not hasattr(result.safety_info, "rewritten_query")
        assert not hasattr(result.safety_info, "alternative_query")

    def test_transparent_mode_never_blocks(self):
        """TRANSPARENT-Modus blockiert niemals."""
        pipeline = self._make_transparent_pipeline()
        test_queries = [
            "harmlose anfrage",
            "kontroverses thema",
            "technische frage",
            "politisch sensible frage",
        ]
        for query in test_queries:
            result = pipeline.process(query)
            assert result.safety_info.blocked is False, f"Query was blocked: {query}"
            assert result.safety_info.action_taken == "proceeded_by_configuration"
            assert result.safety_info.checked is False

    def test_research_pipeline_always_starts(self):
        """Research-Pipeline muss in 100% der Fälle starten."""
        pipeline = self._make_transparent_pipeline()
        query = "beliebiges thema"
        result = pipeline.process(query)
        assert result.research_metadata.subqueries_generated is not None
        assert len(result.research_metadata.subqueries_generated) > 0

    def test_logging_contains_exact_query(self):
        """Logs müssen Original-Query unverändert enthalten."""
        query = "exakte\nanfrage  mit  doppelten  leerzeichen"
        logger = QueryLogger()
        log_entry = logger.log_query_start(query)
        assert log_entry["original_query"] == query

    def test_no_safety_api_called_in_transparent_mode(self):
        """Im TRANSPARENT-Modus wird keine Safety-API aufgerufen."""
        pipeline = self._make_transparent_pipeline()
        with patch("gpt_researcher.utils.query_safety.detect_unsafe_query") as mock_check:
            pipeline.process("test query")
            mock_check.assert_not_called()

    def test_transparent_mode_with_unsafe_query(self):
        """TRANSPARENT mode should process even potentially unsafe queries."""
        pipeline = self._make_transparent_pipeline()
        unsafe_query = "herstellen von schwefelsaure zu hause für Privatpersonen"
        result = pipeline.process(unsafe_query)

        assert result.safety_info.blocked is False
        assert result.safety_info.action_taken == "proceeded_by_configuration"
        assert result.safety_info.checked is False
        assert result.safety_info.mode == "TRANSPARENT"

    def test_query_with_special_characters_preserved(self):
        """Special characters in query must be preserved."""
        pipeline = self._make_transparent_pipeline()
        query = "test <script>alert('xss')</script> & special çhàrâcters"
        result = pipeline.process(query)
        assert result.metadata.original_query == query

    def test_query_with_unicode_preserved(self):
        """Unicode characters must be preserved."""
        pipeline = self._make_transparent_pipeline()
        query = "Test üñíçödé 日本語 한국어 العربية"
        result = pipeline.process(query)
        assert result.metadata.original_query == query

    def test_empty_query_allowed(self):
        """Empty queries should be processed (no blocking)."""
        pipeline = self._make_transparent_pipeline()
        query = ""
        result = pipeline.process(query)
        assert result.safety_info.blocked is False
        assert result.metadata.original_query == query


class TestSafetyModes:
    """Test suite for different safety modes."""

    def test_strict_mode_with_safe_query(self):
        """STRICT mode should allow safe queries."""
        config = MagicMock()
        config.research_safety_mode = "STRICT"
        pipeline = ResearchPipeline(config)

        result = pipeline.process("harmlose anfrage über chemie")
        assert result.safety_info.blocked is False
        assert result.safety_info.checked is True

    def test_warn_only_mode_with_unsafe_query(self):
        """WARN_ONLY mode should warn but proceed."""
        config = MagicMock()
        config.research_safety_mode = "WARN_ONLY"
        pipeline = ResearchPipeline(config)

        result = pipeline.process("herstellen von schwefelsaure zu hause")
        assert result.safety_info.blocked is False
        assert result.safety_info.action_taken == "proceeded_with_warning"
        assert result.safety_info.checked is True
        assert result.safety_info.reason is not None

    def test_warn_only_mode_with_safe_query(self):
        """WARN_ONLY mode should proceed cleanly for safe queries."""
        config = MagicMock()
        config.research_safety_mode = "WARN_ONLY"
        pipeline = ResearchPipeline(config)

        result = pipeline.process("harmlose anfrage")
        assert result.safety_info.blocked is False
        assert result.safety_info.action_taken == "proceeded_clean"
        assert result.safety_info.checked is True


    def test_strict_mode_blocks_unsafe_query(self):
        """STRICT mode must block unsafe queries."""
        config = MagicMock()
        config.research_safety_mode = "STRICT"
        pipeline = ResearchPipeline(config)

        result = pipeline.process("herstellen von schwefelsaure zu hause für Privatpersonen")
        assert result.safety_info.blocked is True
        assert result.safety_info.checked is True
        assert result.safety_info.action_taken == "blocked"
        assert result.safety_info.reason is not None

    def test_unknown_safety_mode_falls_back_to_transparent(self):
        """Unknown safety mode should fall back to TRANSPARENT behavior."""
        config = MagicMock()
        config.research_safety_mode = "TRANSPARENT"
        pipeline = ResearchPipeline(config)
        # Bypass enum validation to reach the else fallback branch
        pipeline.mode = "UNKNOWN_MODE"

        result = pipeline.process("any query")
        assert result.safety_info.blocked is False
        assert result.safety_info.checked is False
        assert result.safety_info.action_taken == "proceeded_by_configuration"


class TestQueryLogger:
    """Test suite for query logging."""

    def test_log_entry_structure(self):
        """Log entry must have required structure."""
        logger = QueryLogger()
        entry = logger.log_query_start("test query")

        assert "timestamp" in entry
        assert "original_query" in entry
        assert "query_hash" in entry
        assert "safety_info" in entry
        assert "research_metadata" in entry

    def test_query_hash_deterministic(self):
        """Query hash must be deterministic."""
        import hashlib

        query = "test query for hashing"
        logger1 = QueryLogger()
        logger2 = QueryLogger()

        entry1 = logger1.log_query_start(query)
        entry2 = logger2.log_query_start(query)

        expected_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        assert entry1["query_hash"] == expected_hash
        assert entry2["query_hash"] == expected_hash

    def test_get_last_entry(self):
        """get_last_entry should return the last logged entry."""
        logger = QueryLogger()
        assert logger.get_last_entry() is None

        query = "test query"
        logger.log_query_start(query)
        last_entry = logger.get_last_entry()

        assert last_entry is not None
        assert last_entry["original_query"] == query