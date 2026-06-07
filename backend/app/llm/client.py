"""Thin, swappable LLM client.

Responsibilities (v1):
- Provider-agnostic surface: business logic calls :meth:`LLMClient.generate_json`
  and never touches a provider SDK. The only place a provider SDK is imported is
  inside the concrete provider classes in this module.
- JSON contract: every call requests JSON, parses it, and validates it against a
  caller-supplied Pydantic model.
- Repair-once-then-raise: on a parse/validation failure we retry exactly once with
  a repair instruction, then raise :class:`LLMError`.
- Structured logging: every provider call logs model, latency, and token usage,
  which sets up v2 observability cleanly.

Swap providers via ``LLM_PROVIDER`` / ``LLM_MODEL`` env vars (see app/config.py).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger("llm")

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when the LLM cannot produce valid, schema-conforming JSON."""


@dataclass(slots=True)
class _Completion:
    """Normalized provider response."""

    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class _Provider(Protocol):
    """Minimal contract every provider must satisfy."""

    model: str

    async def complete(self, *, system: str, prompt: str, temperature: float) -> _Completion: ...


# --------------------------------------------------------------------------- #
# Concrete providers (the ONLY place provider SDKs may be imported)
# --------------------------------------------------------------------------- #
class GroqProvider:
    """Groq provider via the ``groq`` SDK (OpenAI-style chat + JSON mode)."""

    def __init__(self, api_key: str, model: str) -> None:
        from groq import AsyncGroq  # imported lazily so other providers don't require it

        self._client = AsyncGroq(api_key=api_key)
        self.model = model

    async def complete(self, *, system: str, prompt: str, temperature: float) -> _Completion:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        usage = getattr(response, "usage", None)
        return _Completion(
            text=response.choices[0].message.content or "",
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
        )


class GeminiProvider:
    """Google Gemini provider via the ``google-genai`` SDK."""

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai  # imported lazily so other providers don't require it

        self._client = genai.Client(api_key=api_key)
        self.model = model

    async def complete(self, *, system: str, prompt: str, temperature: float) -> _Completion:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            response_mime_type="application/json",
        )
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        usage = getattr(response, "usage_metadata", None)
        return _Completion(
            text=response.text or "",
            prompt_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            completion_tokens=getattr(usage, "candidates_token_count", 0) or 0,
            total_tokens=getattr(usage, "total_token_count", 0) or 0,
        )


def _build_provider() -> _Provider:
    """Construct the configured provider. Add new providers here behind the env switch."""
    provider = settings.llm_provider.lower()
    if provider == "groq":
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY is not set; cannot construct the Groq provider.")
        return GroqProvider(api_key=settings.groq_api_key, model=settings.llm_model)
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMError("GEMINI_API_KEY is not set; cannot construct the Gemini provider.")
        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.llm_model)
    raise LLMError(
        f"Unsupported LLM_PROVIDER {settings.llm_provider!r}. v1 supports: 'groq', 'gemini'."
    )


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #
class LLMClient:
    """Provider-agnostic client that returns validated Pydantic models."""

    def __init__(self, provider: _Provider | None = None) -> None:
        self._provider = provider or _build_provider()

    async def generate_json(
        self,
        *,
        prompt: str,
        response_model: type[T],
        system: str = "",
        temperature: float | None = None,
    ) -> T:
        """Call the LLM and return an instance of ``response_model``.

        Retries once with a repair instruction on parse/validation failure, then
        raises :class:`LLMError`.
        """
        temp = settings.llm_temperature if temperature is None else temperature

        completion = await self._call(system=system, prompt=prompt, temperature=temp, attempt=1)
        try:
            return self._parse(completion.text, response_model)
        except (json.JSONDecodeError, ValidationError) as first_error:
            logger.warning(
                "llm.json_invalid",
                extra={"model": self._provider.model, "error": str(first_error)},
            )
            # --- single repair attempt (deterministic) ---
            repair_prompt = self._build_repair_prompt(
                original_prompt=prompt,
                bad_output=completion.text,
                error=first_error,
                response_model=response_model,
            )

        repaired = await self._call(system=system, prompt=repair_prompt, temperature=0.0, attempt=2)
        try:
            return self._parse(repaired.text, response_model)
        except (json.JSONDecodeError, ValidationError) as second_error:
            raise LLMError(
                f"LLM failed to produce valid {response_model.__name__} JSON after repair: "
                f"{second_error}"
            ) from second_error

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #
    async def _call(
        self, *, system: str, prompt: str, temperature: float, attempt: int
    ) -> _Completion:
        start = time.perf_counter()
        completion = await self._provider.complete(
            system=system, prompt=prompt, temperature=temperature
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "llm.call",
            extra={
                "model": self._provider.model,
                "attempt": attempt,
                "temperature": temperature,
                "latency_ms": latency_ms,
                "prompt_tokens": completion.prompt_tokens,
                "completion_tokens": completion.completion_tokens,
                "total_tokens": completion.total_tokens,
            },
        )
        return completion

    @staticmethod
    def _parse(text: str, response_model: type[T]) -> T:
        payload = _strip_code_fences(text).strip()
        if not payload:
            raise json.JSONDecodeError("empty LLM response", payload, 0)
        data = json.loads(payload)
        return response_model.model_validate(data)

    @staticmethod
    def _build_repair_prompt(
        *,
        original_prompt: str,
        bad_output: str,
        error: Exception,
        response_model: type[T],
    ) -> str:
        schema = json.dumps(response_model.model_json_schema(), indent=2)
        return (
            "Your previous response was not valid JSON for the required schema.\n\n"
            f"Required JSON schema for {response_model.__name__}:\n{schema}\n\n"
            f"Validation error:\n{error}\n\n"
            f"Your previous (invalid) output:\n{bad_output}\n\n"
            "Return ONLY a corrected JSON object that satisfies the schema. "
            "No prose, no markdown, no code fences.\n\n"
            f"Original request:\n{original_prompt}"
        )


def _strip_code_fences(text: str) -> str:
    """Remove a surrounding ```json ... ``` fence if the model added one."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else stripped[3:]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped


@lru_cache
def get_llm_client() -> LLMClient:
    """Return the cached, process-wide LLM client."""
    return LLMClient()
