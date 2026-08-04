SUPPORTED_REPORT_LANGUAGES = frozenset({"Chinese (Simplified)", "English"})


def normalize_report_language(language: object) -> str | None:
    if not isinstance(language, str):
        return None

    normalized = language.strip()
    return normalized if normalized in SUPPORTED_REPORT_LANGUAGES else None
