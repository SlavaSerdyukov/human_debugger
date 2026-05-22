from datetime import date
from statistics import mean
from typing import Any

from app.analytics.metrics import split_tags
from app.models import Entry, Project

NEGATIVE_TAGS = {"stuck", "procrastination", "overwhelmed", "bored"}


def risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "elevated"
    if score >= 20:
        return "watch"
    return "low"


def abandonment_risk(project: Project, entries: list[Entry], today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    logs = sorted(project.logs, key=lambda log: log.date)
    risk = 0
    factors: list[str] = []

    if logs:
        days_since_log = (today - logs[-1].date).days
        if days_since_log > 7:
            added = min(30, (days_since_log - 7) * 4 + 10)
            risk += added
            factors.append(f"no logs for {days_since_log} days")

        recent_logs = logs[-3:]
        avg_friction = mean(log.friction_score for log in recent_logs)
        if avg_friction >= 7:
            risk += 20
            factors.append("high friction")
        if len(logs) >= 3 and logs[-3].progress_score > logs[-2].progress_score > logs[-1].progress_score:
            risk += 18
            factors.append("declining progress")
    else:
        days_since_create = (today - project.created_at.date()).days
        if days_since_create > 7:
            risk += 30
            factors.append(f"no logs for {days_since_create} days")

    recent_entries = sorted(entries, key=lambda entry: entry.date)[-7:]
    if recent_entries and mean(entry.focus for entry in recent_entries) <= 4:
        risk += 15
        factors.append("low focus")
    if recent_entries and mean(entry.energy for entry in recent_entries) <= 4:
        risk += 15
        factors.append("low energy")

    negative_count = sum(1 for entry in recent_entries for tag in split_tags(entry.tags) if tag in NEGATIVE_TAGS)
    if negative_count:
        risk += min(20, negative_count * 5)
        factors.append("negative tags present")

    if project.status in {"paused", "abandoned"}:
        risk += 10
        factors.append(f"project status is {project.status}")
    if project.status == "completed":
        risk = 0
        factors = ["project completed"]

    score = min(100, risk)
    return {
        "project": project.name,
        "project_id": project.id,
        "abandonment_risk": score,
        "risk_level": risk_level(score),
        "main_risk_factors": factors or ["no strong risk signals"],
    }
