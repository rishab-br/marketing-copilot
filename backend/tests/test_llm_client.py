"""Tests for the LLM client's JSON contract: parse, repair-once, then raise.

These use a fake provider so no network/API key is needed — the point is to lock
in the parsing + repair-then-raise behaviour, which is a guardrail in its own right.
"""

import pytest
from pydantic import BaseModel

from app.llm.client import LLMClient, LLMError, _Completion


class _Sample(BaseModel):
    name: str
    count: int


class FakeProvider:
    """Returns a scripted sequence of raw text responses, one per call."""

    model = "fake-model"

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls = 0

    async def complete(self, *, system, prompt, temperature) -> _Completion:
        text = self._responses[self.calls]
        self.calls += 1
        return _Completion(text=text, prompt_tokens=1, completion_tokens=1, total_tokens=2)


async def test_parses_valid_json_first_try():
    provider = FakeProvider(['{"name": "spring-sale", "count": 3}'])
    client = LLMClient(provider=provider)

    result = await client.generate_json(prompt="x", response_model=_Sample)

    assert result == _Sample(name="spring-sale", count=3)
    assert provider.calls == 1  # no repair needed


async def test_strips_code_fences():
    provider = FakeProvider(['```json\n{"name": "a", "count": 1}\n```'])
    client = LLMClient(provider=provider)

    result = await client.generate_json(prompt="x", response_model=_Sample)

    assert result == _Sample(name="a", count=1)


async def test_repairs_once_then_succeeds():
    provider = FakeProvider(
        [
            "not json at all",  # first attempt fails
            '{"name": "ok", "count": 2}',  # repair attempt succeeds
        ]
    )
    client = LLMClient(provider=provider)

    result = await client.generate_json(prompt="x", response_model=_Sample)

    assert result == _Sample(name="ok", count=2)
    assert provider.calls == 2  # exactly one repair


async def test_raises_after_failed_repair():
    provider = FakeProvider(["garbage", "still garbage"])
    client = LLMClient(provider=provider)

    with pytest.raises(LLMError):
        await client.generate_json(prompt="x", response_model=_Sample)

    assert provider.calls == 2  # tried once, repaired once, then gave up
