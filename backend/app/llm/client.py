"""
llm/client.py
-------------
LLM backend used by reasoning.py. Default provider is Groq, which runs
open-weight models (Llama 3.3 70B, etc.) on a genuinely free, no-card-required
tier — this satisfies the contest's "open-source models like LLaMA... are
encouraged for fairness" guidance without needing a paid Anthropic key.

Three modes, chosen by env vars:
  - MOCK_LLM=true          -> deterministic, zero-cost mock (unchanged from before)
  - LLM_PROVIDER=groq      -> free tier, default. Needs GROQ_API_KEY.
  - LLM_PROVIDER=anthropic -> paid, only if you explicitly want it back. Needs ANTHROPIC_API_KEY.

Whichever provider is used, chat() always returns the SAME shape (an
_LLMResponse with a .content list of _TextBlock/_ToolUseBlock and a
.stop_reason), so reasoning.py / executor.py never need to know which
backend actually answered.
"""
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(BACKEND_ENV)

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _ToolUseBlock:
    name: str
    input: dict
    id: str = "tool-call-1"
    type: str = "tool_use"


@dataclass
class _LLMResponse:
    content: list
    stop_reason: str = "end_turn"


class LLMClient:
    def __init__(self, api_key: str | None = None):
        self.mock_mode = os.environ.get("MOCK_LLM", "").lower() in {"1", "true", "yes"}
        self.provider = os.environ.get("LLM_PROVIDER", "groq").lower()

        if self.mock_mode:
            return

        if self.provider == "anthropic":
            self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            self.model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            if not self.api_key or self.api_key == "your-key-here":
                raise ValueError(
                    "ANTHROPIC_API_KEY is missing. Add it to backend/.env, "
                    "switch LLM_PROVIDER=groq for the free tier, or set MOCK_LLM=true."
                )
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        else:
            self.api_key = api_key or os.environ.get("GROQ_API_KEY")
            self.model = os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
            if not self.api_key or self.api_key == "your-groq-key-here":
                raise ValueError(
                    "GROQ_API_KEY is missing. Get a free key at console.groq.com "
                    "and add it to backend/.env, or set MOCK_LLM=true for offline dev."
                )

    def chat(self, system: str, messages: list, tools: list | None = None, max_tokens: int = 1000):
        if self.mock_mode:
            return self._mock_chat(system, messages, tools)
        if self.provider == "anthropic":
            return self._anthropic_chat(system, messages, tools, max_tokens)
        return self._groq_chat(system, messages, tools, max_tokens)

    # ---- Anthropic (paid, optional) ------------------------------------
    def _anthropic_chat(self, system, messages, tools, max_tokens):
        kwargs = dict(model=self.model, max_tokens=max_tokens, system=system, messages=messages)
        if tools:
            kwargs["tools"] = tools
        return self._client.messages.create(**kwargs)

    # ---- Groq (free, default) ------------------------------------------
    def _groq_chat(self, system, messages, tools, max_tokens):
        oa_messages = [{"role": "system", "content": system}]
        oa_messages.extend(self._to_openai_messages(messages))

        body = {
            "model": self.model,
            "messages": oa_messages,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = [self._to_openai_tool(t) for t in tools]

        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text[:300]}")

        choice = resp.json()["choices"][0]
        return self._from_openai_choice(choice)

    @staticmethod
    def _to_openai_tool(tool: dict) -> dict:
        """Anthropic tool schema -> OpenAI/Groq function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }

    @staticmethod
    def _to_openai_messages(messages: list) -> list:
        """Anthropic-shaped conversation history (as built by executor.py)
        -> OpenAI/Groq-shaped messages."""
        out = []
        for msg in messages:
            role, content = msg["role"], msg["content"]

            if isinstance(content, str):
                out.append({"role": role, "content": content})
                continue

            if role == "assistant":
                # content is a list of _TextBlock / _ToolUseBlock (or real
                # Anthropic content blocks with the same attribute names)
                text_parts = [b.text for b in content if getattr(b, "type", None) == "text"]
                tool_calls = [
                    {
                        "id": b.id,
                        "type": "function",
                        "function": {"name": b.name, "arguments": json.dumps(b.input)},
                    }
                    for b in content if getattr(b, "type", None) == "tool_use"
                ]
                assistant_msg = {"role": "assistant", "content": "".join(text_parts) or None}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                out.append(assistant_msg)
                continue

            if role == "user":
                # content is a list of {"type": "tool_result", "tool_use_id", "content"} dicts.
                # OpenAI/Groq wants each as its OWN "tool" role message.
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        out.append({
                            "role": "tool",
                            "tool_call_id": item["tool_use_id"],
                            "content": str(item.get("content", "")),
                        })
                continue

        return out

    @staticmethod
    def _from_openai_choice(choice: dict) -> _LLMResponse:
        message = choice["message"]
        blocks = []
        if message.get("content"):
            blocks.append(_TextBlock(message["content"]))
        tool_calls = message.get("tool_calls") or []
        for tc in tool_calls:
            try:
                args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                args = {}
            blocks.append(_ToolUseBlock(name=tc["function"]["name"], input=args, id=tc["id"]))

        stop_reason = "tool_use" if tool_calls else "end_turn"
        return _LLMResponse(content=blocks, stop_reason=stop_reason)

    # ---- Mock (free, offline, deterministic) ---------------------------
    def _mock_chat(self, system: str, messages: list, tools: list | None = None):
        """Small deterministic LLM substitute for demos/tests with no API key at all."""
        last_text = self._last_text(messages)

        if "planning module" in system:
            goal = last_text.split("Goal:", 1)[-1].strip().splitlines()[0] or "the requested topic"
            topic = self._topic(goal)
            plan = [
                f"Search for a high-level overview of {topic}",
                f"Find key benefits, limitations, and current trends for {topic}",
                f"Collect practical examples and credible source points about {topic}",
                f"Compare the findings and prepare a recommendation for {topic}",
            ]
            return _LLMResponse([_TextBlock(json.dumps(plan))])

        if "execution module" in system:
            if not self._has_tool_result(messages):
                instruction = self._current_instruction(last_text)
                return _LLMResponse(
                    [
                        _TextBlock("Thought: I need current external information before answering this sub-task."),
                        _ToolUseBlock("web_search", {"query": instruction}),
                    ],
                    stop_reason="tool_use",
                )
            observation = self._last_tool_observation(messages)
            return _LLMResponse([
                _TextBlock(
                    "FINAL ANSWER: The available evidence suggests that "
                    f"{self._summarize_observation(observation)}"
                )
            ])

        if "synthesis module" in system:
            goal = re.search(r"Original goal:\s*(.+)", last_text)
            title = goal.group(1).strip() if goal else "Research Report"
            return _LLMResponse([_TextBlock(self._mock_report(title, last_text))])

        return _LLMResponse([_TextBlock("FINAL ANSWER: Mock response.")])

    @staticmethod
    def _last_text(messages: list) -> str:
        for message in reversed(messages):
            content = message.get("content", "")
            if isinstance(content, str):
                return content
        return ""

    @staticmethod
    def _has_tool_result(messages: list) -> bool:
        for message in messages:
            content = message.get("content")
            if isinstance(content, list):
                if any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content):
                    return True
        return False

    @staticmethod
    def _last_tool_observation(messages: list) -> str:
        for message in reversed(messages):
            content = message.get("content")
            if isinstance(content, list):
                for item in reversed(content):
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        return str(item.get("content", ""))
        return ""

    @staticmethod
    def _current_instruction(text: str) -> str:
        match = re.search(r"Current sub-task:\s*(.+)", text, re.DOTALL)
        return match.group(1).strip() if match else text.strip()

    @staticmethod
    def _topic(goal: str) -> str:
        return re.sub(r"\s+", " ", goal).strip().strip(".")

    @staticmethod
    def _summarize_observation(observation: str) -> str:
        compact = re.sub(r"\s+", " ", observation).strip()
        if not compact:
            return "the search result was empty, so the agent should run a better targeted search in live mode."
        return compact[:450]

    @staticmethod
    def _mock_report(title: str, prompt_text: str) -> str:
        findings = prompt_text.split("Findings:", 1)[-1].strip()
        return (
            f"# {title}\n\n"
            "## Executive Summary\n"
            "This demo report was generated in MOCK_LLM mode, so the workflow can be shown "
            "without any API key. The agent still planned the task, called tools, observed "
            "results, preserved state, and synthesized the final output.\n\n"
            "## Findings\n"
            f"{findings}\n\n"
            "## Demo Note\n"
            "For final judging, switch MOCK_LLM to false (LLM_PROVIDER=groq with a free "
            "GROQ_API_KEY) to produce live-source output."
        )
