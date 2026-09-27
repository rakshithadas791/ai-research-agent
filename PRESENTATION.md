# AI Research Agent - 5 Slide Presentation

## Slide 1 - Problem Chosen

**AI Research & Report Generation Agent**

- User gives a topic or research goal.
- The system plans research steps, gathers information with tools, stores intermediate findings, and generates a final report.
- This solves a real student workflow: quickly creating a structured first draft for technical research.

## Slide 2 - Why This Is Agentic

- It does not send one prompt directly to the LLM.
- The agent follows a workflow: Plan -> Act -> Observe -> Update State -> Respond.
- The LLM decides whether it needs another tool call or can answer the current sub-task.
- State is carried across steps so later reasoning uses earlier findings.
- The system loads prior SQLite notes at the start and saves a new memory note after each report.

## Slide 3 - Architecture

```text
React Dashboard
      |
FastAPI WebSocket API
      |
ResearchAgent Orchestrator
      |
Planner -> Executor/ReAct Loop -> AgentState -> Synthesizer
      |
Tools: Web Search, Calculator, File Writer, SQLite Memory
```

## Slide 4 - Workflow Demo

Example input:

```text
Applications of computer vision in agriculture
```

Execution flow:

1. Memory loads prior notes for the goal.
2. Planner creates 3-5 research sub-tasks.
3. Executor runs a ReAct loop for each sub-task.
4. Tool calls return observations.
5. AgentState stores completed steps and findings.
6. Synthesizer writes the final Markdown report and saves a new memory note.

## Slide 5 - Results And Learning

- Full-stack system: React frontend + FastAPI backend.
- Core agent concepts demonstrated: reasoning, planning, tool use, execution, state, final synthesis.
- Repeat runs can reuse prior memory, showing how the agent improves with use.
- Tests cover tools, API, mock LLM behavior, and end-to-end agent flow.
- Demo mode allows presentation without paid API access; live mode can use Anthropic with an API key.
