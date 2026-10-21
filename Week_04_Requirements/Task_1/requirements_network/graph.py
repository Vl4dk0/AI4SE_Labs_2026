"""LangGraph wiring. The coverage node is the only way back to extract."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import (
    assemble,
    classify_docs,
    coverage_check,
    cross_dedup,
    dedup_conflicts,
    extract,
    fold,
    group_by_category,
    load_corpus,
    resolve,
    write_document,
)
from .state import NetworkState


def build_graph() -> CompiledStateGraph[NetworkState, None, NetworkState, NetworkState]:
    graph: StateGraph[NetworkState, None, NetworkState, NetworkState] = StateGraph(
        NetworkState
    )
    graph.add_node("load_corpus", load_corpus)
    graph.add_node("classify_docs", classify_docs)
    graph.add_node("extract", extract)
    graph.add_node("coverage_check", coverage_check)
    graph.add_node("group_by_category", group_by_category)
    graph.add_node("dedup_conflicts", dedup_conflicts)
    graph.add_node("fold_categories", fold)
    graph.add_node("cross_dedup", cross_dedup)
    graph.add_node("resolve", resolve)
    graph.add_node("write_document", write_document)
    graph.add_node("assemble", assemble)

    graph.add_edge(START, "load_corpus")
    graph.add_edge("load_corpus", "classify_docs")
    graph.add_edge("classify_docs", "extract")
    graph.add_edge("extract", "coverage_check")
    # Failing documents return to extract with the checker's reason in state.
    # When the retry budget is spent, pending_doc_ids is empty and we move on.
    graph.add_conditional_edges(
        "coverage_check",
        _route_after_coverage,
        {"extract": "extract", "group_by_category": "group_by_category"},
    )
    graph.add_edge("group_by_category", "dedup_conflicts")
    # Within-category merges land before the cross pass, so that model only
    # sees survivors. The boost stays in resolve, after the second merge.
    graph.add_edge("dedup_conflicts", "fold_categories")
    graph.add_edge("fold_categories", "cross_dedup")
    graph.add_edge("cross_dedup", "resolve")
    graph.add_edge("resolve", "write_document")
    graph.add_edge("write_document", "assemble")
    graph.add_edge("assemble", END)
    return graph.compile()


def _route_after_coverage(state: NetworkState) -> str:
    if state["pending_doc_ids"]:
        return "extract"
    return "group_by_category"
