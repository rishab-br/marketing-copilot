"""Persistence layer: SQLModel tables + CRUD helpers (async).

Tables: Campaign (the brief + run status), AssetRecord (latest per-platform
result + approval), Run (one orchestration execution: initial or regenerate).
Domain JSON (brief, hashtags, guardrail, score) is stored in JSON columns and
rehydrated into the Pydantic domain models on read.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Asset, AssetResult, Brief, EvalScore, GuardrailResult


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
class Campaign(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    brief: dict = Field(sa_column=Column(JSON))
    status: str = Field(default="pending")  # pending|running|completed|failed
    needs_human_attention: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class AssetRecord(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    campaign_id: str = Field(index=True, foreign_key="campaign.id")
    platform: str = Field(index=True)
    body: str
    cta: str
    hashtags: list = Field(default_factory=list, sa_column=Column(JSON))
    guardrail: dict = Field(sa_column=Column(JSON))
    score: dict = Field(sa_column=Column(JSON))
    iterations: int = Field(default=0)
    approved: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Run(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    campaign_id: str = Field(index=True, foreign_key="campaign.id")
    kind: str = Field(default="initial")  # initial|regenerate
    platform: str | None = Field(default=None)
    status: str = Field(default="running")  # running|completed|failed
    iteration: int = Field(default=0)
    needs_human_attention: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_now)
    finished_at: datetime | None = Field(default=None)


# --------------------------------------------------------------------------- #
# Campaign CRUD
# --------------------------------------------------------------------------- #
async def create_campaign(session: AsyncSession, brief: Brief) -> Campaign:
    campaign = Campaign(brief=brief.model_dump())
    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)
    return campaign


async def get_campaign(session: AsyncSession, campaign_id: str) -> Campaign | None:
    return await session.get(Campaign, campaign_id)


async def set_campaign_status(
    session: AsyncSession,
    campaign_id: str,
    status: str,
    *,
    needs_human_attention: bool | None = None,
) -> None:
    campaign = await session.get(Campaign, campaign_id)
    if campaign is None:
        return
    campaign.status = status
    if needs_human_attention is not None:
        campaign.needs_human_attention = needs_human_attention
    campaign.updated_at = _now()
    session.add(campaign)
    await session.commit()


# --------------------------------------------------------------------------- #
# Asset CRUD
# --------------------------------------------------------------------------- #
async def get_asset(session: AsyncSession, campaign_id: str, platform: str) -> AssetRecord | None:
    stmt = select(AssetRecord).where(
        AssetRecord.campaign_id == campaign_id,
        AssetRecord.platform == platform.strip().lower(),
    )
    return (await session.exec(stmt)).first()


async def list_assets(session: AsyncSession, campaign_id: str) -> list[AssetRecord]:
    stmt = select(AssetRecord).where(AssetRecord.campaign_id == campaign_id)
    return list((await session.exec(stmt)).all())


async def upsert_asset(session: AsyncSession, campaign_id: str, result: AssetResult) -> AssetRecord:
    """Insert or replace the asset for a platform. New content resets approval."""
    record = await get_asset(session, campaign_id, result.asset.platform)
    if record is None:
        record = AssetRecord(campaign_id=campaign_id, platform=result.asset.platform)

    record.body = result.asset.body
    record.cta = result.asset.cta
    record.hashtags = result.asset.hashtags
    record.guardrail = result.guardrail.model_dump()
    record.score = result.score.model_dump()
    record.iterations = result.iterations
    record.approved = False  # regenerated/updated content must be re-approved
    record.updated_at = _now()

    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def set_asset_approved(
    session: AsyncSession, campaign_id: str, platform: str, approved: bool = True
) -> AssetRecord | None:
    record = await get_asset(session, campaign_id, platform)
    if record is None:
        return None
    record.approved = approved
    record.updated_at = _now()
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


def record_to_result(record: AssetRecord) -> AssetResult:
    """Rehydrate a stored row into the AssetResult domain model."""
    return AssetResult(
        asset=Asset(
            platform=record.platform,
            body=record.body,
            cta=record.cta,
            hashtags=record.hashtags,
        ),
        guardrail=GuardrailResult(**record.guardrail),
        score=EvalScore(**record.score),
        iterations=record.iterations,
    )


# --------------------------------------------------------------------------- #
# Run CRUD
# --------------------------------------------------------------------------- #
async def create_run(
    session: AsyncSession, campaign_id: str, *, kind: str = "initial", platform: str | None = None
) -> Run:
    run = Run(campaign_id=campaign_id, kind=kind, platform=platform)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def finish_run(
    session: AsyncSession,
    run_id: str,
    *,
    status: str,
    iteration: int = 0,
    needs_human_attention: bool = False,
) -> None:
    run = await session.get(Run, run_id)
    if run is None:
        return
    run.status = status
    run.iteration = iteration
    run.needs_human_attention = needs_human_attention
    run.finished_at = _now()
    session.add(run)
    await session.commit()
