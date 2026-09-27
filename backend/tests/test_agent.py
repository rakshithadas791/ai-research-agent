import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from app.agent.agent import ResearchAgent
from app.tools.database_tool import get_notes


def test_agent_run_end_to_end(tmp_path, monkeypatch):
    """Runs the full Plan -> Act -> Observe -> Respond loop with the LLM
    mocked out, so this test needs no API key and no network."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MOCK_LLM", "true")

    class FakeBlock:
        type = "text"
        text = "FINAL ANSWER: mocked finding"

    class FakeResp:
        content = [FakeBlock()]
        stop_reason = "end_turn"

    with patch("app.agent.reasoning.Reasoning.plan", return_value=["Step one", "Step two"]), \
         patch("app.agent.reasoning.Reasoning.react_turn", return_value=FakeResp()), \
         patch("app.agent.reasoning.Reasoning.synthesize", return_value="# Report\nDone."):

        agent = ResearchAgent()
        events = []
        state = agent.run("test goal", on_event=events.append)

        assert state.plan == ["Step one", "Step two"]
        assert len(state.step_results) == 2
        assert state.final_report == "# Report\nDone."
        assert os.path.exists(state.report_path)
        assert any(e["type"] == "done" for e in events)
        assert any(e["type"] == "step_complete" for e in events)
        assert any(
            e["type"] == "tool_call" and e["data"]["tool"] == "get_notes"
            for e in events
        )
        assert "Report Done." in get_notes("test goal")
