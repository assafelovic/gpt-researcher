from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SafetyInfo:
    checked: bool = False
    mode: str = "TRANSPARENT"
    blocked: bool = False
    reason: Optional[str] = None
    action_taken: str = "proceeded_by_configuration"

    def to_dict(self) -> dict:
        return asdict(self)
