from datetime import date, timedelta
from statistics import mean
from typing import Any

from app.analytics.trends import trend_for
from app.models import Entry

CORE_METRICS = ("mood", "energy", "focus", "stress")


def split_tags(tags: str) -> list[str]:
    return [tag.strip().lower() for tag in tags.replace("#", "").split(",") if tag.strip()]


def average(values: list[float]) -> float | None:
    return round(mean(values), 2) if values else None


def rolling_averages(entries: list[Entry], window: int = 3) -> dict[str, list[dict[str, float | str | None]]]:
    ordered = sorted(entries, key=lambda entry: entry.date)
    result: dict[str, list[dict[str, float | str | None]]] = {metric: [] for metric in CORE_METRICS}
    if window <= 0:
        return result

    for index, entry in enumerate(ordered):
        scoped = ordered[max(0, index - window + 1) : index + 1]
        for metric in CORE_METRICS:
            values = [float(getattr(item, metric)) for item in scoped]
            result[metric].append(
                {
                    "date": entry.date.isoformat(),
                    "value": average(values),
                    "sample_size": len(values),
                }
            )
    return result


def metric_summary(entries: list[Entry], today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    ordered = sorted(entries, key=lambda entry: entry.date)
    result: dict[str, Any] = {}

    for window in (7, 30):
        cutoff = today - timedelta(days=window - 1)
        scoped = [entry for entry in ordered if entry.date >= cutoff]
        result[f"last_{window}_days"] = {
            "count": len(scoped),
            "mood": average([entry.mood for entry in scoped]),
            "energy": average([entry.energy for entry in scoped]),
            "focus": average([entry.focus for entry in scoped]),
            "stress": average([entry.stress for entry in scoped]),
        }

    result["trends"] = {
        "mood": trend_for([entry.mood for entry in ordered]).__dict__,
        "energy": trend_for([entry.energy for entry in ordered]).__dict__,
        "focus": trend_for([entry.focus for entry in ordered]).__dict__,
        "stress": trend_for([entry.stress for entry in ordered]).__dict__,
    }
    result["rolling"] = rolling_averages(ordered)
    return result
