"""Checkpoint manager for deep research state persistence.

Persists intermediate research state to disk so that if report generation
fails (rate limits, token limits, etc.), the expensive research phase can
be skipped on retry.
"""

import json
import logging
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CHECKPOINT_DIR = os.path.join(Path.home(), ".gpt-researcher", "checkpoints")


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug for matching."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80]


class ResearchCheckpoint:
    """Persists intermediate deep research state to disk for crash recovery.

    After conduct_research() completes successfully, checkpoint.save() writes
    all reusable state (context, visited_urls, sources, costs, config) to a
    JSON file. If the subsequent write_report() fails, the checkpoint allows
    the next run to skip research entirely and retry only report generation.

    Attributes:
        checkpoint_dir: Directory where checkpoint files are stored.
    """

    def __init__(self, output_dir: str = None):
        """Initialize checkpoint manager.

        Args:
            output_dir: Directory for checkpoint files. Falls back to
                CHECKPOINT_DIR env var, then ~/.gpt-researcher/checkpoints/.
        """
        self.checkpoint_dir = (
            output_dir
            or os.environ.get("CHECKPOINT_DIR")
            or DEFAULT_CHECKPOINT_DIR
        )
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def save(self, researcher, status: str = "research_complete") -> str:
        """Serialize researcher state to JSON after conduct_research() succeeds.

        Args:
            researcher: GPTResearcher instance with completed research state.
            status: Checkpoint status label.

        Returns:
            Path to the saved checkpoint file.
        """
        query = researcher.query
        slug = _slugify(query)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{slug}-{timestamp}.json"
        filepath = os.path.join(self.checkpoint_dir, filename)

        # Extract sources without raw_content (too large)
        compact_sources = []
        for src in (researcher.research_sources or []):
            compact_sources.append({
                k: v for k, v in src.items()
                if k != "raw_content"
            })

        checkpoint_data = {
            "version": 1,
            "status": status,
            "query": query,
            "query_slug": slug,
            "timestamp": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "context": researcher.context if isinstance(researcher.context, str)
                else list(researcher.context) if researcher.context else [],
            "visited_urls": list(researcher.visited_urls) if researcher.visited_urls else [],
            "research_sources": compact_sources,
            "research_costs": researcher.research_costs,
            "agent": researcher.agent,
            "role": researcher.role,
            "config_snapshot": {
                "report_type": researcher.report_type,
                "report_format": researcher.report_format,
                "tone": researcher.tone.value if hasattr(researcher.tone, 'value') else str(researcher.tone),
                "smart_llm": getattr(researcher.cfg, 'smart_llm', None),
                "smart_token_limit": getattr(researcher.cfg, 'smart_token_limit', None),
                "total_words": getattr(researcher.cfg, 'total_words', None),
            },
        }

        # Atomic write: write to temp file then rename
        fd, tmp_path = tempfile.mkstemp(
            dir=self.checkpoint_dir, suffix=".json.tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, filepath)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        logger.info(f"Checkpoint saved: {filepath} ({len(compact_sources)} sources, ${researcher.research_costs:.2f})")
        return filepath

    def find(self, query: str, max_age_hours: int = 168) -> dict[str, Any] | None:
        """Find the most recent valid checkpoint for a given query.

        Args:
            query: Research query to match.
            max_age_hours: Maximum checkpoint age in hours (default 7 days).

        Returns:
            Parsed checkpoint dict with added '_filepath' key, or None.
        """
        target_slug = _slugify(query)
        if not target_slug:
            return None

        now = time.time()
        max_age_secs = max_age_hours * 3600
        best: dict[str, Any] | None = None
        best_time = 0.0

        try:
            entries = os.listdir(self.checkpoint_dir)
        except FileNotFoundError:
            return None

        for entry in entries:
            if not entry.endswith(".json"):
                continue
            filepath = os.path.join(self.checkpoint_dir, entry)

            # Quick age check via mtime before parsing
            try:
                mtime = os.path.getmtime(filepath)
            except OSError:
                continue
            if now - mtime > max_age_secs:
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            # Match by slug
            checkpoint_slug = data.get("query_slug", "")
            if checkpoint_slug != target_slug:
                continue

            # Only return usable checkpoints
            if data.get("status") not in ("research_complete", "report_failed"):
                continue

            if mtime > best_time:
                best = data
                best["_filepath"] = filepath
                best_time = mtime

        return best

    def restore(self, researcher, checkpoint: dict) -> None:
        """Restore researcher state from checkpoint, skipping conduct_research().

        Args:
            researcher: GPTResearcher instance to restore state into.
            checkpoint: Parsed checkpoint dict from find().
        """
        context = checkpoint.get("context", [])
        if isinstance(context, list):
            researcher.context = "\n".join(context) if context else ""
        else:
            researcher.context = context or ""

        researcher.visited_urls = set(checkpoint.get("visited_urls", []))
        researcher.research_sources = checkpoint.get("research_sources", [])
        researcher.research_costs = checkpoint.get("research_costs", 0.0)

        if checkpoint.get("agent"):
            researcher.agent = checkpoint["agent"]
        if checkpoint.get("role"):
            researcher.role = checkpoint["role"]

        logger.info(
            f"Checkpoint restored: {len(checkpoint.get('visited_urls', []))} URLs, "
            f"{len(checkpoint.get('research_sources', []))} sources, "
            f"${checkpoint.get('research_costs', 0):.2f} prior cost"
        )

    def update_status(self, checkpoint_path: str, status: str, error: str = None) -> None:
        """Update checkpoint status (e.g., report_failed, report_complete).

        Args:
            checkpoint_path: Path to the checkpoint file.
            status: New status string.
            error: Optional error message to record.
        """
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["status"] = status
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            if error:
                data["last_error"] = error

            fd, tmp_path = tempfile.mkstemp(
                dir=self.checkpoint_dir, suffix=".json.tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, checkpoint_path)

        except Exception as e:
            logger.warning(f"Failed to update checkpoint status: {e}")

    def cleanup(self, max_age_hours: int = 168) -> int:
        """Remove checkpoints older than max_age.

        Args:
            max_age_hours: Maximum age in hours (default 7 days).

        Returns:
            Number of checkpoints removed.
        """
        now = time.time()
        max_age_secs = max_age_hours * 3600
        removed = 0

        try:
            entries = os.listdir(self.checkpoint_dir)
        except FileNotFoundError:
            return 0

        for entry in entries:
            if not entry.endswith(".json"):
                continue
            filepath = os.path.join(self.checkpoint_dir, entry)
            try:
                if now - os.path.getmtime(filepath) > max_age_secs:
                    os.unlink(filepath)
                    removed += 1
            except OSError:
                continue

        if removed:
            logger.info(f"Cleaned up {removed} stale checkpoint(s)")
        return removed
