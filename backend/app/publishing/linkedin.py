"""LinkedIn publisher (UGC Posts API v2, async via httpx).

Requires in .env:
    LINKEDIN_ACCESS_TOKEN   — OAuth 2.0 user token with w_member_social scope
    LINKEDIN_AUTHOR_URN     — e.g. "urn:li:person:XXXXXXXX" or "urn:li:organization:XXXXXXXX"

LinkedIn does not expose a simple post-lookup endpoint for user posts, so
get_status reconstructs the URL from the stored post_id.
"""

from __future__ import annotations

import logging

from app.models import Asset
from app.publishing.base import PublishError, PublisherBase

logger = logging.getLogger("publishing.linkedin")

_API = "https://api.linkedin.com/v2/ugcPosts"


def _compose(asset: Asset) -> str:
    parts = [asset.body]
    if asset.cta:
        parts.append(asset.cta)
    if asset.hashtags:
        parts.append(" ".join(f"#{h}" for h in asset.hashtags))
    return "\n\n".join(parts)


class LinkedInPublisher(PublisherBase):
    name = "linkedin"

    def __init__(self, access_token: str, author_urn: str) -> None:
        self._token = access_token
        self._author = author_urn

    async def post(self, asset: Asset) -> tuple[str, str | None]:
        try:
            import httpx  # noqa: PLC0415
        except ImportError as exc:
            raise PublishError("httpx not installed") from exc

        text = _compose(asset)
        payload = {
            "author": self._author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        logger.info("posting to linkedin")
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(_API, json=payload, headers=headers)
        if not resp.is_success:
            raise PublishError(f"LinkedIn API {resp.status_code}: {resp.text}")

        post_id = resp.headers.get("x-restli-id", "")
        url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None
        return post_id, url

    async def get_status(self, post_id: str) -> tuple[str, str | None]:
        url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None
        return "published", url
