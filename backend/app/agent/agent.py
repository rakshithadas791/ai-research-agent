"""
agent.py
--------
The orchestrator (Agent Controller in the architecture diagram). Combines
Planner + Executor + AgentState and emits events as it goes, so the API
layer can either wait for the final result (REST) or stream progress live
(WebSocket).
"""
from app.agent.state import AgentState, StepResult
from app.agent.planner import Planner
from app.agent.executor import Executor
from app.agent.reasoning import Reasoning
from app.services.report_service import save_report
from app.tools.database_tool import get_notes, save_note


class ResearchAgent:
    def __init__(self):
        reasoning = Reasoning()
        self.planner = Planner(reasoning)
        self.executor = Executor(reasoning)
        self.reasoning = reasoning

    def run(self, goal: str, on_event=None) -> AgentState:
        def emit(event_type, data):
            if on_event:
                on_event({"type": event_type, "data": data})

        state = AgentState(goal=goal)

        # 0. MEMORY: reuse prior notes so repeat runs can improve over time.
        emit("tool_call", {"step": 0, "tool": "get_notes", "input": {"topic": goal}})
        prior_notes = get_notes(goal)
        emit("observation", {"step": 0, "tool": "get_notes", "result": prior_notes[:500]})
        if not prior_notes.startswith("No notes found"):
            state.memory_context = prior_notes

        # 1. PLAN
        state.plan = self.planner.create_plan(goal, state.memory_context)
        emit("plan", state.plan)

        # 2-3. ACT + OBSERVE, per sub-task, grounded by state.context_so_far()
        for i, step in enumerate(state.plan, 1):
            emit("step_start", {"step": i, "instruction": step})

            answer, trace = self.executor.run_step(
                instruction=step,
                context_so_far=state.context_so_far(),
                on_event=lambda et, d, i=i: emit(et, {"step": i, **d}),
            )

            state.add_step_result(StepResult(i, step, trace, answer))
            emit("step_complete", {"step": i, "answer": answer})

        # 4. RESPOND: synthesize + persist
        emit("synthesizing", {})
        state.final_report = self.reasoning.synthesize(goal, state.context_so_far())
        state.report_path = save_report(goal, state.final_report)
        memory_note = _memory_note(state.final_report)
        emit("tool_call", {"step": 0, "tool": "save_note", "input": {"topic": goal}})
        note_result = save_note(goal, memory_note)
        emit("observation", {"step": 0, "tool": "save_note", "result": note_result})

        emit("done", {"report": state.final_report, "path": state.report_path})
        return state


def _memory_note(report: str, max_chars: int = 900) -> str:
    compact = " ".join(report.strip().split())
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rsplit(" ", 1)[0] + "..."
