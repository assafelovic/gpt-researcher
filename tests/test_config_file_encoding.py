"""UTF-8 configuration values must not depend on the system locale."""

import builtins
import json
from functools import partial

import pytest

import gpt_researcher.config.config as config_module
from gpt_researcher.config.config import Config


@pytest.mark.parametrize("locale_encoding", ["utf-8", "cp1252", "gbk"])
def test_load_config_preserves_utf8_values(tmp_path, monkeypatch, locale_encoding):
    values = {"LANGUAGE": "Español", "AGENT_ROLE": "中文研究员"}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(values, ensure_ascii=False), encoding="utf-8")
    # Model the default encoding on non-UTF-8 systems while reading a real file.
    monkeypatch.setattr(
        config_module,
        "open",
        partial(builtins.open, encoding=locale_encoding),
        raising=False,
    )

    loaded = Config.load_config(str(path))

    assert loaded["LANGUAGE"] == values["LANGUAGE"]
    assert loaded["AGENT_ROLE"] == values["AGENT_ROLE"]
