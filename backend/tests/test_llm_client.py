import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.llm.client import LLMClient


def test_mock_llm_plans_without_api_key(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")
    client = LLMClient()

    resp = client.chat(
        system="You are the planning module of an autonomous research agent.",
        messages=[{"role": "user", "content": "Goal: Research AI in agriculture"}],
    )

    assert resp.content[0].type == "text"
    assert "AI in agriculture" in resp.content[0].text


def test_mock_llm_requests_tool_before_answering(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")
    client = LLMClient()

    resp = client.chat(
        system="You are the execution module of an autonomous research agent.",
        messages=[{"role": "user", "content": "Current sub-task: Search for AI in agriculture"}],
        tools=[{"name": "web_search"}],
    )

    assert resp.stop_reason == "tool_use"
    assert resp.content[1].name == "web_search"


def test_real_mode_requires_api_key(monkeypatch):
    """Default provider is Groq (free tier) — it should require GROQ_API_KEY,
    not an Anthropic key, when neither MOCK_LLM nor LLM_PROVIDER is set."""
    monkeypatch.delenv("MOCK_LLM", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    try:
        LLMClient()
    except ValueError as exc:
        assert "GROQ_API_KEY is missing" in str(exc)
    else:
        raise AssertionError("LLMClient should require an API key in real mode")


def test_anthropic_mode_requires_its_own_key(monkeypatch):
    monkeypatch.delenv("MOCK_LLM", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    try:
        LLMClient()
    except ValueError as exc:
        assert "ANTHROPIC_API_KEY is missing" in str(exc)
    else:
        raise AssertionError("LLMClient should require an API key when LLM_PROVIDER=anthropic")
