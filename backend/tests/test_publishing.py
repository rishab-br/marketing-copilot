"""Tests for the v2 publishing layer.

Covers:
- StubPublisher interface
- Publisher registry (stub mode)
- POST /campaigns/{id}/assets/{platform}/publish (publish now + schedule)
- Approval gate enforcement
- GET  /campaigns/{id}/posts
- DELETE /campaigns/{id}/posts/{post_id}
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session, init_db, make_sessionmaker, to_async_url
from app.main import app
from app.models import Asset, AssetResult, EvalScore, GuardrailResult
from app.services import orchestrator

BRIEF = {
    "brand": "Acme",
    "product": "LaunchPad",
    "goal": "drive signups",
    "audience": "founders",
    "tone": "confident",
    "platforms": ["instagram"],
}


def _result_dict(platform="instagram") -> dict:
    result = AssetResult(
        asset=Asset(platform=platform, body="Great copy", cta="Sign up", hashtags=["launch"]),
        guardrail=GuardrailResult(passed=True),
        score=EvalScore(clarity=5, cta_strength=5, brand_fit=5, platform_fit=5, rationale="good"),
        iterations=1,
    )
    return result.model_dump(mode="json")


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_url = to_async_url(f"sqlite:///{tmp_path / 'test.db'}")
    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = make_sessionmaker(engine)
    asyncio.run(init_db(engine))

    async def _override() -> AsyncSession:
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = _override

    async def fake_stream(brief, **kwargs):
        yield {
            "type": "complete",
            "results": [_result_dict("instagram")],
            "needs_human_attention": False,
            "iteration": 1,
        }

    monkeypatch.setattr(orchestrator, "run_and_stream", fake_stream)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


@pytest.fixture
def campaign_id(client) -> str:
    """Create a campaign and run its stream so assets are persisted."""
    resp = client.post("/campaigns", json=BRIEF)
    cid = resp.json()["id"]
    client.get(f"/campaigns/{cid}/stream", headers={"accept": "text/event-stream"})
    return cid


# --------------------------------------------------------------------------- #
# StubPublisher unit tests
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_stub_publisher_post():
    from app.publishing.stub import StubPublisher

    pub = StubPublisher("instagram")
    post_id, url = await pub.post(
        Asset(platform="instagram", body="Hello!", cta="Shop now", hashtags=["sale"])
    )
    assert post_id
    assert url and "instagram" in url


@pytest.mark.asyncio
async def test_stub_publisher_get_status():
    from app.publishing.stub import StubPublisher

    pub = StubPublisher("twitter")
    status, url = await pub.get_status("abc123")
    assert status == "published"
    assert url is not None


# --------------------------------------------------------------------------- #
# Registry unit tests
# --------------------------------------------------------------------------- #


def test_registry_stub_mode(monkeypatch):
    import app.config as cfg
    from app.publishing.stub import StubPublisher

    monkeypatch.setattr(cfg.settings, "publishing_mode", "stub")
    from app.publishing import registry

    pub = registry.get_publisher("twitter")
    assert isinstance(pub, StubPublisher)


def test_registry_real_mode_falls_back_to_stub_when_no_keys(monkeypatch):
    import app.config as cfg
    from app.publishing.stub import StubPublisher

    monkeypatch.setattr(cfg.settings, "publishing_mode", "real")
    monkeypatch.setattr(cfg.settings, "twitter_consumer_key", "")
    from app.publishing import registry

    pub = registry.get_publisher("twitter")
    assert isinstance(pub, StubPublisher)


# --------------------------------------------------------------------------- #
# API integration tests
# --------------------------------------------------------------------------- #


def test_publish_now_requires_approved(client, campaign_id):
    resp = client.post(f"/campaigns/{campaign_id}/assets/instagram/publish", json={})
    assert resp.status_code == 422
    assert "approved" in resp.json()["detail"]


def test_publish_now_success(client, campaign_id):
    client.post(f"/campaigns/{campaign_id}/assets/instagram/approve")
    resp = client.post(f"/campaigns/{campaign_id}/assets/instagram/publish", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "published"
    assert data["platform"] == "instagram"
    assert data["post_id"]
    assert data["url"]


def test_publish_schedule_stores_pending(client, campaign_id):
    client.post(f"/campaigns/{campaign_id}/assets/instagram/approve")
    future = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
    resp = client.post(
        f"/campaigns/{campaign_id}/assets/instagram/publish",
        json={"scheduled_at": future},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["scheduled_at"] is not None


def test_publish_schedule_past_datetime_rejected(client, campaign_id):
    client.post(f"/campaigns/{campaign_id}/assets/instagram/approve")
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    resp = client.post(
        f"/campaigns/{campaign_id}/assets/instagram/publish",
        json={"scheduled_at": past},
    )
    assert resp.status_code == 422


def test_list_posts_empty(client, campaign_id):
    resp = client.get(f"/campaigns/{campaign_id}/posts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_posts_after_publish(client, campaign_id):
    client.post(f"/campaigns/{campaign_id}/assets/instagram/approve")
    client.post(f"/campaigns/{campaign_id}/assets/instagram/publish", json={})
    posts = client.get(f"/campaigns/{campaign_id}/posts").json()
    assert len(posts) == 1
    assert posts[0]["platform"] == "instagram"
    assert posts[0]["status"] == "published"


def test_cancel_scheduled_post(client, campaign_id):
    client.post(f"/campaigns/{campaign_id}/assets/instagram/approve")
    future = (datetime.now(UTC) + timedelta(hours=3)).isoformat()
    sched = client.post(
        f"/campaigns/{campaign_id}/assets/instagram/publish",
        json={"scheduled_at": future},
    ).json()
    post_id = sched["id"]

    cancel = client.delete(f"/campaigns/{campaign_id}/posts/{post_id}")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"


def test_cancel_published_post_fails(client, campaign_id):
    client.post(f"/campaigns/{campaign_id}/assets/instagram/approve")
    published = client.post(
        f"/campaigns/{campaign_id}/assets/instagram/publish", json={}
    ).json()
    resp = client.delete(f"/campaigns/{campaign_id}/posts/{published['id']}")
    assert resp.status_code == 404


def test_publish_unknown_campaign(client):
    resp = client.post("/campaigns/doesnotexist/assets/instagram/publish", json={})
    assert resp.status_code == 404
