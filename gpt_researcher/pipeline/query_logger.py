import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class QueryLogger:
    def __init__(self):
        self._last_entry: Optional[dict] = None

    def log_query_start(self, query: str, safety_info: Optional[dict] = None) -> dict:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_query": query,
            "query_hash": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "safety_info": safety_info or {
                "checked": False,
                "mode": "TRANSPARENT",
                "blocked": False,
                "reason": None,
                "action_taken": "proceeded_by_configuration",
            },
            "research_metadata": {
                "subqueries_generated": [],
                "sources_requested": 0,
                "results_returned": 0,
            },
        }
        self._last_entry = entry
        logger.info(f"Query logged: {json.dumps(entry, ensure_ascii=False)}")
        return entry

    def update_research_metadata(self, subqueries: list, sources: int = 0, results: int = 0) -> None:
        if self._last_entry:
            self._last_entry["research_metadata"]["subqueries_generated"] = subqueries
            self._last_entry["research_metadata"]["sources_requested"] = sources
            self._last_entry["research_metadata"]["results_returned"] = results

    def get_last_entry(self) -> Optional[dict]:
        return self._last_entry


query_logger = QueryLogger()
