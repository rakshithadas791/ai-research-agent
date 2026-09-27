"""state.py — carries context across every step of the workflow."""
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class StepResult:
    step_number: int
    instruction: str
    trace: list
    answer: str


@dataclass
class AgentState:
    goal: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    memory_context: str = ""
    plan: list = field(default_factory=list)
    step_results: list = field(default_factory=list)
    final_report: str = ""
    report_path: str = ""

    def add_step_result(self, result: StepResult):
        self.step_results.append(result)

    def context_so_far(self) -> str:
        sections = []
        if self.memory_context:
            sections.append(f"Relevant prior memory:\n{self.memory_context}")
        if self.step_results:
            sections.append(
                "\n\n".join(
                    f"Step {r.step_number} - {r.instruction}\nFinding: {r.answer}"
                    for r in self.step_results
                )
            )
        return "\n\n".join(sections) if sections else "(nothing gathered yet)"

    def to_dict(self):
        return {
            "goal": self.goal,
            "memory_context": self.memory_context,
            "plan": self.plan,
            "steps": [asdict(r) for r in self.step_results],
            "final_report": self.final_report,
            "report_path": self.report_path,
        }
