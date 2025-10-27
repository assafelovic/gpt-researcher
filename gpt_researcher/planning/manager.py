from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional


class PlanManager:
    def __init__(
        self,
        query: str,
        token_limit: Optional[float] = None,
        web_limit: Optional[int] = None,
        cost_limit: Optional[float] = None,
    ) -> None:
        self.query = query
        self.created_at = datetime.utcnow().isoformat()
        self.steps: list[Dict[str, object]] = []
        self.budgets: Dict[str, Dict[str, Optional[float]]] = {
            "tokens": {"limit": token_limit, "used": 0.0},
            "web_calls": {"limit": web_limit, "used": 0.0},
            "cost": {"limit": cost_limit, "used": 0.0},
        }

    def add_step(self, query: str, rationale: str) -> Dict[str, object]:
        step = {"query": query, "rationale": rationale, "status": "pending"}
        step["created_at"] = datetime.utcnow().isoformat(); step["metadata"] = {}
        self.steps.append(step)
        return step

    def update_step(self, query: str, status: str, metadata: Optional[Dict[str, object]] = None) -> None:
        for step in self.steps:
            if step["query"] == query:
                step["status"] = status
                if metadata:
                    step["metadata"].update(metadata)
                break

    def record_usage(self, budget_name: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("Budget usage must be non-negative")
        budget = self.budgets.setdefault(budget_name, {"limit": None, "used": 0.0})
        budget["used"] = float(budget.get("used", 0.0)) + float(amount)

    def should_halt(self, enforce: bool = False) -> bool:
        return bool(enforce and any(
            b["limit"] is not None and b.get("used", 0.0) >= b["limit"]
            for b in self.budgets.values()
        ))

    def get_trace(self) -> Dict[str, object]:
        def summary(budget: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
            limit = budget["limit"]; used = budget.get("used", 0.0)
            return {
                "limit": limit,
                "used": used,
                "remaining": None if limit is None else max(limit - used, 0.0),
                "exhausted": limit is not None and used >= limit,
            }
        return {
            "query": self.query,
            "created_at": self.created_at,
            "steps": list(self.steps),
            "budgets": {name: summary(budget) for name, budget in self.budgets.items()},
        }
