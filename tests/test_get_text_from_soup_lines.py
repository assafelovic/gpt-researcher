from __future__ import annotations
import importlib.util
from pathlib import Path

from bs4 import BeautifulSoup


def _load():
    path = Path(__file__).resolve().parents[1] / "gpt_researcher" / "scraper" / "utils.py"
    spec = importlib.util.spec_from_file_location("su", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _scraped_text(markup: str) -> str:
    """Run markup through the same steps as the BeautifulSoup scraper."""
    su = _load()
    return su.get_text_from_soup(su.clean_soup(BeautifulSoup(markup, "lxml")))


def test_inline_elements_stay_in_their_line():
    markup = (
        "<h1>Setup</h1>"
        '<p>Read the <a href="/docs">setup guide</a> before you start. It is un<b>believ</b>able.</p>'
        "<p>Do <em>not</em> delete the <code>data</code> folder.</p>"
        "<p>Wrapped\nsource line</p>"
        "<ul><li>Alpha <b>one</b></li><li>Beta</li></ul>"
        "<table><tr><td>Apple <i>red</i></td><td>3</td></tr></table>"
        "<p>Line one<br>Line two</p>"
        "<div><button>Save</button><button>Cancel</button></div>"
    )
    assert _scraped_text(markup).split("\n") == [
        "Setup",
        "Read the setup guide before you start. It is unbelievable.",
        "Do not delete the data folder.",
        "Wrapped source line",
        "Alpha one",
        "Beta",
        "Apple red",
        "3",
        "Line one",
        "Line two",
        "Save Cancel",
    ]


def test_preformatted_text_keeps_its_line_breaks():
    markup = "<p>Example:</p><pre>first line\nsecond line</pre><p>Done.</p>"
    assert _scraped_text(markup) == "Example:\nfirst line\nsecond line\nDone."


def test_script_style_and_comment_text_is_not_page_text():
    markup = "<p>Visible</p><script>var hidden = 1;</script><style>p { color: red; }</style><!-- note -->"
    assert _load().get_text_from_soup(BeautifulSoup(markup, "lxml")) == "Visible"


def test_deeply_nested_markup_is_extracted():
    markup = "<div>" * 5000 + "deep" + "</div>" * 5000
    assert _load().get_text_from_soup(BeautifulSoup(markup, "html.parser")) == "deep"
