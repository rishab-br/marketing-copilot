"""Twitter / X publisher (API v2 via tweepy).

Requires four credentials in .env:
    TWITTER_CONSUMER_KEY
    TWITTER_CONSUMER_SECRET
    TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_TOKEN_SECRET

The tweepy client is synchronous; we run it in a thread pool via asyncio.to_thread
so it doesn't block the event loop.

Character limit: 280. We truncate body + cta + hashtags to fit, prioritising
the body then the CTA then hashtags (dropped if they'd overflow).
"""

from __future__ import annotations

import asyncio
import logging

from app.models import Asset
from app.publishing.base import PublishError, PublisherBase

logger = logging.getLogger("publishing.twitter")

_LIMIT = 280


def _compose(asset: Asset) -> str:
    parts = [asset.body]
    if asset.cta:
        parts.append(asset.cta)
    tags = " ".join(f"#{h}" for h in asset.hashtags)
    candidate = "\n\n".join(parts)
    if tags:
        candidate_with_tags = f"{candidate}\n\n{tags}"
        if len(candidate_with_tags) <= _LIMIT:
            return candidate_with_tags
    if len(candidate) <= _LIMIT:
        return candidate
    # Truncate body to fit within limit (leave room for "…")
    budget = _LIMIT - len("\n\n" + asset.cta) - 1 if asset.cta else _LIMIT - 1
    return asset.body[:budget] + "…"


class TwitterPublisher(PublisherBase):
    name = "twitter"

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        self._creds = (consumer_key, consumer_secret, access_token, access_token_secret)

    def _build_client(self):
        try:
            import tweepy  # noqa: PLC0415
        except ImportError as exc:
            raise PublishError("tweepy not installed; add it to pyproject.toml") from exc
        ck, cs, at, ats = self._creds
        return tweepy.Client(
            consumer_key=ck,
            consumer_secret=cs,
            access_token=at,
            access_token_secret=ats,
        )

    def _sync_post(self, text: str) -> tuple[str, str]:
        client = self._build_client()
        response = client.create_tweet(text=text)
        post_id = str(response.data["id"])
        url = f"https://twitter.com/i/web/status/{post_id}"
        return post_id, url

    async def post(self, asset: Asset) -> tuple[str, str | None]:
        text = _compose(asset)
        logger.info("posting to twitter (%d chars)", len(text))
        try:
            return await asyncio.to_thread(self._sync_post, text)
        except Exception as exc:
            raise PublishError(f"Twitter post failed: {exc}") from exc

    async def get_status(self, post_id: str) -> tuple[str, str | None]:
        url = f"https://twitter.com/i/web/status/{post_id}"
        return "published", url
