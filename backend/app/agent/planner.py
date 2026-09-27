"""planner.py — turns a goal into an ordered list of sub-tasks (Plan-and-Execute)."""
from app.agent.reasoning import Reasoning


class Planner:
    def __init__(self, reasoning: Reasoning | None = None):
        self.reasoning = reasoning or Reasoning()

    def create_plan(self, goal: str, prior_context: str = "") -> list[str]:
        return self.reasoning.plan(goal, prior_context)
