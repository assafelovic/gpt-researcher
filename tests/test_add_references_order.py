"""Regression tests for add_references deterministic ordering.

``visited_urls`` is a set, so iterating it directly makes the report's
References section order vary run-to-run. add_references must emit the URLs
in a stable (sorted) order.
"""

from gpt_researcher.actions.markdown_processing import add_references


def test_add_references_renders_in_sorted_order():
    urls = {"https://c.example", "https://a.example", "https://b.example"}
    out = add_references("# Report", urls)

    expected_tail = (
        "\n\n\n## References\n\n"
        "- [https://a.example](https://a.example)\n"
        "- [https://b.example](https://b.example)\n"
        "- [https://c.example](https://c.example)\n"
    )
    assert out == "# Report" + expected_tail


def test_add_references_stable_across_equivalent_sets():
    # Two sets built in different insertion orders are equal but may iterate
    # differently; the rendered references must be identical.
    urls1 = set()
    for u in ("https://z.example", "https://m.example", "https://a.example"):
        urls1.add(u)
    urls2 = set()
    for u in ("https://a.example", "https://z.example", "https://m.example"):
        urls2.add(u)

    assert add_references("# R", urls1) == add_references("# R", urls2)
