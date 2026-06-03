"""Campaign API routes (CLAUDE.md §11).

POST   /campaigns                                   submit a brief -> id
GET    /campaigns/{id}/stream                       SSE: agent steps + results
GET    /campaigns/{id}                              fetch a completed run
POST   /campaigns/{id}/assets/{platform}/approve    approve one asset
POST   /campaigns/{id}/assets/{platform}/regenerate re-run the loop for one asset
"""

from __future__ import annotations

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app import store
from app.db import get_session
from app.models import Asset, AssetResult, Brief, EvalScore, GuardrailResult
from app.services import orchestrator

logger = logging.getLogger("api")

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# --------------------------------------------------------------------------- #
# Response schemas
# --------------------------------------------------------------------------- #
class CampaignCreated(BaseModel):
    id: str
    stream_url: str


class AssetView(BaseModel):
    platform: str
    asset: Asset
    guardrail: GuardrailResult
    score: EvalScore
    iterations: int
    approved: bool


class CampaignView(BaseModel):
    id: str
    status: str
    needs_human_attention: bool
    brief: Brief
    assets: list[AssetView]


def _to_view(record: store.AssetRecord) -> AssetView:
    result = store.record_to_result(record)
    return AssetView(
        platform=record.platform,
        asset=result.asset,
        guardrail=result.guardrail,
        score=result.score,
        iterations=result.iterations,
        approved=record.approved,
    )


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@router.post("", response_model=CampaignCreated, status_code=201)
async def create_campaign(brief: Brief, session: SessionDep):
    campaign = await store.create_campaign(session, brief)
    return CampaignCreated(id=campaign.id, stream_url=f"/campaigns/{campaign.id}/stream")


@router.get("/{campaign_id}/stream")
async def stream_campaign(campaign_id: str, session: SessionDep):
    campaign = await store.get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")

    brief = Brief(**campaign.brief)
    run = await store.create_run(session, campaign_id, kind="initial")

    async def event_gen():
        await store.set_campaign_status(session, campaign_id, "running")
        try:
            async for event in orchestrator.run_and_stream(brief):
                if event["type"] == "complete":
                    for raw in event["results"]:
                        await store.upsert_asset(
                            session, campaign_id, AssetResult.model_validate(raw)
                        )
                    await store.set_campaign_status(
                        session,
                        campaign_id,
                        "completed",
                        needs_human_attention=event["needs_human_attention"],
                    )
                    await store.finish_run(
                        session,
                        run.id,
                        status="completed",
                        iteration=event["iteration"],
                        needs_human_attention=event["needs_human_attention"],
                    )
                yield {"event": event["type"], "data": json.dumps(event)}
        except Exception as exc:  # noqa: BLE001 - surface failure to client + DB
            logger.exception("campaign stream failed", extra={"campaign_id": campaign_id})
            await store.set_campaign_status(session, campaign_id, "failed")
            await store.finish_run(session, run.id, status="failed")
            yield {"event": "error", "data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(event_gen())


@router.get("/{campaign_id}", response_model=CampaignView)
async def get_campaign(campaign_id: str, session: SessionDep):
    campaign = await store.get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    records = await store.list_assets(session, campaign_id)
    return CampaignView(
        id=campaign.id,
        status=campaign.status,
        needs_human_attention=campaign.needs_human_attention,
        brief=Brief(**campaign.brief),
        assets=[_to_view(r) for r in records],
    )


@router.post("/{campaign_id}/assets/{platform}/approve", response_model=AssetView)
async def approve_asset(campaign_id: str, platform: str, session: SessionDep):
    record = await store.set_asset_approved(session, campaign_id, platform, True)
    if record is None:
        raise HTTPException(status_code=404, detail="asset not found")
    return _to_view(record)


@router.post("/{campaign_id}/assets/{platform}/regenerate", response_model=AssetView)
async def regenerate_asset(campaign_id: str, platform: str, session: SessionDep):
    campaign = await store.get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign not found")

    platform = platform.strip().lower()
    brief_data = dict(campaign.brief)
    if platform not in [p.strip().lower() for p in brief_data.get("platforms", [])]:
        raise HTTPException(status_code=404, detail="platform not in campaign brief")

    # Re-run the loop for just this one platform.
    single = Brief(**{**brief_data, "platforms": [platform]})
    run = await store.create_run(session, campaign_id, kind="regenerate", platform=platform)
    result = await orchestrator.run_once(single)

    match = next((r for r in result["results"] if r["asset"]["platform"] == platform), None)
    if match is None:
        await store.finish_run(session, run.id, status="failed")
        raise HTTPException(status_code=502, detail="regeneration produced no asset")

    record = await store.upsert_asset(session, campaign_id, AssetResult.model_validate(match))
    await store.finish_run(
        session,
        run.id,
        status="completed",
        iteration=result["iteration"],
        needs_human_attention=result["needs_human_attention"],
    )
    return _to_view(record)
