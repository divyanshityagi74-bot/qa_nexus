"""
graph.py
========
Defines the LangGraph StateGraph for Phase 1.

This file owns:
  - TestGenState  — the shared state schema (TypedDict)
  - All node imports
  - Graph wiring: nodes + edges + conditional edges
  - compile() call that returns the runnable graph

Usage from main.py:
    from src.graph import build_graph
    graph = build_graph()
    result = graph.invoke({
        "filepath": "samples/requirements/svod_offer_internal_requirements.txt",
        "collection_path": "samples/collections/postman_collection.json",
        "auth_collection_path": "samples/collections/demo_examples.json",
        "environment_path": "samples/environments/staging.json",
        "app_url": "https://staging-opc.irdeto.com",
    })
"""

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END


# ─────────────────────────────────────────────────────────────
# STATE SCHEMA
# Every node reads from this and returns a partial update dict.
# ─────────────────────────────────────────────────────────────

class TestGenState(TypedDict):

    # ── Inputs ───────────────────────────────────────────────
    filepath: Optional[str]              # requirements doc path
    collection_path: Optional[str]       # postman feature collection
    auth_collection_path: Optional[str]  # demo_examples.json
    environment_path: Optional[str]      # dev.json / staging.json
    app_url: Optional[str]               # for UI test generation
    env_name: Optional[str]              # dev / staging / prod

    # ── After resolve_environment ────────────────────────────
    resolved_collection: Optional[dict]
    variables: dict

    # ── After load_document ──────────────────────────────────
    chunks: List[str]

    # ── After parse_collection ───────────────────────────────
    endpoints: List[dict]
    auth_endpoints: List[dict]

    # ── After build_chain_graph ──────────────────────────────
    chain_map: dict

    # ── After extract_scenarios ──────────────────────────────
    scenarios: List[dict]
    retry_count: int
    failed_chunks: List[int]

    # ── After generate nodes ─────────────────────────────────
    api_layer: Optional[dict]
    ui_layer: Optional[dict]
    bdd_output: Optional[str]

    # ── Error tracking ───────────────────────────────────────
    error: Optional[str]


# ─────────────────────────────────────────────────────────────
# CONDITIONAL EDGE FUNCTIONS
# ─────────────────────────────────────────────────────────────

def should_retry(state: TestGenState) -> str:
    """
    After validate_output node.
    Empty scenarios + retries remaining → retry
    Error set → stop
    Otherwise → proceed
    """
    from src.config import MAX_RETRIES
    if state.get("error"):
        return "error"
    if not state.get("scenarios") and state.get("retry_count", 0) < MAX_RETRIES:
        return "retry"
    return "proceed"


def route_by_type(state: TestGenState) -> List[str]:
    """
    After validation succeeds.
    Checks which test types exist in scenarios.
    Returns list of generator nodes to run in parallel.
    If no --url provided, skips UI generation.
    """
    scenarios = state.get("scenarios", [])
    has_api   = any(s.get("test_type") == "API" for s in scenarios)
    has_ui    = any(s.get("test_type") == "UI"  for s in scenarios)

    routes = []
    if has_api:
        routes.append("generate_api_tests")
    if has_ui and state.get("app_url"):
        routes.append("generate_ui_tests")

    return routes if routes else ["generate_api_tests"]


# ─────────────────────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────────────────────

def build_graph():
    """
    Wires all nodes and edges together.
    Call once at startup and reuse the compiled graph.
    """
    from src.nodes.resolve_environment import resolve_environment
    from src.nodes.load_document       import load_document
    from src.nodes.parse_collection    import parse_collection
    from src.nodes.build_chain_graph   import build_chain_graph
    from src.nodes.extract_scenarios   import extract_scenarios
    from src.nodes.validate_output     import validate_output
    from src.nodes.generate_api_tests  import generate_api_tests
    from src.nodes.generate_ui_tests   import generate_ui_tests
    from src.nodes.write_outputs       import write_outputs

    graph = StateGraph(TestGenState)

    # ── Register nodes ────────────────────────────────────────
    graph.add_node("resolve_environment", resolve_environment)
    graph.add_node("load_document",       load_document)
    graph.add_node("parse_collection",    parse_collection)
    graph.add_node("build_chain_graph",   build_chain_graph)
    graph.add_node("extract_scenarios",   extract_scenarios)
    graph.add_node("validate_output",     validate_output)
    graph.add_node("generate_api_tests",  generate_api_tests)
    graph.add_node("generate_ui_tests",   generate_ui_tests)
    graph.add_node("write_outputs",       write_outputs)

    # ── Entry point ───────────────────────────────────────────
    graph.set_entry_point("resolve_environment")

    # ── Linear edges ──────────────────────────────────────────
    graph.add_edge("resolve_environment", "load_document")
    graph.add_edge("load_document",       "parse_collection")
    graph.add_edge("parse_collection",    "build_chain_graph")
    graph.add_edge("build_chain_graph",   "extract_scenarios")
    graph.add_edge("extract_scenarios",   "validate_output")

    # ── Conditional edge: retry or proceed ────────────────────
    graph.add_conditional_edges(
        "validate_output",
        should_retry,
        {
            "retry":   "extract_scenarios",
            "proceed": "generate_api_tests",
            "error":   END,
        }
    )

    # ── Parallel fan-out: API and UI ──────────────────────────
    graph.add_conditional_edges(
        "validate_output",
        route_by_type,
        {
            "generate_api_tests": "generate_api_tests",
            "generate_ui_tests":  "generate_ui_tests",
        }
    )

    # ── Fan-in: both generators feed write_outputs ────────────
    graph.add_edge("generate_api_tests", "write_outputs")
    graph.add_edge("generate_ui_tests",  "write_outputs")
    graph.add_edge("write_outputs",      END)

    return graph.compile()