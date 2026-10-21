"""Graph state. Nodes replace the keys they own; nothing is appended blindly."""

from __future__ import annotations

from typing import Any, TypedDict


class NetworkState(TypedDict):
    input_dir: str
    output_path: str
    documents: list[dict[str, Any]]
    classifications: list[dict[str, Any]]
    extractions: list[dict[str, Any]]
    extract_attempts: dict[str, int]
    pending_doc_ids: list[str]
    coverage_failures: list[dict[str, Any]]
    uncovered: list[dict[str, Any]]
    coverage_rounds: int
    grouped: list[dict[str, Any]]
    judgements: list[dict[str, Any]]
    folded: list[dict[str, Any]]
    cross_groups: list[dict[str, Any]]
    cross_dropped: int
    resolved: list[dict[str, Any]]
    blacklist: list[dict[str, Any]]
    markdown: str
    requirement_count: int
    blacklist_count: int


def fresh_state(input_dir: str, output_path: str) -> NetworkState:
    return {
        "input_dir": input_dir,
        "output_path": output_path,
        "documents": [],
        "classifications": [],
        "extractions": [],
        "extract_attempts": {},
        "pending_doc_ids": [],
        "coverage_failures": [],
        "uncovered": [],
        "coverage_rounds": 0,
        "grouped": [],
        "judgements": [],
        "folded": [],
        "cross_groups": [],
        "cross_dropped": 0,
        "resolved": [],
        "blacklist": [],
        "markdown": "",
        "requirement_count": 0,
        "blacklist_count": 0,
    }
