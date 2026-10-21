"""Shared vocabulary for the network.

One model-id table, one category list, and one authority order, so nodes
cannot drift apart on the labels the coverage check and the resolver compare.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# Cheapest three ids allowed by the assignment. Nothing else is ever sent.
# cross_dedup shares gpt-5-nano with dedup so a second pass cannot drift models.
MODELS: dict[str, str] = {
    "classify": "gpt-4.1-nano",
    "extract": "gpt-5-nano",
    "dedup": "gpt-5-nano",
    "cross_dedup": "gpt-5-nano",
    "polish": "gpt-4o-mini",
}

DocType = Literal[
    "decision",
    "specification",
    "interview",
    "email",
    "survey",
    "reference",
    "other",
]

Category = Literal[
    "circulation",
    "cataloging",
    "holds",
    "patrons",
    "acquisitions",
    "reports",
    "staff_admin_security",
    "interoperability",
    "performance_capacity",
    "other",
]

Priority = Literal["Must", "Should", "Could", "Won't"]

DOC_TYPES: tuple[DocType, ...] = (
    "decision",
    "specification",
    "interview",
    "email",
    "survey",
    "reference",
    "other",
)

# Decision outranks a draft spec, which outranks people talking, which
# outranks a mail thread, a survey, background reading, then anything else.
AUTHORITY_RANK: dict[DocType, int] = {
    "decision": 6,
    "specification": 5,
    "interview": 4,
    "email": 3,
    "survey": 2,
    "reference": 1,
    "other": 0,
}

CATEGORIES: tuple[Category, ...] = (
    "circulation",
    "cataloging",
    "holds",
    "patrons",
    "acquisitions",
    "reports",
    "staff_admin_security",
    "interoperability",
    "performance_capacity",
    "other",
)

# Temporary ids exist only so nodes can point at a row before REQ-xxx exists.
# A published sentence uses KEPT_MARK until those final ids are assigned.
KEPT_MARK = "[[KEPT]]"
_TEMP_CATEGORIES = "|".join(sorted(CATEGORIES, key=len, reverse=True))
TEMP_ID_RE = re.compile(rf"T-(?:{_TEMP_CATEGORIES})-\d+\b")

CATEGORY_LABELS: dict[Category, str] = {
    "circulation": "Circulation",
    "cataloging": "Cataloging",
    "holds": "Holds",
    "patrons": "Patrons",
    "acquisitions": "Acquisitions",
    "reports": "Reports",
    "staff_admin_security": "Staff, administration, and security",
    "interoperability": "Interoperability",
    "performance_capacity": "Performance and capacity",
    "other": "Other",
}

PRIORITIES: tuple[Priority, ...] = ("Must", "Should", "Could", "Won't")

# Must is the strongest obligation. Merge keeps the max; boost steps up one.
PRIORITY_RANK: dict[Priority, int] = {
    "Must": 3,
    "Should": 2,
    "Could": 1,
    "Won't": 0,
}

PRIORITY_UP: dict[Priority, Priority] = {
    "Won't": "Could",
    "Could": "Should",
    "Should": "Must",
    "Must": "Must",
}

# Initial extraction plus this many returns to the extract node.
MAX_COVERAGE_RETRIES = 2

_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class Document(BaseModel):
    doc_id: str
    text: str


class DocClassification(BaseModel):
    doc_id: str
    doc_type: DocType
    date: str | None
    summary: str


class RawRequirement(BaseModel):
    name: str
    description: str
    category: Category
    proposed_priority: Priority
    sources: list[str]


class Extraction(BaseModel):
    doc_id: str
    requirements: list[RawRequirement]
    no_requirements_reason: str | None = None


class CoverageFailure(BaseModel):
    doc_id: str
    reason: str


class OpenConflict(BaseModel):
    other_temp_id: str
    why: str
    tie_break: Literal["specificity", "stable_id"]


class StagedRequirement(BaseModel):
    temp_id: str
    name: str
    description: str
    category: Category
    priority: Priority
    sources: list[str]
    # Filled once, before polishing, so later prose can cite REQ-xxx.
    public_id: str = ""
    open_conflicts: list[OpenConflict] = Field(default_factory=list)


class DuplicateGroup(BaseModel):
    member_ids: list[str] = Field(
        description="Temp ids that state the same requirement."
    )
    keep_id: str = Field(description="Temp id whose identity survives the merge.")
    merged_name: str = Field(description="Short name that keeps every concrete detail.")
    merged_description: str = Field(
        description="One paragraph merging the members without dropping conditions."
    )


class ConflictPair(BaseModel):
    a: str
    b: str
    why: str = Field(description="Why both cannot be true of the same system.")


class NonsensicalItem(BaseModel):
    id: str
    why: str


class CategoryJudgement(BaseModel):
    category: Category
    duplicate_sets: list[DuplicateGroup]
    conflicts: list[ConflictPair]
    nonsensical: list[NonsensicalItem]


class BlacklistEntry(BaseModel):
    temp_id: str
    name: str
    description: str
    category: Category
    sources: list[str]
    kind: Literal["duplicate", "conflict", "nonsensical"]
    reason: str
    conflicts_with: str | None = None


class LlmClassification(BaseModel):
    doc_type: DocType
    date: str | None = Field(
        description="YYYY-MM-DD if the document states a date, else null."
    )
    summary: str = Field(description="One sentence on what the document is.")


class LlmRequirement(BaseModel):
    name: str
    description: str
    category: Category
    proposed_priority: Priority
    sources: list[str]


class LlmExtraction(BaseModel):
    requirements: list[LlmRequirement]
    no_requirements_reason: str | None


class LlmDedup(BaseModel):
    duplicate_sets: list[DuplicateGroup]
    conflicts: list[ConflictPair]
    nonsensical: list[NonsensicalItem]


class CrossDuplicateSet(BaseModel):
    """Name-only duplicate proposal. Wording is filled in code from the members."""

    member_ids: list[str] = Field(
        description="Ids from the input that name the same obligation."
    )
    keep_id: str = Field(description="One id from member_ids; the more specific name.")


class LlmCrossDedup(BaseModel):
    duplicate_sets: list[CrossDuplicateSet]


class LlmPolishedRequirement(BaseModel):
    id: str
    name: str
    description: str
    sources: list[str]


class LlmPolishBatch(BaseModel):
    requirements: list[LlmPolishedRequirement]


class LlmBlacklistLine(BaseModel):
    id: str
    explanation: str


class LlmBlacklistBatch(BaseModel):
    entries: list[LlmBlacklistLine]


def normalize_date(value: str | None) -> str | None:
    """Keep a real calendar date and drop anything the model invented a shape for."""
    if value is None:
        return None
    match = _ISO_DATE.search(value.strip())
    if match is None:
        return None
    try:
        return date(
            int(match.group(1)), int(match.group(2)), int(match.group(3))
        ).isoformat()
    except ValueError:
        return None


def priority_max(left: Priority, right: Priority) -> Priority:
    if PRIORITY_RANK[left] >= PRIORITY_RANK[right]:
        return left
    return right
