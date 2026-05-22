from datetime import date, datetime, timedelta

from app.analytics import (
    abandonment_risk,
    build_debug_report,
    detect_declining_focus,
    detect_project_patterns,
    metric_summary,
    rolling_averages,
    semantic_memory_summary,
)
from app.llm import summarize_report_with_llm
from app.models import Entry, Project, ProjectLog


def entry(day: date, focus: int = 6, energy: int = 6, stress: int = 4, sleep: float = 7.0, tags: str = "") -> Entry:
    return Entry(
        id=1,
        date=day,
        text="signal",
        mood=6,
        energy=energy,
        focus=focus,
        stress=stress,
        sleep_hours=sleep,
        tags=tags,
        created_at=datetime.utcnow(),
    )


def test_metric_summary_calculates_averages() -> None:
    today = date(2026, 5, 17)
    entries = [
        entry(today - timedelta(days=1), focus=8, energy=6),
        entry(today, focus=4, energy=8),
    ]

    summary = metric_summary(entries, today=today)

    assert summary["last_7_days"]["focus"] == 6
    assert summary["last_7_days"]["energy"] == 7
    assert summary["last_30_days"]["count"] == 2


def test_detect_declining_focus() -> None:
    today = date(2026, 5, 17)
    entries = [
        entry(today - timedelta(days=2), focus=7),
        entry(today - timedelta(days=1), focus=5),
        entry(today, focus=3),
    ]

    pattern = detect_declining_focus(entries)

    assert pattern is not None
    assert pattern["name"] == "Possible focus slide"


def test_detection_project_without_logs() -> None:
    today = date(2026, 5, 17)
    project = Project(
        id=1,
        name="Quiet Project",
        description="",
        status="active",
        created_at=datetime(2026, 5, 1),
    )
    project.logs = []

    patterns = detect_project_patterns([project], [], today=today)

    assert patterns
    assert patterns[0]["name"] == "Possible silent project"


def test_abandonment_risk_uses_core_signals() -> None:
    today = date(2026, 5, 17)
    project = Project(
        id=1,
        name="Risky",
        description="",
        status="active",
        created_at=datetime(2026, 4, 20),
    )
    project.logs = [
        ProjectLog(project_id=1, date=today - timedelta(days=10), progress_score=7, friction_score=7),
        ProjectLog(project_id=1, date=today - timedelta(days=9), progress_score=5, friction_score=8),
        ProjectLog(project_id=1, date=today - timedelta(days=8), progress_score=3, friction_score=9),
    ]
    entries = [
        entry(today - timedelta(days=2), focus=3, energy=3, tags="stuck"),
        entry(today - timedelta(days=1), focus=4, energy=3, tags="procrastination"),
        entry(today, focus=3, energy=4, tags="overwhelmed"),
    ]

    risk = abandonment_risk(project, entries, today=today)

    assert risk["abandonment_risk"] >= 80
    assert "declining progress" in risk["main_risk_factors"]
    assert "high friction" in risk["main_risk_factors"]


def test_build_report_handles_empty_data() -> None:
    report = build_debug_report([], [], today=date(2026, 5, 17))

    assert report["data_state"] == "insufficient data"
    assert report["detected_patterns"] == []
    assert report["project_risk"] == []
    assert report["semantic_memory"]["embedding_model"] == "local-hash-v1"


def test_rolling_averages_expose_recent_signal() -> None:
    today = date(2026, 5, 17)
    entries = [
        entry(today - timedelta(days=2), focus=3),
        entry(today - timedelta(days=1), focus=6),
        entry(today, focus=9),
    ]

    rolling = rolling_averages(entries, window=3)

    assert rolling["focus"][-1]["value"] == 6
    assert rolling["focus"][-1]["sample_size"] == 3


def test_semantic_memory_uses_local_summary_without_raw_text() -> None:
    today = date(2026, 5, 17)
    entries = [
        entry(today - timedelta(days=1), tags="stuck, planning"),
        entry(today, tags="stuck, shipping"),
    ]

    memory = semantic_memory_summary(entries, [])

    assert memory["item_count"] == 2
    assert memory["top_tags"][0]["tag"] == "stuck"
    assert "raw" not in memory


def test_llm_fallback_without_ollama() -> None:
    result = summarize_report_with_llm({"title": "Human Debug Report"}, model="model-that-is-not-local")

    assert result["available"] is False
    assert "Deterministic report" in result["summary"]
