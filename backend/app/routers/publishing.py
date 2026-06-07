"""Publishing routes (v2).

POST   /campaigns/{id}/assets/{platform}/publish   publish now or schedule
GET    /campaigns/{id}/posts                        list all posts for a campaign
DELETE /campaigns/{id}/posts/{post_id}              cancel a scheduled post

Rule (CLAUDE.md §v2): an asset MUST be approved before it can be published.
This is enforced here at the API layer — the frontend gate is UX only.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app import store
from app.db import get_session
from app.models import PostStatus, PublishRequest, PublishResult
from app.publishing.base import PublishError
from app.publishing.registry import get_publisher

logger = logging.getLogger("api.publishing")

router = APIRouter(prefix="/campaigns", tags=["publishing"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/{campaign_id}/assets/{platform}/publish", response_model=PublishResult)
async def publish_asset(
    campaign_id: str,
    platform: str,
    body: PublishRequest,
    session: SessionDep,
) -> PublishResult:
    """Publish an approved asset immediately or schedule it for later.

    - ``body.scheduled_at`` is None  → publish now.
    - ``body.scheduled_at`` is a future datetime → store as pending; a background
      worker (v2) will execute it.  Until that worker exists, the record stays
      pending and can be cancelled.
    """
    # 1. Campaign must exist.
    campaign = await store.get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")

    # 2. Asset must exist and be approved — never auto-publish.
    platform = platform.strip().lower()
    record = await store.get_asset(session, campaign_id, platform)
    if record is None:
        raise HTTPException(status_code=404, detail="asset not found")
    if not record.approved:
        raise HTTPException(
            status_code=422,
            detail="asset must be approved before publishing",
        )

    publisher = get_publisher(platform)

    # 3. Schedule case: store pending, no API call yet.
    if body.scheduled_at is not None:
        sched = body.scheduled_at
        if sched.tzinfo is None:
            sched = sched.replace(tzinfo=UTC)
        if sched <= datetime.now(UTC):
            raise HTTPException(
                status_code=422,
                detail="scheduled_at must be in the future",
            )
        logger.info(
            "scheduling post campaign=%s platform=%s at=%s",
            campaign_id, platform, sched.isoformat(),
        )
        return await store.create_post(
            session,
            campaign_id=campaign_id,
            platform=platform,
            post_id="",
            url=None,
            status=PostStatus.pending,
            scheduled_at=sched,
        )

    # 4. Publish now.
    logger.info("publishing now campaign=%s platform=%s provider=%s", campaign_id, platform, publisher.name)
    try:
        post_id, url = await publisher.post(record_to_asset(record))
    except PublishError as exc:
        logger.error("publish failed: %s", exc)
        return await store.create_post(
            session,
            campaign_id=campaign_id,
            platform=platform,
            post_id="",
            url=None,
            status=PostStatus.failed,
            error=str(exc),
        )

    return await store.create_post(
        session,
        campaign_id=campaign_id,
        platform=platform,
        post_id=post_id,
        url=url,
        status=PostStatus.published,
        published_at=datetime.now(UTC),
    )


@router.get("/{campaign_id}/posts", response_model=list[PublishResult])
async def list_posts(campaign_id: str, session: SessionDep) -> list[PublishResult]:
    campaign = await store.get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    return await store.list_posts(session, campaign_id)


@router.delete("/{campaign_id}/posts/{post_id}", response_model=PublishResult)
async def cancel_post(campaign_id: str, post_id: str, session: SessionDep) -> PublishResult:
    """Cancel a *pending* (scheduled) post. Published posts cannot be cancelled here."""
    result = await store.cancel_post(session, post_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="post not found or not in pending state",
        )
    if result.platform not in [
        a.platform
        for a in await store.list_assets(session, campaign_id)
    ]:
        raise HTTPException(status_code=404, detail="post does not belong to this campaign")
    return result


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def record_to_asset(record: store.AssetRecord):
    from app.models import Asset  # noqa: PLC0415
    return Asset(
        platform=record.platform,
        body=record.body,
        cta=record.cta,
        hashtags=record.hashtags,
    )
