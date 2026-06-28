"""Tests for image dimension parsing.

`parse_dimension` is called for every `<img>` width/height attribute during
scraping. Non-numeric values like '100%', 'auto', and '50em' are common and
valid HTML, but used to print an error line to stdout for each one, polluting
application output. It should parse numeric/px values and silently (debug-log)
return None for the rest.
"""

import logging
import unittest

from gpt_researcher.scraper.utils import parse_dimension


class TestParseDimension(unittest.TestCase):
    def test_plain_integer(self):
        self.assertEqual(parse_dimension("100"), 100)

    def test_px_suffix(self):
        self.assertEqual(parse_dimension("10px"), 10)

    def test_decimal_value(self):
        self.assertEqual(parse_dimension("409.12"), 409)

    def test_non_numeric_returns_none(self):
        for value in ("100%", "auto", "", "50em"):
            self.assertIsNone(parse_dimension(value))

    def test_non_numeric_does_not_write_to_stdout(self):
        # Regression: these used to print(...) one line per malformed value.
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            for value in ("100%", "auto", "50em"):
                parse_dimension(value)
        self.assertEqual(buf.getvalue(), "")

    def test_non_numeric_logs_at_debug(self):
        with self.assertLogs(level=logging.DEBUG) as captured:
            parse_dimension("100%")
        self.assertTrue(any("100%" in m for m in captured.output))


if __name__ == "__main__":
    unittest.main()
