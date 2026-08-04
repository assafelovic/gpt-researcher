import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "gpt_researcher"
    / "utils"
    / "language.py"
)


def load_language_module():
    spec = importlib.util.spec_from_file_location("report_language", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReportLanguageTest(unittest.TestCase):
    def test_supported_languages_are_normalized(self):
        language = load_language_module()

        self.assertEqual(
            language.normalize_report_language(" Chinese (Simplified) "),
            "Chinese (Simplified)",
        )
        self.assertEqual(
            language.normalize_report_language(" English "),
            "English",
        )

    def test_unsupported_languages_fall_back(self):
        language = load_language_module()

        for value in (None, "", "French", 123):
            with self.subTest(value=value):
                self.assertIsNone(language.normalize_report_language(value))


if __name__ == "__main__":
    unittest.main()
