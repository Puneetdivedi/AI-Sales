import requests
from config import Config
from logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Small wrapper around a chat completion API."""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.last_error = ""
        self.enabled = self._is_enabled()

    def _is_enabled(self):
        if self.provider == "none":
            return False
        if self.provider == "openai_compatible":
            return bool(Config.API_KEY and Config.LLM_ENDPOINT and Config.LLM_MODEL)
        return False

    def status_line(self):
        if self.provider == "none":
            return "AI status: disabled (set LLM_PROVIDER=openai_compatible to enable)."
        if self.provider == "openai_compatible":
            if self.enabled:
                return "AI status: enabled (openai_compatible)."
            return "AI status: missing API_KEY / LLM_ENDPOINT / LLM_MODEL."
        return f"AI status: unknown provider '{self.provider}'."

    def complete(self, system_prompt, user_prompt):
        if not self.enabled:
            return None

        if self.provider == "openai_compatible":
            payload = {
                "model": Config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": Config.MAX_TOKENS,
                "temperature": Config.TEMPERATURE,
            }
            headers = {
                "Authorization": f"Bearer {Config.API_KEY}",
                "Content-Type": "application/json",
            }

            try:
                resp = requests.post(
                    Config.LLM_ENDPOINT, json=payload, headers=headers, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices")
                if not choices:
                    return None
                message = choices[0].get("message", {})
                content = message.get("content", "").strip()
                return content if content else None
            except Exception as exc:
                self.last_error = str(exc)
                logger.warning("LLM request failed: %s", exc)
                return None

        return None
