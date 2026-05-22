from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1"
    timeout: float = 8.0


def get_ollama_settings() -> OllamaSettings:
    timeout_raw = getenv("OLLAMA_TIMEOUT", "8.0")
    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 8.0

    return OllamaSettings(
        base_url=getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=getenv("OLLAMA_MODEL", "llama3.1"),
        timeout=timeout,
    )
