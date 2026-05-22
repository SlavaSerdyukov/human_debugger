from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 4.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_models(self) -> list[str]:
        response = httpx.get(f"{self.base_url}/api/tags", timeout=self.timeout)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        models = payload.get("models", [])
        return [str(item.get("name")) for item in models if item.get("name")]

    def status(self, configured_model: str) -> dict[str, Any]:
        try:
            models = self.list_models()
            return {
                "available": True,
                "base_url": self.base_url,
                "configured_model": configured_model,
                "models": models,
                "model_available": configured_model in models or any(name.startswith(f"{configured_model}:") for name in models),
            }
        except Exception as exc:
            return {
                "available": False,
                "base_url": self.base_url,
                "configured_model": configured_model,
                "models": [],
                "model_available": False,
                "error": exc.__class__.__name__,
            }

    def generate(self, prompt: str, model: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {"num_predict": 180},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        text = str(payload.get("response", "")).strip()
        if not text:
            raise ValueError("Empty Ollama response")
        return text
