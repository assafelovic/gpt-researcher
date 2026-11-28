"""Bootstrap intervals, paired comparison and signal to noise over result records."""

import json
import math

from evals.research_eval import stats


def write(tmp_path, name, rows):
    d = tmp_path / name
    for run_id, qid, mode, value in rows:
        (d / run_id).mkdir(parents=True)
        rec = {"run_id": run_id, "question_id": qid, "mode": mode, "scored_at": "2026-11-20T00:00:00Z",
               "metrics": {"m": {"value": value, "higher_is_better": True}}}
        (d / run_id / "0.2+x.json").write_text(json.dumps(rec))
    return d


ROWS = [(f"r{q}{m}", f"q{q}", m, 0.5 + 0.1 * q + (0.05 if m == "deep" else 0))
        for q in range(5) for m in ("default", "deep")]


def test_interval_contains_mean_and_is_reproducible(tmp_path):
    recs = stats.load_results(write(tmp_path, "a", ROWS))
    rows = stats.summarize(recs, resamples=2000)
    allrow = next(r for r in rows if r["mode"] == "all")
    assert allrow["n"] == 10
    assert allrow["low"] <= allrow["mean"] <= allrow["high"]
    assert rows == stats.summarize(recs, resamples=2000)


def test_constant_values_give_a_zero_width_interval(tmp_path):
    recs = stats.load_results(write(tmp_path, "a", [(f"r{q}", f"q{q}", "default", 1.0) for q in range(4)]))
    r = stats.summarize(recs, resamples=500)[0]
    assert r["low"] == r["mean"] == r["high"] == 1.0


def test_paired_difference_detects_a_shift_and_ignores_none(tmp_path):
    base = stats.load_results(write(tmp_path, "a", ROWS))
    shifted = stats.load_results(write(tmp_path, "b", [(r, q, m, v + 0.1) for r, q, m, v in ROWS]))
    same = stats.load_results(write(tmp_path, "c", ROWS))
    d = next(r for r in stats.compare(base, shifted, resamples=1000) if r["mode"] == "all")
    assert math.isclose(d["diff"], 0.1) and d["differs"]
    d0 = next(r for r in stats.compare(base, same, resamples=1000) if r["mode"] == "all")
    assert d0["diff"] == 0 and not d0["differs"]


def test_signal_to_noise(tmp_path):
    main = stats.load_results(write(tmp_path, "a", ROWS))
    noisy = stats.load_results(write(tmp_path, "b", [(r, q, m, v + (0.02 if i % 2 else -0.02))
                                                      for i, (r, q, m, v) in enumerate(ROWS)]))
    s = stats.signal_to_noise(main, noisy)[0]
    assert s["n"] == 10 and s["snr"] > 2 and s["mdd"] > 0
