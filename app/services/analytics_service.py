from typing import Any

from sqlalchemy.orm import Session

from app import analytics, llm
from app.services import entry_service, project_service


def build_report(session: Session) -> dict[str, Any]:
    entries = entry_service.list_entries(session)
    projects = project_service.list_projects(session)
    return analytics.build_debug_report(entries, projects)


def build_report_with_llm_summary(session: Session) -> tuple[dict[str, Any], dict[str, Any]]:
    report = build_report(session)
    return report, llm.summarize_report_with_llm(report)


def llm_status() -> dict[str, Any]:
    return llm.get_llm_status()
