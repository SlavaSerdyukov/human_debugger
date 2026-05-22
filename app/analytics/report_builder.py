from datetime import date
from typing import Any

from app.analytics.correlations import correlations
from app.analytics.metrics import metric_summary
from app.analytics.patterns import detect_entry_patterns, detect_project_patterns
from app.analytics.risk_engine import abandonment_risk
from app.analytics.semantic_memory import semantic_memory_summary
from app.models import Entry, Project


def behavior_loops(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [pattern for pattern in patterns if pattern.get("category") == "behavior_loop"]


def build_debug_report(entries: list[Entry], projects: list[Project], today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    metrics = metric_summary(entries, today)
    project_risks = [abandonment_risk(project, entries, today) for project in projects]
    patterns = detect_entry_patterns(entries) + detect_project_patterns(projects, entries, today)

    return {
        "title": "Human Debug Report",
        "generated_for": today.isoformat(),
        "data_state": "ready" if len(entries) >= 3 else "insufficient data",
        "system_status": {
            "focus": metrics["trends"]["focus"]["label"],
            "energy": metrics["trends"]["energy"]["label"],
            "stress": metrics["trends"]["stress"]["label"],
            "mood": metrics["trends"]["mood"]["label"],
        },
        "metrics": metrics,
        "correlations": correlations(entries, projects),
        "detected_patterns": patterns,
        "behavior_loops": behavior_loops(patterns),
        "semantic_memory": semantic_memory_summary(entries, projects),
        "project_risk": sorted(project_risks, key=lambda item: item["abandonment_risk"], reverse=True),
        "guardrail": "This is a local behavior debugging aid. It offers hypotheses and signals, not medical advice.",
    }
