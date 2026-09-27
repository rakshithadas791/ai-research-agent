import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_reports_endpoint_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    assert resp.json() == []


def test_research_endpoint_mocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MOCK_LLM", "true")
    with patch("app.agent.reasoning.Reasoning.plan", return_value=["Step one"]), \
         patch("app.agent.reasoning.Reasoning.synthesize", return_value="# Report"), \
         patch("app.agent.executor.Executor.run_step", return_value=("mocked answer", [])):
        resp = client.post("/api/research", json={"goal": "test"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["final_report"] == "# Report"
        assert body["plan"] == ["Step one"]
