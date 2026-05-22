from typing import Any
import json

LLM_GUARDRAILS = (
    "Rewrite this deterministic Human Debug Report in a friendly, direct, lightly cyberpunk tone. "
    "Return plain text only, no Markdown, headings, bullets, or formatting markers. "
    "Keep the response under 80 words. "
    "Do not add facts. Use only hypotheses, patterns, signals, possible risks, and suggested patches. "
    "Do not make medical claims. Do not use clinical framing. "
    "Never imply a condition or personal defect. "
    "You receive structured signals only, not raw journal entries."
)


def report_signal_payload(report_data: dict[str, Any]) -> dict[str, Any]:
    metrics = report_data.get("metrics", {})
    return {
        "title": report_data.get("title"),
        "generated_for": report_data.get("generated_for"),
        "data_state": report_data.get("data_state"),
        "system_status": report_data.get("system_status", {}),
        "metric_windows": {
            "last_7_days": metrics.get("last_7_days", {}),
            "last_30_days": metrics.get("last_30_days", {}),
            "trends": metrics.get("trends", {}),
        },
        "correlations": report_data.get("correlations", {}),
        "detected_patterns": report_data.get("detected_patterns", []),
        "behavior_loops": report_data.get("behavior_loops", []),
        "project_risk": report_data.get("project_risk", []),
        "semantic_memory": report_data.get("semantic_memory", {}),
        "guardrail": report_data.get("guardrail"),
    }


def build_summary_prompt(report_data: dict[str, Any]) -> str:
    payload = json.dumps(report_signal_payload(report_data), ensure_ascii=False, sort_keys=True)
    return f"{LLM_GUARDRAILS}\n\nStructured deterministic signals only:\n{payload}"
