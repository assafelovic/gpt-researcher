"""Research safety mode configuration."""

from enum import Enum


class ResearchSafetyMode(str, Enum):
    TRANSPARENT = "TRANSPARENT"
    WARN_ONLY = "WARN_ONLY"
    STRICT = "STRICT"
