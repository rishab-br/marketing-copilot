"""Abstract publisher interface.

Each concrete publisher (stub, twitter, linkedin…) subclasses PublisherBase and
implements `post` and `get_status`. The rest of the system only depends on this
interface — swapping providers requires no changes to routes or orchestration.

Schedule semantics live at the API layer (store a PostRecord with status=pending,
scheduled_at set). A background worker (v2: APScheduler / Celery) picks those
records up and calls `post`. That separation keeps this interface simple.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Asset


class PublisherBase(ABC):
    """Stateless async publisher.  One instance per provider (or per test stub)."""

    # Short label used in logs ("stub", "twitter", "linkedin")
    name: str = "unknown"

    @abstractmethod
    async def post(self, asset: Asset) -> tuple[str, str | None]:
        """Publish *asset* immediately.

        Returns:
            (post_id, url) — post_id is the platform-assigned ID (or a local
            stub ID). url is the live permalink, or None if unavailable.
        Raises:
            PublishError on any non-retriable failure.
        """

    @abstractmethod
    async def get_status(self, post_id: str) -> tuple[str, str | None]:
        """Fetch the current status of *post_id* from the platform.

        Returns:
            (status_str, url | None) — status_str is one of the PostStatus values.
        """


class PublishError(RuntimeError):
    """Raised by a publisher when posting fails."""
