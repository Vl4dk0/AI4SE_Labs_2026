"""Assemble the single Markdown document the assignment asks for.

Identifiers are assigned here, after resolution, so the sort is stable:
category order, then MoSCoW from Must down to Won't, then name.
"""

from __future__ import annotations

import re

from .models import (
    CATEGORIES,
    CATEGORY_LABELS,
    KEPT_MARK,
    MODELS,
    TEMP_ID_RE,
    BlacklistEntry,
    Category,
    DocClassification,
    Extraction,
    Priority,
    StagedRequirement,
)

_PRIORITY_ORDER: dict[Priority, int] = {"Must": 0, "Should": 1, "Could": 2, "Won't": 3}


def assign_ids(
    requirements: list[StagedRequirement],
) -> list[tuple[str, StagedRequirement]]:
    ordered = sorted(
        requirements,
        key=lambda item: (
            CATEGORIES.index(item.category),
            _PRIORITY_ORDER[item.priority],
            item.name.lower(),
            item.temp_id,
        ),
    )
    assigned: list[tuple[str, StagedRequirement]] = []
    for index, item in enumerate(ordered, start=1):
        public = f"REQ-{index:03d}"
        assigned.append((public, item.model_copy(update={"public_id": public})))
    return assigned


def ordered_for_document(
    requirements: list[StagedRequirement],
) -> list[tuple[str, StagedRequirement]]:
    """Keep ids assigned before polishing.

    Sorting again by the polished name would renumber, and an explanation
    that already cites REQ-xxx would point at the wrong requirement.
    """
    if requirements and all(item.public_id for item in requirements):
        return sorted(
            [(item.public_id, item) for item in requirements],
            key=lambda pair: int(pair[0].removeprefix("REQ-")),
        )
    return assign_ids(requirements)


def render_document(
    *,
    generated_on: str,
    requirements: list[tuple[str, StagedRequirement]],
    blacklist: list[tuple[BlacklistEntry, str]],
    classifications: list[DocClassification],
    extractions: list[Extraction],
    uncovered: dict[str, str],
    coverage_rounds: int,
) -> str:
    id_by_temp = {item.temp_id: req_id for req_id, item in requirements}
    name_by_temp = _names(requirements, blacklist)
    models_line = (
        "Models: "
        f"classification `{MODELS['classify']}`; "
        f"extraction and deduplication `{MODELS['dedup']}`; "
        f"polishing `{MODELS['polish']}`."
    )
    scale_intro = (
        "Priorities use MoSCoW. A stronger priority wins when two wordings of the "
        "same requirement are merged."
    )
    must_line = (
        "- **Must** — the system is not acceptable without this. The source says "
        "shall, must, or required, or it is a stated specification requirement."
    )
    wont_line = (
        "- **Won't** — explicitly out of scope for this iteration. Recorded so it "
        "is not built and not forgotten."
    )
    boost_line = (
        "**Boost.** After duplicates are merged, a requirement whose sources include "
        "a decision document, or a requirement with at least three distinct sources, "
        "is raised one level. Must stays Must. The boost is applied once, even when "
        "both conditions are true. An explicit Won't that is backed by a decision or "
        "by three sources therefore becomes a Could."
    )
    lines: list[str] = [
        "# Software requirements",
        "",
        f"Generated: {generated_on}",
        "",
        models_line,
        "",
        "## Priority scale",
        "",
        scale_intro,
        "",
        must_line,
        "- **Should** — important, but acceptance does not depend on it.",
        "- **Could** — do it if the schedule allows. A wish or an option.",
        wont_line,
        "",
        boost_line,
        "",
        "Requirements are grouped by category. Each identifier is stable for this document.",
        "",
    ]
    if not requirements:
        lines.append("No requirements survived resolution.")
        lines.append("")
    current: Category | None = None
    for req_id, requirement in requirements:
        if requirement.category != current:
            current = requirement.category
            lines.append(f"## {CATEGORY_LABELS[current]}")
            lines.append("")
        lines.extend(_requirement_block(req_id, requirement, blacklist))
    lines.extend(_blacklist_section(blacklist, id_by_temp, name_by_temp))
    lines.extend(
        _appendix(
            classifications=classifications,
            extractions=extractions,
            requirements=requirements,
            uncovered=uncovered,
            coverage_rounds=coverage_rounds,
        )
    )
    # Last gate. Nodes bind [[KEPT]] earlier; this still catches an id a model echoed.
    text = "\n".join(lines).rstrip() + "\n"
    return scrub_published(text, id_by_temp, name_by_temp)


def _requirement_block(
    req_id: str,
    requirement: StagedRequirement,
    blacklist: list[tuple[BlacklistEntry, str]],
) -> list[str]:
    sources = ", ".join(f"`{source}`" for source in requirement.sources)
    lines = [
        f"### {req_id} — {requirement.name}",
        "",
        f"- **Priority:** {requirement.priority}",
        f"- **Sources:** {sources}",
        "",
        requirement.description.strip(),
        "",
    ]
    by_temp = {entry.temp_id: entry for entry, _explanation in blacklist}
    for note in requirement.open_conflicts:
        other = by_temp.get(note.other_temp_id)
        # The temporary id is a join key. The published line uses the name.
        other_name = other.name if other is not None else "a discarded requirement"
        if note.tie_break == "specificity":
            kept = "This wording was kept because it is more specific."
        else:
            kept = "Both wordings were equally specific; this one was kept for a stable order."
        why = note.why.strip()
        lines.append(
            f"> **Open conflict.** Authority and date tied with discarded requirement "
            f'"{other_name}". {kept} {why}'
        )
        lines.append("")
    return lines


def _blacklist_section(
    blacklist: list[tuple[BlacklistEntry, str]],
    id_by_temp: dict[str, str],
    name_by_temp: dict[str, str],
) -> list[str]:
    intro = (
        "Candidates removed because they duplicated another requirement, conflicted "
        "with a stronger one, or were not a real requirement."
    )
    lines = [
        "## Blacklist",
        "",
        intro,
        "",
    ]
    if not blacklist:
        lines.append("None.")
        lines.append("")
        return lines
    ordered = sorted(
        blacklist, key=lambda pair: (pair[0].category, pair[0].name.lower())
    )
    for entry, explanation in ordered:
        lines.append(f"### Discarded — {entry.name}")
        lines.append("")
        lines.append(f"- **Category:** {CATEGORY_LABELS[entry.category]}")
        sources = ", ".join(f"`{source}`" for source in entry.sources) or "none"
        lines.append(f"- **Original sources:** {sources}")
        lines.append(f"- **Disposition:** {_disposition(entry, id_by_temp)}")
        lines.append("")
        lines.append(entry.description.strip())
        lines.append("")
        shown = explanation.strip() or entry.reason.strip()
        lines.append(present_explanation(entry, shown, id_by_temp, name_by_temp))
        lines.append("")
    return lines


def _disposition(entry: BlacklistEntry, id_by_temp: dict[str, str]) -> str:
    other = id_by_temp.get(entry.conflicts_with or "")
    if entry.kind == "nonsensical" or not other:
        if entry.kind == "duplicate":
            return "Duplicate"
        if entry.kind == "conflict":
            return "Conflict"
        return "Nonsensical"
    if entry.kind == "duplicate":
        return f"Duplicate of {other}"
    return f"Conflicts with {other}"


def present_explanation(
    entry: BlacklistEntry,
    explanation: str,
    id_by_temp: dict[str, str],
    name_by_temp: dict[str, str],
) -> str:
    """Bind the surviving requirement to its REQ id before anyone reads the sentence."""
    text = explanation
    public = id_by_temp.get(entry.conflicts_with or "")
    if public:
        text = text.replace(KEPT_MARK, public)
    else:
        text = text.replace(KEPT_MARK, "the surviving requirement")
    return scrub_temp_ids(text, id_by_temp, name_by_temp)


def scrub_temp_ids(
    text: str, id_by_temp: dict[str, str], name_by_temp: dict[str, str]
) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        public = id_by_temp.get(token)
        if public:
            return public
        name = name_by_temp.get(token)
        if name:
            return f'"{name}"'
        return "a requirement"

    return TEMP_ID_RE.sub(repl, text)


def scrub_published(
    text: str, id_by_temp: dict[str, str], name_by_temp: dict[str, str]
) -> str:
    text = text.replace(KEPT_MARK, "the surviving requirement")
    return scrub_temp_ids(text, id_by_temp, name_by_temp)


def _names(
    requirements: list[tuple[str, StagedRequirement]],
    blacklist: list[tuple[BlacklistEntry, str]],
) -> dict[str, str]:
    names = {item.temp_id: item.name for _req_id, item in requirements}
    for entry, _explanation in blacklist:
        names.setdefault(entry.temp_id, entry.name)
    return names


def _appendix(
    *,
    classifications: list[DocClassification],
    extractions: list[Extraction],
    requirements: list[tuple[str, StagedRequirement]],
    uncovered: dict[str, str],
    coverage_rounds: int,
) -> list[str]:
    counts: dict[str, int] = {}
    for _req_id, requirement in requirements:
        for source in set(requirement.sources):
            counts[source] = counts.get(source, 0) + 1
    reasons = {
        item.doc_id: (item.no_requirements_reason or "").strip()
        for item in extractions
        if (item.no_requirements_reason or "").strip()
    }
    by_class = {item.doc_id: item for item in classifications}
    loop_line = (
        f"Coverage loop ran {coverage_rounds} time(s), including the first pass. "
        f"Retry budget after that pass: 2."
    )
    lines = [
        "## Appendix: documents reviewed",
        "",
        loop_line,
        "",
        "| Document | Type | Date | Outcome |",
        "| --- | --- | --- | --- |",
    ]
    for doc_id in sorted(by_class):
        info = by_class[doc_id]
        when = info.date or "—"
        outcome = _outcome(
            doc_id, counts.get(doc_id, 0), reasons.get(doc_id, ""), uncovered
        )
        summary = _cell(info.summary)
        lines.append(
            f"| `{doc_id}` | {info.doc_type} | {when} | {_cell(outcome)} {summary} |"
        )
    lines.append("")
    lines.append("## Uncovered documents")
    lines.append("")
    if not uncovered:
        lines.append(
            "Every document is covered by at least one requirement that cites it, "
            "or by an explicit reason that it states no requirement."
        )
    else:
        lines.append(
            "These documents still failed the coverage check after the retry budget."
        )
        lines.append("")
        for doc_id in sorted(uncovered):
            lines.append(f"- `{doc_id}` — {_cell(uncovered[doc_id])}")
    lines.append("")
    return lines


def _outcome(doc_id: str, count: int, reason: str, uncovered: dict[str, str]) -> str:
    if doc_id in uncovered:
        return f"UNCOVERED ({uncovered[doc_id]})."
    if count:
        noun = "requirement" if count == 1 else "requirements"
        return f"{count} {noun}."
    if reason:
        return f"No requirements: {reason}."
    return "No requirements in the final set."


def _cell(value: str) -> str:
    return " ".join(value.replace("|", "/").split())
