from typing import Any

from app.llm.config import get_ollama_settings
from app.llm.ollama_client import OllamaClient
from app.llm.prompts import build_summary_prompt


def get_llm_status(client: OllamaClient | None = None) -> dict[str, Any]:
    settings = get_ollama_settings()
    client = client or OllamaClient(base_url=settings.base_url, timeout=settings.timeout)
    return client.status(configured_model=settings.model)


def summarize_report_with_llm(
    report_data: dict[str, Any],
    model: str | None = None,
    client: OllamaClient | None = None,
) -> dict[str, Any]:
    settings = get_ollama_settings()
    selected_model = model or settings.model
    client = client or OllamaClient(base_url=settings.base_url, timeout=settings.timeout)
    try:
        summary = client.generate(build_summary_prompt(report_data), model=selected_model)
        return {
            "available": True,
            "base_url": client.base_url,
            "model": selected_model,
            "summary": summary,
            "raw_journal_sent": False,
        }
    except Exception as exc:
        return {
            "available": False,
            "base_url": client.base_url,
            "model": selected_model,
            "summary": "LLM layer offline. Deterministic report is available.",
            "error": exc.__class__.__name__,
            "raw_journal_sent": False,
        }
