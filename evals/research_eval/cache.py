"""
Scoring-side cache: one SQLite file, stdlib only.
------------------------------------------------
The agent cannot be replayed, so reproducibility is guaranteed on the scoring
side: the same archive scored twice must give the same numbers. Every LLM and
embedding result is stored under a key that pins everything that could change
it, and read back on the next run.

Namespaces (eval-design/infrastructure.md §5):

  question   per-question artefacts (key points), keyed by
             question_id + prompt version + judge model
  domain     source-authority verdicts, keyed by domain + prompt version
  llm        every judge response, keyed by hash(model + prompt version +
             full input + parameters)
  embedding  embedding vectors, keyed by model + hash(text)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

DEFAULT_CACHE_PATH = Path(__file__).parent / "cache" / "research_eval.sqlite"


def stable_hash(*parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EvalCache:
    def __init__(self, path: str | Path = DEFAULT_CACHE_PATH) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            " namespace TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,"
            " created_at REAL NOT NULL, PRIMARY KEY (namespace, key))")
        self._db.commit()

    def get(self, namespace: str, key: str) -> Any | None:
        with self._lock:
            row = self._db.execute(
                "SELECT value FROM cache WHERE namespace = ? AND key = ?",
                (namespace, key)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, namespace: str, key: str, value: Any) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO cache (namespace, key, value, created_at)"
                " VALUES (?, ?, ?, ?)",
                (namespace, key, json.dumps(value, ensure_ascii=False), time.time()))
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()
