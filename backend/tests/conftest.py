"""Shared test fixtures.

``make_client`` builds an LLMClient backed by a fake provider that returns a
scripted sequence of responses (dicts are JSON-encoded for you) and records the
prompts it received, so tests can assert on what the agent sent.
"""

from __future__ import annotations

import json

import pytest

from app.llm.client import LLMClient, _Completion


class RecordingProvider:
    """Fake provider: scripted responses + records system/prompt of each call."""

    model = "fake-model"

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls = 0
        self.prompts: list[str] = []
        self.systems: list[str] = []

    async def complete(self, *, system, prompt, temperature) -> _Completion:
        self.prompts.append(prompt)
        self.systems.append(system)
        text = self._responses[self.calls]
        self.calls += 1
        return _Completion(text=text, prompt_tokens=1, completion_tokens=1, total_tokens=2)


@pytest.fixture
def make_client():
    def _make(responses: list) -> tuple[LLMClient, RecordingProvider]:
        encoded = [r if isinstance(r, str) else json.dumps(r) for r in responses]
        provider = RecordingProvider(encoded)
        return LLMClient(provider=provider), provider

    return _make
