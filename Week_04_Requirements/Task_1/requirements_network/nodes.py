"""One function per graph node.

LLM nodes only classify, extract, judge, or rephrase. Merging sources,
choosing a conflict winner, and writing the file stay in code so a model
cannot quietly drop a citation.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from .corpus import discover_documents, head_tail, split_text
from .coverage import check_coverage, split_retry
from .llm import ModelRejected, invoke_structured, safe_error
from .models import (
    CATEGORIES,
    BlacklistEntry,
    Category,
    CategoryJudgement,
    CrossDuplicateSet,
    DocClassification,
    DocType,
    Document,
    Extraction,
    LlmBlacklistBatch,
    LlmClassification,
    LlmCrossDedup,
    LlmDedup,
    LlmExtraction,
    LlmPolishBatch,
    LlmPolishedRequirement,
    RawRequirement,
    StagedRequirement,
    normalize_date,
)
from .prompts import (
    BLACKLIST_SYSTEM,
    CLASSIFY_SYSTEM,
    CROSS_DEDUP_SYSTEM,
    DEDUP_SYSTEM,
    EXTRACT_SYSTEM,
    POLISH_SYSTEM,
    blacklist_user,
    classify_user,
    cross_dedup_user,
    dedup_user,
    extract_user,
    polish_user,
)
from .render import (
    assign_ids,
    ordered_for_document,
    present_explanation,
    render_document,
    scrub_temp_ids,
)
from .resolve import finalize_resolution, fold_categories
from .state import NetworkState

_WORKERS = 4
_POLISH_BATCH = 12
# A flat list of every survivor is skimmed and under-calls. Windows stay
# short enough to compare, overlap, and are sorted by name so variants sit together.
_CROSS_ONE_CALL = 80
_CROSS_BATCH = 80
_CROSS_OVERLAP = 20
# The small classifier follows the topic. These two lines are the form.
_MAIL_FROM = re.compile(r"(?m)^From:\s+\S")
_MAIL_SUBJECT = re.compile(r"(?m)^Subject:\s+\S")


def load_corpus(state: NetworkState) -> dict[str, object]:
    documents = discover_documents(Path(state["input_dir"]))
    print(f"[load_corpus] {len(documents)} documents", file=sys.stderr, flush=True)
    return {
        "documents": [item.model_dump() for item in documents],
        "pending_doc_ids": [item.doc_id for item in documents],
    }


def classify_docs(state: NetworkState) -> dict[str, object]:
    documents = _documents(state)

    def one(index: int) -> DocClassification:
        document = documents[index]
        print(f"[classify] {document.doc_id}", file=sys.stderr, flush=True)
        parsed = invoke_structured(
            "classify",
            LlmClassification,
            CLASSIFY_SYSTEM,
            classify_user(document.doc_id, head_tail(document.text)),
        )
        summary = " ".join(parsed.summary.split())
        return DocClassification(
            doc_id=document.doc_id,
            doc_type=_email_if_threaded(document.text, parsed.doc_type),
            date=normalize_date(parsed.date),
            summary=summary[:300],
        )

    classified = _parallel(list(range(len(documents))), one)
    return {"classifications": [item.model_dump() for item in classified]}


def extract(state: NetworkState) -> dict[str, object]:
    documents = {item.doc_id: item for item in _documents(state)}
    pending = list(state["pending_doc_ids"])
    failures = {
        item["doc_id"]: str(item["reason"]) for item in state["coverage_failures"]
    }
    existing = {item["doc_id"]: item for item in state["extractions"]}
    attempts = dict(state["extract_attempts"])

    def one(doc_id: str) -> Extraction:
        document = documents[doc_id]
        previous = failures.get(doc_id) if attempts.get(doc_id, 0) else None
        return _extract_document(document.doc_id, document.text, previous)

    fresh = _parallel(pending, one)
    for extraction in fresh:
        existing[extraction.doc_id] = extraction.model_dump()
        attempts[extraction.doc_id] = attempts.get(extraction.doc_id, 0) + 1
    print(f"[extract] finished {len(fresh)} documents", file=sys.stderr, flush=True)
    return {"extractions": list(existing.values()), "extract_attempts": attempts}


def coverage_check(state: NetworkState) -> dict[str, object]:
    doc_ids = [item.doc_id for item in _documents(state)]
    extractions = [Extraction.model_validate(item) for item in state["extractions"]]
    failures = check_coverage(doc_ids, extractions)
    requeue, uncovered_ids = split_retry(failures, state["extract_attempts"])
    failure_by_id = {item.doc_id: item.reason for item in failures}
    uncovered = [
        {"doc_id": doc_id, "reason": failure_by_id[doc_id]} for doc_id in uncovered_ids
    ]
    rounds = state["coverage_rounds"] + 1
    print(
        f"[coverage] round {rounds}: {len(failures)} failing, {len(requeue)} requeued",
        file=sys.stderr,
        flush=True,
    )
    return {
        "coverage_failures": [item.model_dump() for item in failures],
        "pending_doc_ids": requeue,
        "uncovered": uncovered,
        "coverage_rounds": rounds,
    }


def group_by_category(state: NetworkState) -> dict[str, object]:
    extractions = [Extraction.model_validate(item) for item in state["extractions"]]
    raw: list[RawRequirement] = []
    for extraction in extractions:
        raw.extend(extraction.requirements)
    raw.sort(
        key=lambda item: (
            item.category,
            tuple(item.sources),
            item.name,
            item.description,
        )
    )
    counts = dict.fromkeys(CATEGORIES, 0)
    staged: list[StagedRequirement] = []
    for requirement in raw:
        counts[requirement.category] += 1
        staged.append(
            StagedRequirement(
                temp_id=f"T-{requirement.category}-{counts[requirement.category]:03d}",
                name=requirement.name.strip(),
                description=requirement.description.strip(),
                category=requirement.category,
                priority=requirement.proposed_priority,
                sources=sorted(set(requirement.sources)),
            )
        )
    print(f"[group] {len(staged)} raw requirements", file=sys.stderr, flush=True)
    return {"grouped": [item.model_dump() for item in staged]}


def dedup_conflicts(state: NetworkState) -> dict[str, object]:
    staged = [StagedRequirement.model_validate(item) for item in state["grouped"]]
    groups: dict[Category, list[StagedRequirement]] = {
        category: [] for category in CATEGORIES
    }
    for requirement in staged:
        groups[requirement.category].append(requirement)

    def one(category: Category) -> CategoryJudgement:
        members = groups[category]
        if not members:
            return CategoryJudgement(
                category=category,
                duplicate_sets=[],
                conflicts=[],
                nonsensical=[],
            )
        print(f"[dedup] {category} ({len(members)})", file=sys.stderr, flush=True)
        parsed = invoke_structured(
            "dedup",
            LlmDedup,
            DEDUP_SYSTEM,
            dedup_user(category, members),
        )
        return CategoryJudgement(
            category=category,
            duplicate_sets=list(parsed.duplicate_sets),
            conflicts=list(parsed.conflicts),
            nonsensical=list(parsed.nonsensical),
        )

    nonempty: list[Category] = [
        category for category, members in groups.items() if members
    ]
    judged = _parallel(nonempty, one)
    return {"judgements": [item.model_dump() for item in judged]}


def fold(state: NetworkState) -> dict[str, object]:
    staged = [StagedRequirement.model_validate(item) for item in state["grouped"]]
    judgements = [
        CategoryJudgement.model_validate(item) for item in state["judgements"]
    ]
    classifications = _classifications(state)
    kept, blacklist = fold_categories(staged, judgements, classifications)
    print(
        f"[fold] {len(kept)} survivors, {len(blacklist)} dropped within category",
        file=sys.stderr,
        flush=True,
    )
    return {
        "folded": [item.model_dump() for item in kept],
        "blacklist": [item.model_dump() for item in blacklist],
    }


def cross_dedup(state: NetworkState) -> dict[str, object]:
    folded = [StagedRequirement.model_validate(item) for item in state["folded"]]
    proposals = _ask_cross(folded)
    print(
        f"[cross_dedup] {len(folded)} survivors, {len(proposals)} proposed sets",
        file=sys.stderr,
        flush=True,
    )
    return {"cross_groups": [item.model_dump() for item in proposals]}


def resolve(state: NetworkState) -> dict[str, object]:
    folded = [StagedRequirement.model_validate(item) for item in state["folded"]]
    blacklist = [BlacklistEntry.model_validate(item) for item in state["blacklist"]]
    proposals = [
        CrossDuplicateSet.model_validate(item) for item in state["cross_groups"]
    ]
    classifications = _classifications(state)
    kept, blacklist, dropped, confirmed = finalize_resolution(
        folded, blacklist, proposals, classifications
    )
    print(
        f"[resolve] {len(kept)} kept, {len(blacklist)} blacklisted, "
        f"{confirmed} cross-category sets, {dropped} requirements removed",
        file=sys.stderr,
        flush=True,
    )
    return {
        "resolved": [item.model_dump() for item in kept],
        "blacklist": [item.model_dump() for item in blacklist],
        "cross_dropped": dropped,
    }


def write_document(state: NetworkState) -> dict[str, object]:
    """Rephrase names and explanations. Sources and membership stay put.

    Ids are fixed first. The polish model then sees REQ-xxx in a blacklist
    reason and never sees the temporary id, which is only a join key.
    """
    resolved = [StagedRequirement.model_validate(item) for item in state["resolved"]]
    blacklist = [BlacklistEntry.model_validate(item) for item in state["blacklist"]]
    numbered = assign_ids(resolved)
    resolved = [item for _public, item in numbered]
    id_by_temp = {item.temp_id: item.public_id for item in resolved}
    name_by_temp = {item.temp_id: item.name for item in resolved}
    for entry in blacklist:
        name_by_temp.setdefault(entry.temp_id, entry.name)
    resolved = [_scrub_requirement(item, id_by_temp, name_by_temp) for item in resolved]
    blacklist = [
        entry.model_copy(
            update={
                "reason": present_explanation(
                    entry, entry.reason, id_by_temp, name_by_temp
                )
            }
        )
        for entry in blacklist
    ]
    polished = _polish_requirements(resolved)
    explained = _polish_blacklist(blacklist)
    return {
        "resolved": [item.model_dump() for item in polished],
        "blacklist": [item.model_dump() for item in explained],
    }


def assemble(state: NetworkState) -> dict[str, object]:
    resolved = [StagedRequirement.model_validate(item) for item in state["resolved"]]
    blacklist = [BlacklistEntry.model_validate(item) for item in state["blacklist"]]
    numbered = ordered_for_document(resolved)
    explanations = {entry.temp_id: entry.reason for entry in blacklist}
    markdown = render_document(
        generated_on=date.today().isoformat(),
        requirements=numbered,
        blacklist=[(entry, explanations[entry.temp_id]) for entry in blacklist],
        classifications=[
            DocClassification.model_validate(item) for item in state["classifications"]
        ],
        extractions=[Extraction.model_validate(item) for item in state["extractions"]],
        uncovered={
            str(item["doc_id"]): str(item["reason"]) for item in state["uncovered"]
        },
        coverage_rounds=state["coverage_rounds"],
    )
    output = Path(state["output_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"[assemble] wrote {output}", file=sys.stderr, flush=True)
    return {
        "markdown": markdown,
        "requirement_count": len(numbered),
        "blacklist_count": len(blacklist),
    }


def _email_if_threaded(text: str, doc_type: DocType) -> DocType:
    """Mail headers decide the genre. The model still calls some threads a spec."""
    head = text[:8000]
    if _MAIL_FROM.search(head) and _MAIL_SUBJECT.search(head):
        return "email"
    return doc_type


def _documents(state: NetworkState) -> list[Document]:
    return [Document.model_validate(item) for item in state["documents"]]


def _classifications(state: NetworkState) -> dict[str, DocClassification]:
    return {
        item.doc_id: item
        for item in (
            DocClassification.model_validate(raw) for raw in state["classifications"]
        )
    }


def _ask_cross(folded: list[StagedRequirement]) -> list[CrossDuplicateSet]:
    if len(folded) < 2:
        return []
    batches = _cross_batches(folded)
    proposals: list[CrossDuplicateSet] = []
    partial = len(batches) > 1
    for index, batch in enumerate(batches, start=1):
        print(
            f"[cross_dedup] batch {index}/{len(batches)} ({len(batch)})",
            file=sys.stderr,
            flush=True,
        )
        parsed = invoke_structured(
            "cross_dedup",
            LlmCrossDedup,
            CROSS_DEDUP_SYSTEM,
            cross_dedup_user(batch, partial=partial),
        )
        proposals.extend(parsed.duplicate_sets)
    return proposals


def _cross_batches(
    items: list[StagedRequirement],
) -> list[list[StagedRequirement]]:
    if len(items) <= _CROSS_ONE_CALL:
        return [items]
    ordered = sorted(items, key=lambda item: (item.name.casefold(), item.temp_id))
    step = _CROSS_BATCH - _CROSS_OVERLAP
    batches: list[list[StagedRequirement]] = []
    start = 0
    while start < len(ordered):
        window = ordered[start : start + _CROSS_BATCH]
        if window:
            batches.append(window)
        if start + _CROSS_BATCH >= len(ordered):
            break
        start += step
    return batches


def _scrub_requirement(
    requirement: StagedRequirement,
    id_by_temp: dict[str, str],
    name_by_temp: dict[str, str],
) -> StagedRequirement:
    notes = [
        note.model_copy(
            update={"why": scrub_temp_ids(note.why, id_by_temp, name_by_temp)}
        )
        for note in requirement.open_conflicts
    ]
    return requirement.model_copy(
        update={
            "description": scrub_temp_ids(
                requirement.description, id_by_temp, name_by_temp
            ),
            "open_conflicts": notes,
        }
    )


def _extract_document(
    doc_id: str, text: str, previous_failure: str | None
) -> Extraction:
    parts = split_text(text)
    print(
        f"[extract] {doc_id} ({len(parts)} part(s))",
        file=sys.stderr,
        flush=True,
    )
    requirements: list[RawRequirement] = []
    reasons: list[str] = []
    for index, part in enumerate(parts, start=1):
        parsed = invoke_structured(
            "extract",
            LlmExtraction,
            EXTRACT_SYSTEM,
            extract_user(
                doc_id,
                part,
                part=index,
                total=len(parts),
                previous_failure=previous_failure,
            ),
        )
        for item in parsed.requirements:
            name = item.name.strip()
            description = item.description.strip()
            if not name or not description:
                continue
            requirements.append(
                RawRequirement(
                    name=name,
                    description=description,
                    category=item.category,
                    proposed_priority=item.proposed_priority,
                    sources=list(item.sources),
                )
            )
        if parsed.no_requirements_reason and parsed.no_requirements_reason.strip():
            reasons.append(parsed.no_requirements_reason.strip())
    reason = None if requirements else (" ".join(reasons).strip() or None)
    return Extraction(
        doc_id=doc_id, requirements=requirements, no_requirements_reason=reason
    )


def _polish_requirements(
    requirements: list[StagedRequirement],
) -> list[StagedRequirement]:
    if not requirements:
        return []
    updated: dict[str, StagedRequirement] = {}
    batches = [
        requirements[start : start + _POLISH_BATCH]
        for start in range(0, len(requirements), _POLISH_BATCH)
    ]
    for batch in batches:
        print(f"[polish] {len(batch)} requirements", file=sys.stderr, flush=True)
        try:
            parsed = invoke_structured(
                "polish",
                LlmPolishBatch,
                POLISH_SYSTEM,
                polish_user(batch),
            )
        except ModelRejected:
            raise
        except RuntimeError as exc:
            print(f"[polish] batch kept unpolished: {safe_error(exc)}", file=sys.stderr)
            for requirement in batch:
                updated[requirement.temp_id] = requirement
            continue
        by_id = {item.id: item for item in parsed.requirements}
        for requirement in batch:
            key = requirement.public_id or requirement.temp_id
            updated[requirement.temp_id] = _accept_polish(requirement, by_id.get(key))
    return [updated[item.temp_id] for item in requirements]


def _accept_polish(
    requirement: StagedRequirement,
    polished: LlmPolishedRequirement | None,
) -> StagedRequirement:
    if polished is None:
        return requirement
    if set(polished.sources) != set(requirement.sources):
        return requirement
    name = polished.name.strip()
    description = polished.description.strip()
    if not name or not description:
        return requirement
    return requirement.model_copy(update={"name": name, "description": description})


def _polish_blacklist(entries: list[BlacklistEntry]) -> list[BlacklistEntry]:
    if not entries:
        return []
    # Batch indexes, not temporary ids. The reason already cites REQ-xxx.
    payload = [
        {
            "id": str(index),
            "name": entry.name,
            "kind": entry.kind,
            "reason": entry.reason,
        }
        for index, entry in enumerate(entries, start=1)
    ]
    print(
        f"[polish] {len(entries)} blacklist explanations", file=sys.stderr, flush=True
    )
    try:
        parsed = invoke_structured(
            "polish",
            LlmBlacklistBatch,
            BLACKLIST_SYSTEM,
            blacklist_user(payload),
        )
    except ModelRejected:
        raise
    except RuntimeError as exc:
        print(f"[polish] blacklist kept unpolished: {safe_error(exc)}", file=sys.stderr)
        return entries
    by_id = {item.id: item.explanation.strip() for item in parsed.entries}
    rewritten: list[BlacklistEntry] = []
    for index, entry in enumerate(entries, start=1):
        explanation = by_id.get(str(index), "")
        if not explanation:
            rewritten.append(entry)
            continue
        rewritten.append(entry.model_copy(update={"reason": explanation}))
    return rewritten


def _parallel[T, R](items: list[T], fn: Callable[[T], R]) -> list[R]:
    if not items:
        return []
    results: list[R | None] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=min(_WORKERS, len(items))) as pool:
        futures = {pool.submit(fn, item): index for index, item in enumerate(items)}
        try:
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        except Exception:
            for pending in futures:
                pending.cancel()
            raise
    finished: list[R] = []
    for item in results:
        if item is None:
            raise RuntimeError("a parallel worker produced no result")
        finished.append(item)
    return finished
