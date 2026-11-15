from __future__ import annotations

import json
import urllib.error
import urllib.request


class KitKatAI:
    """Small local language-model client using Ollama's localhost API."""

    def __init__(self, model: str = "qwen2.5:1.5b", host: str = "http://127.0.0.1:11434"):
        self.model = model
        self.endpoint = host.rstrip("/") + "/api/chat"

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.75,
                "top_p": 0.9,
                "num_ctx": 4096,
            },
            "keep_alive": "10m",
        }).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Ollama is not responding at 127.0.0.1:11434. Start the Ollama app first."
            ) from exc
        except TimeoutError as exc:
            raise RuntimeError("The local model took too long to respond. Try a shorter message.") from exc

        message = result.get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama returned an empty response.")
        return content.strip()
