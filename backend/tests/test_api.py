"""API + persistence tests — full flow with a temp DB and a stubbed orchestrator.

No LLM calls: orchestrator.run_and_stream / run_once are replaced with fakes that
emit scripted events, so we exercise routes, SSE, and SQLite end to end.
"""

import asyncio

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
    "product": "TaskFlow",
    "goal": "drive signups",
    "audience": "founders",
    "tone": "confident",
    "platforms": ["instagram", "linkedin"],
}


def _result_dict(platform="instagram", *, overall_pass=True, body="Body") -> dict:
    dims = (5, 5, 5, 5) if overall_pass else (2, 2, 2, 2)
    result = AssetResult(
        asset=Asset(platform=platform, body=body, cta="Sign up", hashtags=["tag"]),
        guardrail=GuardrailResult(passed=True),
        score=EvalScore(
            clarity=dims[0],
            cta_strength=dims[1],
            brand_fit=dims[2],
            platform_fit=dims[3],
            rationale="r",
        ),
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

    # Default stubs (individual tests can re-monkeypatch).
    async def fake_stream(brief, **kwargs):
        yield {"type": "node", "node": "strategist", "payload": {"angle": "Reclaim your day"}}
        yield {"type": "node", "node": "copywriter", "payload": {"iteration": 1}}
        yield {
            "type": "complete",
            "results": [_result_dict("instagram"), _result_dict("linkedin")],
            "needs_human_attention": False,
            "iteration": 1,
        }

    monkeypatch.setattr(orchestrator, "run_and_stream", fake_stream)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def _create(client) -> str:
    resp = client.post("/campaigns", json=BRIEF)
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_returns_id_and_stream_url(client):
    resp = client.post("/campaigns", json=BRIEF)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["stream_url"] == f"/campaigns/{body['id']}/stream"


def test_get_unknown_campaign_404(client):
    assert client.get("/campaigns/does-not-exist").status_code == 404


def test_stream_emits_events_and_persists(client):
    cid = _create(client)

    resp = client.get(f"/campaigns/{cid}/stream", headers={"accept": "text/event-stream"})
    assert resp.status_code == 200
    text = resp.text
    assert "strategist" in text
    assert "complete" in text

    # The completed run is now persisted and fetchable.
    got = client.get(f"/campaigns/{cid}").json()
    assert got["status"] == "completed"
    assert got["needs_human_attention"] is False
    platforms = {a["platform"] for a in got["assets"]}
    assert platforms == {"instagram", "linkedin"}
    assert all(a["approved"] is False for a in got["assets"])


def test_approve_marks_asset_approved(client):
    cid = _create(client)
    client.get(f"/campaigns/{cid}/stream", headers={"accept": "text/event-stream"})

    resp = client.post(f"/campaigns/{cid}/assets/instagram/approve")
    assert resp.status_code == 200
    assert resp.json()["approved"] is True

    got = client.get(f"/campaigns/{cid}").json()
    insta = next(a for a in got["assets"] if a["platform"] == "instagram")
    assert insta["approved"] is True


def test_approve_unknown_asset_404(client):
    cid = _create(client)
    assert client.post(f"/campaigns/{cid}/assets/instagram/approve").status_code == 404


def test_regenerate_replaces_asset_and_resets_approval(client, monkeypatch):
    cid = _create(client)
    client.get(f"/campaigns/{cid}/stream", headers={"accept": "text/event-stream"})
    client.post(f"/campaigns/{cid}/assets/instagram/approve")

    async def fake_run_once(brief, **kwargs):
        return {
            "results": [_result_dict("instagram", body="Regenerated body")],
            "needs_human_attention": False,
            "iteration": 1,
        }

    monkeypatch.setattr(orchestrator, "run_once", fake_run_once)

    resp = client.post(f"/campaigns/{cid}/assets/instagram/regenerate")
    assert resp.status_code == 200
    view = resp.json()
    assert view["asset"]["body"] == "Regenerated body"
    assert view["approved"] is False  # new content must be re-approved


def test_regenerate_unknown_platform_404(client):
    cid = _create(client)
    assert client.post(f"/campaigns/{cid}/assets/tiktok/regenerate").status_code == 404
