"""
Unified LLM client supporting multiple providers.
Configuration via environment variables (LLM_PROVIDER, LLM_API_KEY, LLM_MODEL).
"""

import os
import json
import time
import re
import logging
from urllib import request as urlrequest, error as urlerror
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client. Uses only stdlib urllib — no third-party HTTP libs."""

    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.model = os.environ.get("LLM_MODEL", "")
        self.timeout = int(os.environ.get("LLM_TIMEOUT", "25"))

        if not self.model:
            self.model = {
                "gemini": "gemini-2.5-flash",
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-sonnet-20241022",
                "deepseek": "deepseek-chat",
                "groq": "llama-3.1-70b-versatile",
                "openrouter": "anthropic/claude-3-haiku",
            }.get(self.provider, "gemini-2.5-flash")

        logger.info(f"LLM client initialized: {self.provider}/{self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def complete(self, prompt: str, system: str = "") -> str:
        """Call the LLM and return the raw response text."""
        start = time.time()
        try:
            dispatch = {
                "gemini": self._gemini,
                "openai": self._openai,
                "anthropic": self._anthropic,
                "deepseek": self._deepseek,
                "groq": self._groq,
                "openrouter": self._openrouter,
                "nvidia": self._nvidia,
            }
            fn = dispatch.get(self.provider)
            if fn is None:
                raise ValueError(f"Unknown provider: {self.provider}")

            result = fn(prompt, system)
            elapsed = time.time() - start
            logger.info(f"LLM call ({self.provider}/{self.model}): {elapsed:.1f}s, {len(result)} chars")
            return result

        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"LLM error ({self.provider}/{self.model}): {e} ({elapsed:.1f}s)")
            raise

    def complete_json(self, prompt: str, system: str = "") -> dict:
        """Call LLM and parse response as JSON. Retries once on parse failure."""
        for attempt in range(2):
            try:
                raw = self.complete(prompt, system)
                return self._extract_json(raw)
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == 0:
                    logger.warning(f"JSON parse failed (attempt 1), retrying: {e}")
                    prompt += (
                        "\n\nIMPORTANT: Your previous response was not valid JSON. "
                        "Respond with ONLY a valid JSON object. No markdown fences, no extra text."
                    )
                else:
                    logger.error(f"JSON parse failed after 2 attempts: {e}")
                    raise

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM output that may contain markdown or prose."""
        text = text.strip()
        # Strip markdown fences
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find first JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())

        raise ValueError(f"No JSON found in response: {text[:200]}")

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    def _openai_compat(self, url: str, prompt: str, system: str,
                       headers: dict) -> str:
        """Shared implementation for OpenAI-compatible APIs."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1500,
        }).encode("utf-8")

        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        req = urlrequest.Request(url, data=body, headers=headers)
        
        # Artificial delay
        time.sleep(1)
        
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _openai(self, prompt: str, system: str) -> str:
        return self._openai_compat(
            "https://api.openai.com/v1/chat/completions",
            prompt, system,
            {"Authorization": f"Bearer {self.api_key}"},
        )

    def _deepseek(self, prompt: str, system: str) -> str:
        return self._openai_compat(
            "https://api.deepseek.com/v1/chat/completions",
            prompt, system,
            {"Authorization": f"Bearer {self.api_key}"},
        )

    def _groq(self, prompt: str, system: str) -> str:
        return self._openai_compat(
            "https://api.groq.com/openai/v1/chat/completions",
            prompt, system,
            {"Authorization": f"Bearer {self.api_key}"},
        )

    def _nvidia(self, prompt: str, system: str) -> str:
        return self._openai_compat(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            prompt, system,
            {"Authorization": f"Bearer {self.api_key}"},
        )

    def _openrouter(self, prompt: str, system: str) -> str:
        return self._openai_compat(
            "https://openrouter.ai/api/v1/chat/completions",
            prompt, system,
            {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://magicpin.com",
            },
        )

    def _anthropic(self, prompt: str, system: str) -> str:
        body_dict: dict = {
            "model": self.model,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body_dict["system"] = system

        req = urlrequest.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body_dict).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
        )
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]

    def _gemini(self, prompt: str, system: str) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        body = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1500},
        }).encode("utf-8")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self.model}:generateContent?key={self.api_key}"
        )
        req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"})
        
        # Small delay for NVIDIA rate limits
        time.sleep(1)
        
        resp = urlrequest.urlopen(req, timeout=self.timeout)
        data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]
