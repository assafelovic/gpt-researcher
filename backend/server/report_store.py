import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List


class ReportStore:
    def __init__(self, path: Path):
        self._path = path
        self._lock = asyncio.Lock()

    async def _ensure_parent_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def _read_all_unlocked(self) -> Dict[str, Dict[str, Any]]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data  # type: ignore[return-value]
        except Exception:
            return {}
        return {}

    async def _write_all_unlocked(self, data: Dict[str, Dict[str, Any]]) -> None:
        await self._ensure_parent_dir()
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(self._path)

    async def list_reports(self, report_ids: List[str] | None = None) -> List[Dict[str, Any]]:
        async with self._lock:
            data = await self._read_all_unlocked()
            if report_ids is None:
                return list(data.values())
            return [data[report_id] for report_id in report_ids if report_id in data]

    async def get_report(self, report_id: str) -> Dict[str, Any] | None:
        async with self._lock:
            data = await self._read_all_unlocked()
            return data.get(report_id)

    async def upsert_report(self, report_id: str, report: Dict[str, Any]) -> None:
        async with self._lock:
            data = await self._read_all_unlocked()
            data[report_id] = report
            await self._write_all_unlocked(data)

    async def delete_report(self, report_id: str) -> bool:
        async with self._lock:
            data = await self._read_all_unlocked()
            existed = report_id in data
            if existed:
                del data[report_id]
                await self._write_all_unlocked(data)
            return existed
