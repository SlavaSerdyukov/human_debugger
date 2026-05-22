from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class Trend:
    label: str
    delta: float


def trend_for(values: list[float]) -> Trend:
    if len(values) < 3:
        return Trend("insufficient data", 0.0)

    midpoint = len(values) // 2
    first = mean(values[:midpoint])
    second = mean(values[midpoint:])
    delta = second - first

    if delta > 0.35:
        return Trend("improving", round(delta, 2))
    if delta < -0.35:
        return Trend("declining", round(delta, 2))
    return Trend("stable", round(delta, 2))
