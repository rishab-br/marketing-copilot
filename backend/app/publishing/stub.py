"""Stub publisher — simulates posting without hitting any real platform API.

Used by default (PUBLISHING_MODE=stub) so the app works out-of-the-box without
OAuth credentials. Generates deterministic-ish fake post IDs and URLs so tests
and demos are predictable. Swap to a real publisher via the registry without
touching any other code.
"""

from __future__ import annotations

import uuid

from app.models import Asset
from app.publishing.base import PublisherBase


class StubPublisher(PublisherBase):
    name = "stub"

    def __init__(self, platform: str) -> None:
        self._platform = platform

    async def post(self, asset: Asset) -> tuple[str, str | None]:
        post_id = uuid.uuid4().hex[:12]
        url = f"https://stub.example/{self._platform}/{post_id}"
        return post_id, url

    async def get_status(self, post_id: str) -> tuple[str, str | None]:
        # Stub posts are always "published" once created.
        url = f"https://stub.example/{self._platform}/{post_id}"
        return "published", url
