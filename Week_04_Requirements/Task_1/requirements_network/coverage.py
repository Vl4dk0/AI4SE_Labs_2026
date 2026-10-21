"""Deterministic check that extraction did not drop a source document.

A document is covered when some requirement cites it, or the extractor gave
a real reason that it contains no requirement. Anything else goes back to
extract until the retry budget is spent.
"""

from __future__ import annotations

from .models import MAX_COVERAGE_RETRIES, CoverageFailure, Extraction


def check_coverage(
    doc_ids: list[str], extractions: list[Extraction]
) -> list[CoverageFailure]:
    known = set(doc_ids)
    by_doc = {item.doc_id: item for item in extractions}
    failures: list[CoverageFailure] = []
    for doc_id in doc_ids:
        extraction = by_doc.get(doc_id)
        if extraction is None:
            failures.append(
                CoverageFailure(doc_id=doc_id, reason="no extraction was produced")
            )
            continue
        reason = _problem(doc_id, extraction, known)
        if reason is not None:
            failures.append(CoverageFailure(doc_id=doc_id, reason=reason))
    return failures


def split_retry(
    failures: list[CoverageFailure],
    attempts: dict[str, int],
    max_retries: int = MAX_COVERAGE_RETRIES,
) -> tuple[list[str], list[str]]:
    """Separate documents that may be extracted again from those we give up on.

    ``attempts`` is how many extractions have already finished. The budget is
    the first pass plus ``max_retries`` returns to the extract node.
    """
    requeue: list[str] = []
    uncovered: list[str] = []
    limit = 1 + max_retries
    for failure in failures:
        if attempts.get(failure.doc_id, 0) < limit:
            requeue.append(failure.doc_id)
        else:
            uncovered.append(failure.doc_id)
    return requeue, uncovered


def _problem(doc_id: str, extraction: Extraction, known: set[str]) -> str | None:
    unknown: list[str] = []
    cites_self = False
    for requirement in extraction.requirements:
        for source in requirement.sources:
            if source not in known:
                unknown.append(source)
            if source == doc_id:
                cites_self = True
    problems: list[str] = []
    if unknown:
        listed = ", ".join(sorted(set(unknown)))
        problems.append(f"cited unknown sources: {listed}")
    if extraction.requirements:
        if not cites_self:
            problems.append("no requirement lists this document in sources")
    else:
        reason = (extraction.no_requirements_reason or "").strip()
        if not reason:
            problems.append("no requirements and no no_requirements_reason")
    if not problems:
        return None
    return "; ".join(problems)
