"""
main.py
-------
FastAPI entry point.

Endpoints:
  POST /api/research         - run the agent synchronously, return the final result
  GET  /api/reports          - history of past runs (from SQLite)
  GET  /api/reports/{id}     - one past report in full
  WS   /ws/research          - run the agent and STREAM every plan/step/tool/report
                                event as it happens, for the live dashboard

The agent itself is synchronous (the Anthropic SDK call blocks), so the
websocket handler runs it in a thread pool executor and forwards events
into an asyncio.Queue that gets pushed to the client as they arrive.
"""
import asyncio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent.agent import ResearchAgent
from app.models.schemas import ResearchRequest
from app.services.report_service import list_reports, get_report

app = FastAPI(title="AI Research Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AI Research Agent API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    return {
        "mock_llm": os.environ.get("MOCK_LLM", "").lower() in {"1", "true", "yes"},
        "llm_provider": provider,
        "groq_key_present": bool(os.environ.get("GROQ_API_KEY")),
        "groq_model": os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


@app.post("/api/research")
def research(req: ResearchRequest):
    agent = ResearchAgent()
    state = agent.run(req.goal)
    return {
        "plan": state.plan,
        "final_report": state.final_report,
        "report_path": state.report_path,
    }


@app.get("/api/reports")
def reports():
    return list_reports()


@app.get("/api/reports/{report_id}")
def report(report_id: int):
    result = get_report(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@app.websocket("/ws/research")
async def ws_research(websocket: WebSocket):
    await websocket.accept()
    try:
        msg = await websocket.receive_json()
        goal = msg.get("goal", "")
        if not goal:
            await websocket.send_json({"type": "error", "data": {"message": "No goal provided"}})
            await websocket.close()
            return

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def on_event(event):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def run_agent():
            try:
                agent = ResearchAgent()
                agent.run(goal, on_event=on_event)
            except Exception as e:
                on_event({"type": "error", "data": {"message": str(e)}})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel: stop streaming

        loop.run_in_executor(None, run_agent)

        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)

    except WebSocketDisconnect:
        pass
