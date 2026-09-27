"""
reasoning.py
------------
All prompt engineering + raw LLM calls live here. planner.py and
executor.py both delegate to this module rather than building prompts
themselves, so the "what should the model be told" logic has one home.
"""
import json
from app.llm.client import LLMClient

PLANNER_SYSTEM = """You are the planning module of an autonomous research agent.
Given a user's goal, break it into 3-5 concrete, ordered sub-tasks that,
once all completed, fully satisfy the goal. Respond with ONLY a JSON array
of short strings, no prose, no markdown fences. Example:
["Search for X", "Compare Y and Z", "Summarize findings on W"]"""

REACT_SYSTEM = """You are the execution module of an autonomous research agent,
working on one sub-task at a time using the ReAct pattern (Thought, Action, Observation).

On each turn, first decide: do I already have enough information to answer this
sub-task, or do I need to gather more context with a tool?

- If you need more information, use web_search, read_file, get_notes, or save_note as appropriate.
- If you need computation, use calculator.
- If you call a tool, call exactly one tool.
- If you have enough, respond with plain text starting with "FINAL ANSWER:"
  followed by a concise, well-supported answer to the CURRENT SUB-TASK ONLY.

Keep this per-step answer SHORT — 2-4 sentences or a handful of short bullet
points, never a formatted table or a multi-section mini-report. This answer
gets carried forward as context for every later step and for the final
report, so a long answer here multiplies token cost across the whole run.
Save any polished formatting (tables, headings) for the final report, which
is written separately at the end from all steps' answers combined.

If a tool call fails or comes back with no useful data, do NOT immediately
retry the same tool with a slightly reworded query — that wastes turns and
tokens for very little gain. Instead, try at most ONE different tool or
angle, and if that also doesn't help, give your FINAL ANSWER using whatever
you do have, explicitly noting what you couldn't confirm. An honest,
partial answer beats an expensive, repetitive search loop.

Always ground your final answer in the tool observations you actually received —
never invent facts you did not look up or compute."""

SYNTHESIS_SYSTEM = """You are the synthesis module of an autonomous research agent.
You are given the original goal and the findings from each completed sub-task
(each finding is grounded only in real tool observations gathered earlier).

Write a single coherent Markdown report that fulfills the original goal,
using ONLY the findings you were actually given below. Do not invent named
studies, authors, publication years, percentages, statistics, or sources
that do not appear in the findings — if the findings are thin or general,
write a shorter, more general report rather than inventing specifics to
make it sound more authoritative. Fabricated citations are a serious
failure, worse than an honest, modest report.

Keep it reasonably concise (roughly 300-500 words, a few clear sections) —
this is a quick research summary, not an academic paper with a methodology
section or a references list. Use headings and bullet points where useful,
and write it as a finished report a human requested, not as an internal
execution log."""


class Reasoning:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()

    def plan(self, goal: str, prior_context: str = "") -> list[str]:
        user_prompt = f"Goal: {goal}"
        if prior_context:
            user_prompt += f"\n\nRelevant prior memory:\n{prior_context}"
        resp = self.llm.chat(
            system=PLANNER_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=500,
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return [line.strip("-* ") for line in text.splitlines() if line.strip()]

    def react_turn(self, messages: list, tools: list, max_tokens: int = 500):
        """One turn of the ReAct loop. Returns the raw Anthropic response —
        the executor decides what to do with tool_use blocks vs a final answer."""
        return self.llm.chat(system=REACT_SYSTEM, messages=messages, tools=tools, max_tokens=max_tokens)

    def force_answer(self, messages: list, max_tokens: int = 400):
        """Called when the turn budget for a sub-task runs out. No tools are
        offered, so the model CANNOT call another one — it must answer with
        whatever real observations are already in the conversation. This is
        the backstop for when the model keeps rewording searches instead of
        ever committing to a FINAL ANSWER."""
        nudge = {
            "role": "user",
            "content": (
                "You are out of tool calls for this sub-task. Do not attempt "
                "to call a tool. Using ONLY the real observations already "
                "above, give your FINAL ANSWER now (2-4 sentences). If the "
                "observations were thin, say plainly what is and isn't "
                "supported — do not invent anything to fill the gap."
            ),
        }
        return self.llm.chat(
            system=REACT_SYSTEM, messages=messages + [nudge], tools=None, max_tokens=max_tokens
        )

    def synthesize(self, goal: str, context_so_far: str) -> str:
        resp = self.llm.chat(
            system=SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": f"Original goal: {goal}\n\nFindings:\n{context_so_far}"}],
            max_tokens=2000,
        )
        return "".join(b.text for b in resp.content if b.type == "text")