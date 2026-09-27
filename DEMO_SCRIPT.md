# Demo Script - 2 To 5 Minutes

## 0:00 - 0:30 Introduction

"This project is an AI Research Agent. The contest asks for an agentic system, not a simple chatbot. So my system takes a research goal, checks prior memory, creates a plan, uses tools, observes results, stores state, and finally produces a structured report."

## 0:30 - 1:15 Architecture

"The frontend is built with React and shows the workflow live. The backend is FastAPI. Inside the backend, the ResearchAgent controls memory, planning, execution, state, and synthesis. The tools include web search, calculator, file writing, and SQLite memory."

Point to:

- `backend/app/agent/planner.py`
- `backend/app/agent/executor.py`
- `backend/app/agent/state.py`
- `backend/app/tools/`

## 1:15 - 3:30 Live Run

Run backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Run frontend:

```bash
cd frontend
npm run dev
```

Type:

```text
Applications of computer vision in agriculture
```

Explain while it runs:

"First, the agent checks SQLite memory for earlier notes on the same goal. Then the planner creates sub-tasks. The executor runs each step using a ReAct loop. When it needs information, it calls a tool. The observation comes back and becomes part of the agent state. The final report is only generated after all planned steps are completed, and then the agent saves a new memory note for future runs."

## 3:30 - 4:30 Output

Show:

- Plan panel
- Execution panel
- Tool Activity panel
- Sources panel
- Final report panel
- Saved report path

Say:

"This proves the system is not a one-shot prompt. It has workflow orchestration, conditional tool use, state management, persistent memory, and final synthesis."

## 4:30 - 5:00 Closing

"The tests use a mocked LLM so they can run without an API key. For classroom demonstration, MOCK_LLM mode is available. For the final contest video, I can use a real API key and live web search to generate the final report."
