"""Loader failure log must include the real extension, not always HTML."""

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "gpt_researcher" / "document" / "document.py"


def test_error_message_uses_file_extension():
    text = SRC.read_text(encoding="utf-8")
    assert "Failed to load HTML document" not in text
    assert "file_extension or 'unknown'" in text or 'file_extension or "unknown"' in text
