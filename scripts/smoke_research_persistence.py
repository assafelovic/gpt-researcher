#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from gpt_researcher.research_run_store import (
    INTERRUPTED_ERROR_CODE,
    ResearchRunStore,
)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="gptr-persistence-") as tmp:
        root = Path(tmp)
        db_path = root / "research_runs.sqlite3"
        output_dir = root / "outputs"
        os.environ["RESEARCH_RUN_STORE_PATH"] = str(db_path)
        os.environ["OUTPUTS_DIR"] = str(output_dir)

        store = ResearchRunStore(db_path, recover_interrupted=False)
        store.create_run(
            "smoke-completed",
            query="restart-safe research smoke",
            report_type="research_report",
            report_source="web",
            tone="Objective",
        )
        report_path = output_dir / "smoke-completed.md"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Smoke report\n", encoding="utf-8")
        store.complete_run(
            "smoke-completed",
            context=["smoke context"],
            sources=[{"title": "Smoke Source", "url": "https://example.com", "content": "ok"}],
            source_urls=["https://example.com"],
            costs=0.0,
            report_path=str(report_path),
            md_path=str(report_path),
        )

        store.create_run("smoke-running", query="interrupted smoke", status="running")

        restarted = ResearchRunStore(db_path, recover_interrupted=True)
        completed = restarted.get_run("smoke-completed")
        interrupted = restarted.get_run("smoke-running")

        assert completed["status"] == "completed"
        assert completed["md_path"] == str(report_path)
        assert completed["sources"][0]["url"] == "https://example.com"
        assert interrupted["status"] == "failed"
        assert interrupted["error_code"] == INTERRUPTED_ERROR_CODE

        print(f"store={db_path}")
        print("completed_status=completed")
        print("interrupted_status=failed")
        print("restart_persistence=ok")


if __name__ == "__main__":
    main()
