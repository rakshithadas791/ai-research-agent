"""
services/report_service.py
---------------------------
Service layer between the agent/API and the raw tools — saves a finished
report to disk (via the file tool) and records it in the reports table
(via the database tool), and exposes read helpers for the history endpoints.
"""
from app.tools.file_tool import write_file
from app.tools.database_tool import save_report_record, list_report_records, get_report_record


def save_report(goal: str, content: str) -> str:
    safe_name = "".join(c if c.isalnum() else "_" for c in goal)[:50]
    filename = f"{safe_name or 'report'}.md"
    path = write_file(filename, content)
    save_report_record(goal, content, path)
    return path


def list_reports():
    return list_report_records()


def get_report(report_id: int):
    return get_report_record(report_id)
