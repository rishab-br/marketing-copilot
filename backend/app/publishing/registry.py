"""Publisher registry — maps platform names to publisher instances.

PUBLISHING_MODE controls which concrete publisher is used:
  stub  (default): StubPublisher for every platform — no API keys needed.
  real : platform-specific real publishers; falls back to stub if keys are absent.

Add new platforms here as one-liners; no changes needed elsewhere.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.publishing.base import PublisherBase
from app.publishing.stub import StubPublisher

logger = logging.getLogger("publishing.registry")


def _build_real(platform: str) -> PublisherBase:
    if platform in ("twitter", "x"):
        if all([
            settings.twitter_consumer_key,
            settings.twitter_consumer_secret,
            settings.twitter_access_token,
            settings.twitter_access_token_secret,
        ]):
            from app.publishing.twitter import TwitterPublisher  # noqa: PLC0415

            return TwitterPublisher(
                consumer_key=settings.twitter_consumer_key,
                consumer_secret=settings.twitter_consumer_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
            )
        logger.warning("twitter keys missing; falling back to stub for platform=%s", platform)

    if platform == "linkedin":
        if settings.linkedin_access_token and settings.linkedin_author_urn:
            from app.publishing.linkedin import LinkedInPublisher  # noqa: PLC0415

            return LinkedInPublisher(
                access_token=settings.linkedin_access_token,
                author_urn=settings.linkedin_author_urn,
            )
        logger.warning("linkedin keys missing; falling back to stub for platform=%s", platform)

    return StubPublisher(platform)


def get_publisher(platform: str) -> PublisherBase:
    """Return the appropriate publisher for *platform* given the current config."""
    if settings.publishing_mode == "real":
        return _build_real(platform)
    return StubPublisher(platform)
