"""
executor.py
-----------
Runs the ReAct loop (Thought -> Action -> Observation) for ONE sub-task,
until the model is confident it can give a final answer, or max_turns is hit.

`on_event` is an optional callback used to stream live progress (thought,
tool_call, observation) up to the API layer — this is what powers the
frontend's live execution dashboard.
"""
from app.agent.reasoning import Reasoning
from app.tools import TOOL_SCHEMAS, execute_tool


class Executor:
    def __init__(self, reasoning: Reasoning | None = None):
        self.reasoning = reasoning or Reasoning()

    def run_step(self, instruction: str, context_so_far: str, on_event=None, max_turns: int = 4):
        def emit(event_type, data):
            if on_event:
                on_event(event_type, data)

        messages = [{
            "role": "user",
            "content": f"Overall context so far:\n{context_so_far}\n\nCurrent sub-task: {instruction}",
        }]
        trace = []

        for _ in range(max_turns):
            resp = self.reasoning.react_turn(messages, TOOL_SCHEMAS)

            thought_text = "".join(b.text for b in resp.content if b.type == "text")
            tool_uses = [b for b in resp.content if b.type == "tool_use"]

            if thought_text:
                emit("thought", {"text": thought_text})

            if resp.stop_reason != "tool_use" or not tool_uses:
                trace.append({"thought": thought_text, "action": None,
                               "action_input": None, "observation": None})
                return self._extract_final(thought_text), trace

            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for tu in tool_uses:
                emit("tool_call", {"tool": tu.name, "input": tu.input})
                observation = execute_tool(tu.name, tu.input)
                emit("observation", {"tool": tu.name, "result": self._trim_for_display(observation)})
                trace.append({"thought": thought_text, "action": tu.name,
                               "action_input": tu.input, "observation": observation})
                tool_results.append({
                    "type": "tool_result", "tool_use_id": tu.id, "content": observation,
                })
            messages.append({"role": "user", "content": tool_results})

        # Turn budget exhausted without a FINAL ANSWER — force one more call
        # with NO tools available, so the model must answer using whatever
        # real observations it already gathered instead of giving up empty.
        emit("thought", {"text": "Turn budget reached — forcing a final answer from what's been gathered."})
        forced = self.reasoning.force_answer(messages)
        forced_text = "".join(b.text for b in forced.content if b.type == "text")
        trace.append({"thought": forced_text, "action": None, "action_input": None, "observation": None})
        return self._extract_final(forced_text), trace

    @staticmethod
    def _extract_final(text: str) -> str:
        final = text.strip()
        if final.upper().startswith("FINAL ANSWER:"):
            final = final.split(":", 1)[1].strip()
        return final or "(no answer produced)"

    @staticmethod
    def _trim_for_display(observation, limit: int = 900) -> str:
        """Truncate a tool observation for the live dashboard WITHOUT cutting
        mid-word/mid-line. A raw [:limit] slice (the previous approach) chops
        whichever result line straddles the boundary — this instead prefers
        cutting at the last complete line, falling back to the last space."""
        text = str(observation)
        if len(text) <= limit:
            return text

        cut = text[:limit]
        last_newline = cut.rfind("\n")
        if last_newline > limit * 0.4:
            return cut[:last_newline].rstrip() + "\n…"

        last_space = cut.rfind(" ")
        if last_space > 0:
            cut = cut[:last_space]
        return cut.rstrip() + "…"