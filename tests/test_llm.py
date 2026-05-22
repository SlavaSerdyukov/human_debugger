from typing import Any

from app.llm.prompts import build_summary_prompt, report_signal_payload
from app.llm.summarizer import get_llm_status, summarize_report_with_llm


class FakeOllamaClient:
    base_url = "http://fake-ollama.local"

    def __init__(self) -> None:
        self.prompt = ""
        self.model = ""

    def generate(self, prompt: str, model: str) -> str:
        self.prompt = prompt
        self.model = model
        return "Possible signal summary."

    def status(self, configured_model: str) -> dict[str, Any]:
        return {
            "available": True,
            "base_url": self.base_url,
            "configured_model": configured_model,
            "models": [configured_model],
            "model_available": True,
        }


def test_prompt_uses_signal_allowlist_without_raw_entries() -> None:
    report = {
        "title": "Human Debug Report",
        "entries": [{"text": "RAW JOURNAL TEXT SHOULD NEVER LEAVE"}],
        "metrics": {"last_7_days": {"focus": 4}, "last_30_days": {}, "trends": {}},
        "detected_patterns": [{"name": "Possible focus slide"}],
    }

    payload = report_signal_payload(report)
    prompt = build_summary_prompt(report)

    assert "entries" not in payload
    assert "RAW JOURNAL TEXT SHOULD NEVER LEAVE" not in prompt
    assert "Possible focus slide" in prompt


def test_summarizer_uses_configured_client_and_marks_privacy_boundary() -> None:
    client = FakeOllamaClient()

    result = summarize_report_with_llm({"title": "Human Debug Report"}, model="llama3.1", client=client)  # type: ignore[arg-type]

    assert result["available"] is True
    assert result["raw_journal_sent"] is False
    assert result["summary"] == "Possible signal summary."
    assert client.model == "llama3.1"


def test_llm_status_uses_client_without_generation() -> None:
    status = get_llm_status(client=FakeOllamaClient())  # type: ignore[arg-type]

    assert status["available"] is True
    assert status["model_available"] is True
