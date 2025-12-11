# deep-research-align:A – Planning & Budget Layer
| Current | Proposed (Deep Research) |
| --- | --- |
| Planner returns string list only; no artifact. | `PlanManager` keeps structured steps + budgets with trace metadata. |
| Costs tracked post-hoc; no budgets or stops. | Configurable token/cost/web budgets with optional enforcement. |
| No plan trace or token accounting. | Plan trace persists to JSON/logs; tokens recorded with costs. |
Summary: `PlanManager` tracks steps and budgets and can emit plan traces without altering CLI/API behaviour.
Verify: `pip install pytest`; `pytest tests/test_plan_manager.py`
