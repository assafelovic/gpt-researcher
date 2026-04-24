from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INTERRUPTED_ERROR_CODE = "interrupted_by_restart"
RUNNING_STATUSES = ("pending", "running")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_outputs_dir() -> Path:
    return Path(os.getenv("OUTPUTS_DIR", "outputs")).expanduser()


def get_research_run_store_path() -> Path:
    return Path(
        os.getenv("RESEARCH_RUN_STORE_PATH", os.path.join("data", "research_runs.sqlite3"))
    ).expanduser()


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [jsonable(v) for v in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _json_dump(value: Any) -> str:
    return json.dumps(jsonable(value), ensure_ascii=False)


def _json_load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


class ResearchRunStore:
    """SQLite-backed durable metadata store for research runs."""

    def __init__(self, path: Path | str | None = None, *, recover_interrupted: bool = True):
        self.path = Path(path) if path is not None else get_research_run_store_path()
        self._lock = threading.RLock()
        self._initialize(recover_interrupted=recover_interrupted)

    @classmethod
    def from_env(cls, *, recover_interrupted: bool = True) -> "ResearchRunStore":
        return cls(get_research_run_store_path(), recover_interrupted=recover_interrupted)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self, *, recover_interrupted: bool) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version < 1:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS research_runs (
                        research_id TEXT PRIMARY KEY,
                        query TEXT NOT NULL,
                        report_type TEXT,
                        report_source TEXT,
                        tone TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        context_json TEXT,
                        sources_json TEXT,
                        source_urls_json TEXT,
                        source_count INTEGER NOT NULL DEFAULT 0,
                        costs REAL NOT NULL DEFAULT 0,
                        report_path TEXT,
                        md_path TEXT,
                        pdf_path TEXT,
                        docx_path TEXT,
                        error_code TEXT,
                        error_message TEXT,
                        resource_topic TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_research_runs_status
                        ON research_runs(status);
                    CREATE INDEX IF NOT EXISTS idx_research_runs_resource_topic
                        ON research_runs(resource_topic);
                    PRAGMA user_version = 1;
                    """
                )
            if version < 2:
                try:
                    conn.execute("ALTER TABLE research_runs ADD COLUMN hlt_research_scope_json TEXT")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise
                conn.execute("PRAGMA user_version = 2")
            if recover_interrupted:
                self._mark_interrupted_locked(conn)

    def _mark_interrupted_locked(self, conn: sqlite3.Connection) -> int:
        now = utc_now_iso()
        cursor = conn.execute(
            """
            UPDATE research_runs
               SET status = 'failed',
                   updated_at = ?,
                   completed_at = COALESCE(completed_at, ?),
                   error_code = ?,
                   error_message = COALESCE(error_message, 'Research run interrupted by API restart')
             WHERE status IN ('pending', 'running')
            """,
            (now, now, INTERRUPTED_ERROR_CODE),
        )
        return cursor.rowcount

    def mark_interrupted_runs_failed(self) -> int:
        with self._lock, self._connect() as conn:
            return self._mark_interrupted_locked(conn)

    def create_run(
        self,
        research_id: str,
        *,
        query: str,
        report_type: str | None = None,
        report_source: str | None = None,
        tone: str | None = None,
        status: str = "running",
        resource_topic: str | None = None,
        hlt_research_scope: Any | None = None,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO research_runs (
                    research_id, query, report_type, report_source, tone, status,
                    created_at, updated_at, started_at, resource_topic,
                    hlt_research_scope_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(research_id) DO UPDATE SET
                    query = excluded.query,
                    report_type = excluded.report_type,
                    report_source = excluded.report_source,
                    tone = excluded.tone,
                    status = excluded.status,
                    updated_at = excluded.updated_at,
                    started_at = COALESCE(research_runs.started_at, excluded.started_at),
                    error_code = NULL,
                    error_message = NULL,
                    resource_topic = COALESCE(excluded.resource_topic, research_runs.resource_topic),
                    hlt_research_scope_json = COALESCE(excluded.hlt_research_scope_json, research_runs.hlt_research_scope_json)
                """,
                (
                    research_id,
                    query,
                    report_type,
                    report_source,
                    tone,
                    status,
                    now,
                    now,
                    now,
                    resource_topic,
                    _json_dump(hlt_research_scope) if hlt_research_scope is not None else None,
                ),
            )

    def update_run(self, research_id: str, **fields: Any) -> None:
        allowed = {
            "query",
            "report_type",
            "report_source",
            "tone",
            "status",
            "started_at",
            "completed_at",
            "context",
            "sources",
            "source_urls",
            "source_count",
            "costs",
            "report_path",
            "md_path",
            "pdf_path",
            "docx_path",
            "error_code",
            "error_message",
            "resource_topic",
            "hlt_research_scope",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Unsupported run fields: {', '.join(sorted(unknown))}")

        column_values: dict[str, Any] = {"updated_at": utc_now_iso()}
        for key, value in fields.items():
            if key == "context":
                column_values["context_json"] = _json_dump(value)
            elif key == "sources":
                column_values["sources_json"] = _json_dump(value)
            elif key == "source_urls":
                column_values["source_urls_json"] = _json_dump(value)
            elif key == "hlt_research_scope":
                column_values["hlt_research_scope_json"] = _json_dump(value)
            else:
                column_values[key] = value

        if len(column_values) == 1:
            return

        assignments = ", ".join(f"{column} = ?" for column in column_values)
        values = [*column_values.values(), research_id]
        with self._lock, self._connect() as conn:
            conn.execute(
                f"UPDATE research_runs SET {assignments} WHERE research_id = ?",
                values,
            )

    def complete_run(
        self,
        research_id: str,
        *,
        context: Any | None = None,
        sources: list[dict[str, Any]] | None = None,
        source_urls: list[str] | None = None,
        costs: float | None = None,
        report_path: str | None = None,
        md_path: str | None = None,
        pdf_path: str | None = None,
        docx_path: str | None = None,
        hlt_research_scope: Any | None = None,
    ) -> None:
        sources = sources or []
        source_urls = source_urls or []
        fields: dict[str, Any] = {
            "status": "completed",
            "completed_at": utc_now_iso(),
            "context": context,
            "sources": sources,
            "source_urls": source_urls,
            "source_count": len(sources),
            "costs": costs or 0.0,
            "report_path": report_path,
            "md_path": md_path,
            "pdf_path": pdf_path,
            "docx_path": docx_path,
            "error_code": None,
            "error_message": None,
        }
        if hlt_research_scope is not None:
            fields["hlt_research_scope"] = hlt_research_scope
        self.update_run(research_id, **fields)

    def fail_run(self, research_id: str, *, error_code: str = "error", error_message: str = "") -> None:
        self.update_run(
            research_id,
            status="failed",
            completed_at=utc_now_iso(),
            error_code=error_code,
            error_message=error_message,
        )

    def get_run(self, research_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM research_runs WHERE research_id = ?",
                (research_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def get_run_by_resource_topic(self, resource_topic: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM research_runs
                 WHERE resource_topic = ?
                 ORDER BY updated_at DESC
                 LIMIT 1
                """,
                (resource_topic,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_runs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM research_runs
                 ORDER BY updated_at DESC
                 LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["context"] = _json_load(data.get("context_json"), [])
        data["sources"] = _json_load(data.get("sources_json"), [])
        data["source_urls"] = _json_load(data.get("source_urls_json"), [])
        data["hlt_research_scope"] = _json_load(data.get("hlt_research_scope_json"), None)
        return data


_store_lock = threading.RLock()
_store: ResearchRunStore | None = None


def get_research_run_store(*, recover_interrupted: bool = True) -> ResearchRunStore:
    global _store
    path = get_research_run_store_path()
    with _store_lock:
        if _store is None or _store.path != path:
            _store = ResearchRunStore(path, recover_interrupted=recover_interrupted)
        return _store
