"""
tools/__init__.py
------------------
Combines every tool module into one dispatch table + one schema list, which
is all agent/executor.py needs to know about. Add a new tool by writing the
function in its own module, then adding one entry here.
"""
from app.tools.search_tool import web_search
from app.tools.calculator_tool import calculator
from app.tools.file_tool import read_file, write_file
from app.tools.database_tool import save_note, get_notes

TOOL_FUNCTIONS = {
    "web_search": web_search,
    "calculator": calculator,
    "read_file": read_file,
    "write_file": write_file,
    "save_note": save_note,
    "get_notes": get_notes,
}

TOOL_SCHEMAS = [
    {
        "name": "web_search",
        "description": "Search the web for up-to-date information on a topic. Returns numbered title/snippet results.",
        "input_schema": {"type": "object",
            "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4)'.",
        "input_schema": {"type": "object",
            "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
    },
    {
        "name": "read_file",
        "description": "Read text content from a local file (e.g. a dataset the user supplied).",
        "input_schema": {"type": "object",
            "properties": {"filename": {"type": "string"}}, "required": ["filename"]},
    },
    {
        "name": "write_file",
        "description": "Write text content to a file on disk.",
        "input_schema": {"type": "object",
            "properties": {"filename": {"type": "string"}, "content": {"type": "string"}},
            "required": ["filename", "content"]},
    },
    {
        "name": "save_note",
        "description": "Persist a fact you've found under a topic, so it can be retrieved later in this or a future run.",
        "input_schema": {"type": "object",
            "properties": {"topic": {"type": "string"}, "content": {"type": "string"}},
            "required": ["topic", "content"]},
    },
    {
        "name": "get_notes",
        "description": "Retrieve previously saved notes for a topic.",
        "input_schema": {"type": "object",
            "properties": {"topic": {"type": "string"}}, "required": ["topic"]},
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"[error] Unknown tool: {name}"
    return fn(**tool_input)
