"""Build and run the orchestration graph.

    strategist -> copywriter -> critic -> (conditional)
                      ^                         |
                      |   revise (iter < max)   |
                      +-------------------------+
                                                |
                                          finalize -> END

The conditional edge (``route_after_critic``) is the heart of the system and is
a pure function so it can be unit-tested in isolation (CLAUDE.md §8).
"""

from __future__ import annotations

import asyncio
import logging

from langgraph.graph import END, StateGraph

from app.agents.copywriter import run_copywriter
from app.agents.critic import run_critic
from app.agents.strategist import run_strategist
from app.graph.state import GraphState
from app.llm.client import LLMClient
from app.models import AssetResult, Brief

logger = logging.getLogger("graph")

REVISE = "revise"
FINALIZE = "finalize"


def _all_pass(state: GraphState) -> bool:
    """True only if there are results and every one clears both gates."""
    return bool(state.results) and all(r.passed(state.threshold) for r in state.results)


def route_after_critic(state: GraphState) -> str:
    """Decide what happens after the critic — the conditional edge.

    - all assets pass guardrails AND meet threshold -> FINALIZE
    - else, if we still have revisions left            -> REVISE (back to copywriter)
    - else (out of iterations)                         -> FINALIZE (best-so-far, flagged)
    """
    if _all_pass(state):
        return FINALIZE
    if state.iteration < state.max_iterations:
        return REVISE
    return FINALIZE


def build_graph(client: LLMClient | None = None):
    """Compile the campaign graph. ``client`` is injectable for testing."""

    async def strategist_node(state: GraphState) -> dict:
        plan = await run_strategist(state.brief, client=client)
        return {"plan": plan}

    async def copywriter_node(state: GraphState) -> dict:
        # On a revision pass, feed the prior drafts + critic feedback back in.
        prior = state.results or None
        assets = await run_copywriter(state.brief, state.plan, prior_results=prior, client=client)
        return {"current_assets": assets, "iteration": state.iteration + 1}

    async def critic_node(state: GraphState) -> dict:
        async def critique(asset) -> AssetResult:
            guardrail, score = await run_critic(asset, state.brief, client=client)
            return AssetResult(
                asset=asset, guardrail=guardrail, score=score, iterations=state.iteration
            )

        results = await asyncio.gather(*(critique(a) for a in state.current_assets))
        return {"results": list(results)}

    def finalize_node(state: GraphState) -> dict:
        needs_human = not _all_pass(state)
        if needs_human:
            logger.info(
                "graph.needs_human_attention",
                extra={"iteration": state.iteration, "max": state.max_iterations},
            )
        return {"needs_human_attention": needs_human}

    graph = StateGraph(GraphState)
    graph.add_node("strategist", strategist_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("critic", critic_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("strategist")
    graph.add_edge("strategist", "copywriter")
    graph.add_edge("copywriter", "critic")
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {REVISE: "copywriter", FINALIZE: "finalize"},
    )
    graph.add_edge("finalize", END)

    return graph.compile()


async def run_campaign(
    brief: Brief,
    *,
    client: LLMClient | None = None,
    max_iterations: int | None = None,
    threshold: float | None = None,
) -> GraphState:
    """Run the full graph for a brief and return the final state."""
    app = build_graph(client=client)

    overrides: dict = {}
    if max_iterations is not None:
        overrides["max_iterations"] = max_iterations
    if threshold is not None:
        overrides["threshold"] = threshold

    initial = GraphState(brief=brief, **overrides)
    final = await app.ainvoke(initial)
    return GraphState.model_validate(final)
