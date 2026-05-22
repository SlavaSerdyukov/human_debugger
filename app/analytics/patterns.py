from collections import Counter
from datetime import date
from statistics import mean
from typing import Any

from app.analytics.metrics import average, split_tags
from app.models import Entry, Project


def detect_declining_focus(entries: list[Entry]) -> dict[str, Any] | None:
    ordered = sorted(entries, key=lambda entry: entry.date)
    if len(ordered) < 3:
        return None

    tail = ordered[-3:]
    if tail[0].focus > tail[1].focus > tail[2].focus:
        return {
            "name": "Possible focus slide",
            "category": "focus",
            "evidence": [f"Focus moved {tail[0].focus} -> {tail[1].focus} -> {tail[2].focus}."],
            "interpretation": "There is a signal that attention is leaking across consecutive days.",
            "suggested_patch": "Protect one small deep-work block before reactive work.",
        }
    return None


def detect_entry_patterns(entries: list[Entry]) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    low_sleep_focus = [entry for entry in entries if entry.sleep_hours < 6 and entry.focus <= 4]
    if len(low_sleep_focus) >= 2:
        avg_focus = average([entry.focus for entry in low_sleep_focus])
        patterns.append(
            {
                "name": "Possible sleep-focus coupling",
                "category": "energy",
                "evidence": [
                    f"{len(low_sleep_focus)} entries combine sleep under 6h with focus at 4 or lower.",
                    f"Average focus on those days: {avg_focus}.",
                ],
                "interpretation": "Low sleep may be making deep work more expensive.",
                "suggested_patch": "After low-sleep nights, choose lighter execution or a 20-minute setup task.",
            }
        )

    tag_counts = Counter(tag for entry in entries for tag in split_tags(entry.tags))
    procrastination_count = tag_counts.get("procrastination", 0)
    if procrastination_count >= 3:
        patterns.append(
            {
                "name": "Possible procrastination loop",
                "category": "behavior_loop",
                "evidence": [f"The tag procrastination appears {procrastination_count} times."],
                "interpretation": "This looks like a repeated start-delay signal, not a character verdict.",
                "suggested_patch": "Define the next action so small it can be started in under 2 minutes.",
            }
        )

    stress_delay_loop = [
        entry
        for entry in entries
        if entry.stress >= 7 and entry.focus <= 4 and {"stuck", "procrastination"} & set(split_tags(entry.tags))
    ]
    if len(stress_delay_loop) >= 2:
        patterns.append(
            {
                "name": "Possible stress-delay loop",
                "category": "behavior_loop",
                "evidence": [
                    f"{len(stress_delay_loop)} entries combine high stress, low focus, and stuck/procrastination tags."
                ],
                "interpretation": "The system may be entering a loop where pressure increases while start friction rises.",
                "suggested_patch": "Lower the first step until it is almost mechanical, then log the friction score.",
            }
        )

    focus_slide = detect_declining_focus(entries)
    if focus_slide:
        patterns.append(focus_slide)
    return patterns


def detect_project_patterns(projects: list[Project], entries: list[Entry], today: date | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    patterns: list[dict[str, Any]] = []

    for project in projects:
        logs = sorted(project.logs, key=lambda log: log.date)
        if not logs:
            age_days = (today - project.created_at.date()).days
            if age_days >= 7 and project.status == "active":
                patterns.append(
                    {
                        "name": "Possible silent project",
                        "category": "project",
                        "project": project.name,
                        "evidence": [f"No progress logs for {age_days} days."],
                        "interpretation": "The project has no telemetry, so drift is harder to catch.",
                        "suggested_patch": "Add one project log, even if the score is low.",
                    }
                )
            continue

        days_since_log = (today - logs[-1].date).days
        if days_since_log > 7:
            patterns.append(
                {
                    "name": "Possible project drift",
                    "category": "project",
                    "project": project.name,
                    "evidence": [f"No project logs for {days_since_log} days."],
                    "interpretation": "Silence around an active project can be an early abandon signal.",
                    "suggested_patch": "Schedule a 15-minute re-entry task and log what blocks it.",
                }
            )

        if len(logs) >= 4:
            early_progress = mean(log.progress_score for log in logs[:2])
            recent_progress = mean(log.progress_score for log in logs[-2:])
            recent_friction = mean(log.friction_score for log in logs[-2:])
            if early_progress >= 7 and early_progress - recent_progress >= 3 and recent_friction >= 6:
                patterns.append(
                    {
                        "name": "Possible architecture euphoria drop",
                        "category": "behavior_loop",
                        "project": project.name,
                        "evidence": [
                            f"Early progress averaged {round(early_progress, 2)}.",
                            f"Recent progress averaged {round(recent_progress, 2)}.",
                            f"Recent friction averaged {round(recent_friction, 2)}.",
                        ],
                        "interpretation": "You may be getting more energy from planning than execution right now.",
                        "suggested_patch": "Define a tiny next action under 20 minutes.",
                    }
                )

        log_dates = {log.date for log in logs}
        joined_entries = [entry for entry in entries if entry.date in log_dates]
        low_progress_high_stress = [
            entry
            for entry in joined_entries
            if entry.stress >= 7 and any(log.date == entry.date and log.progress_score <= 4 for log in logs)
        ]
        if len(low_progress_high_stress) >= 2:
            patterns.append(
                {
                    "name": "Possible stress-progress collision",
                    "category": "project",
                    "project": project.name,
                    "evidence": [f"{len(low_progress_high_stress)} logged days combine high stress with low progress."],
                    "interpretation": "Stress may be crowding out project execution capacity.",
                    "suggested_patch": "Move project work earlier or reduce scope to a single verifiable step.",
                }
            )
    return patterns
