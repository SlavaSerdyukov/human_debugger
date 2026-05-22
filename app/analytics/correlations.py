from math import sqrt
from statistics import mean

from app.models import Entry, Project


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None

    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
    x_part = sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_part = sqrt(sum((y - y_mean) ** 2 for y in ys))
    if x_part == 0 or y_part == 0:
        return None
    return round(numerator / (x_part * y_part), 2)


def correlations(entries: list[Entry], projects: list[Project]) -> dict[str, float | None]:
    ordered_entries = sorted(entries, key=lambda entry: entry.date)
    logs = [log for project in projects for log in project.logs]
    logs_by_date = {log.date: log for log in logs}
    joined = [(entry, logs_by_date[entry.date]) for entry in ordered_entries if entry.date in logs_by_date]
    return {
        "sleep_hours_vs_focus": pearson(
            [entry.sleep_hours for entry in ordered_entries],
            [entry.focus for entry in ordered_entries],
        ),
        "stress_vs_focus": pearson(
            [entry.stress for entry in ordered_entries],
            [entry.focus for entry in ordered_entries],
        ),
        "energy_vs_progress_score": pearson(
            [entry.energy for entry, _ in joined],
            [log.progress_score for _, log in joined],
        ),
    }
