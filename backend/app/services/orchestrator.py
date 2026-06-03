"""Orchestrator service: run the graph and translate it into stream events.

The LLM client is built lazily *here*, so API routes never construct it — that
keeps the routes (and their tests) free of any API-key requirement. Tests stub
out these functions directly.

Stream event shapes (all JSON-serializable dicts):
  {"type": "node", "node": <name>, "payload": {...}}          # progress
  {"type": "complete", "results": [AssetResult...],
   "needs_human_attention": bool, "iteration": int}            # final
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.graph.build import build_graph
from app.graph.state import GraphState
from app.llm.client import LLMClient, get_llm_client
from app.models import Brief


def _initial_state(brief: Brief, max_iterations: int | None, threshold: float | None) -> GraphState:
    overrides: dict[str, Any] = {}
    if max_iterations is not None:
        overrides["max_iterations"] = max_iterations
    if threshold is not None:
        overrides["threshold"] = threshold
    return GraphState(brief=brief, **overrides)


def _progress_payload(node: str, update: dict) -> dict:
    """Sanitize a node's state update into a small, client-friendly payload."""
    if node == "strategist" and update.get("plan") is not None:
        plan = update["plan"]
        return {"angle": plan.angle, "platforms": list(plan.per_platform_direction)}
    if node == "copywriter":
        assets = update.get("current_assets", [])
        return {
            "iteration": update.get("iteration"),
            "platforms": [a.platform for a in assets],
        }
    if node == "critic":
        results = update.get("results", [])
        return {
            "assets": [
                {
                    "platform": r.asset.platform,
                    "overall": r.score.overall,
                    "guardrail_passed": r.guardrail.passed,
                }
                for r in results
            ]
        }
    if node == "finalize":
        return {"needs_human_attention": update.get("needs_human_attention")}
    return {}


async def run_and_stream(
    brief: Brief,
    *,
    client: LLMClient | None = None,
    max_iterations: int | None = None,
    threshold: float | None = None,
) -> AsyncIterator[dict]:
    """Stream agent progress, then a final ``complete`` event with the results."""
    graph = build_graph(client=client or get_llm_client())
    initial = _initial_state(brief, max_iterations, threshold)

    results: list = []
    needs_human = False
    iteration = 0

    async for chunk in graph.astream(initial, stream_mode="updates"):
        for node, update in chunk.items():
            if not isinstance(update, dict):
                continue
            if "iteration" in update:
                iteration = update["iteration"]
            if "results" in update:
                results = update["results"]
            if "needs_human_attention" in update:
                needs_human = update["needs_human_attention"]
            yield {"type": "node", "node": node, "payload": _progress_payload(node, update)}

    yield {
        "type": "complete",
        "results": [r.model_dump(mode="json") for r in results],
        "needs_human_attention": needs_human,
        "iteration": iteration,
    }


async def run_once(
    brief: Brief,
    *,
    client: LLMClient | None = None,
    max_iterations: int | None = None,
    threshold: float | None = None,
) -> dict:
    """Run the graph to completion (no streaming) — used for regenerate."""
    final = None
    async for event in run_and_stream(
        brief, client=client, max_iterations=max_iterations, threshold=threshold
    ):
        if event["type"] == "complete":
            final = event
    assert final is not None  # run_and_stream always emits a complete event
    return final
