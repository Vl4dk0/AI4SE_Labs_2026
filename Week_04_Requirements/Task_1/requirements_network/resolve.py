"""Apply the model's judgements without letting it move sources around.

Duplicates collapse in code (union of sources, stronger priority). Conflicts
are won by the document that has more authority, then by the newer date.
A genuine tie keeps the more specific wording and is recorded as open.
"""

from __future__ import annotations

import re
from datetime import date

from .models import (
    AUTHORITY_RANK,
    KEPT_MARK,
    PRIORITY_RANK,
    PRIORITY_UP,
    TEMP_ID_RE,
    BlacklistEntry,
    CategoryJudgement,
    ConflictPair,
    CrossDuplicateSet,
    DocClassification,
    DuplicateGroup,
    NonsensicalItem,
    OpenConflict,
    Priority,
    StagedRequirement,
    priority_max,
)


def fold_categories(
    staged: list[StagedRequirement],
    judgements: list[CategoryJudgement],
    classifications: dict[str, DocClassification],
) -> tuple[list[StagedRequirement], list[BlacklistEntry]]:
    """Apply within-category judgements and do not boost yet.

    A later cross-category merge still adds sources. Boosting here would
    raise a requirement on a count that is about to grow.
    """
    staged, dropped = _drop_untraceable(staged, classifications)
    by_category: dict[str, list[StagedRequirement]] = {}
    for requirement in staged:
        by_category.setdefault(requirement.category, []).append(requirement)
    judged = {item.category: item for item in judgements}
    kept: list[StagedRequirement] = []
    blacklist: list[BlacklistEntry] = []
    for group in by_category.values():
        survivors, discarded = _resolve_category(
            group, judged.get(group[0].category), classifications
        )
        kept.extend(survivors)
        blacklist.extend(discarded)
    return kept, [*dropped, *blacklist]


def resolve_requirements(
    staged: list[StagedRequirement],
    judgements: list[CategoryJudgement],
    classifications: dict[str, DocClassification],
) -> tuple[list[StagedRequirement], list[BlacklistEntry]]:
    kept, blacklist = fold_categories(staged, judgements, classifications)
    boosted = [_apply_boost(item, classifications) for item in kept]
    return boosted, blacklist


def confirm_cross_sets(
    proposals: list[CrossDuplicateSet],
    requirements: list[StagedRequirement],
) -> list[DuplicateGroup]:
    """Turn name-only proposals into merge groups the resolver already understands.

    A set that stays inside one category is dropped. That pair was already
    judged with the full text; a second guess from the name alone is weaker.
    """
    by_id = {item.temp_id: item for item in requirements}
    groups: list[DuplicateGroup] = []
    for proposal in proposals:
        seen: list[str] = []
        for raw_id in proposal.member_ids:
            temp_id = raw_id.strip()
            if temp_id in by_id and temp_id not in seen:
                seen.append(temp_id)
        if len(seen) < 2:
            continue
        categories = {by_id[temp_id].category for temp_id in seen}
        if len(categories) < 2:
            continue
        keep_id = proposal.keep_id.strip()
        if keep_id not in seen:
            keep_id = seen[0]
        groups.append(
            DuplicateGroup(
                member_ids=seen,
                keep_id=keep_id,
                merged_name="",
                merged_description=_combined_description(
                    [by_id[temp_id] for temp_id in seen]
                ),
            )
        )
    return groups


def finalize_resolution(
    kept: list[StagedRequirement],
    blacklist: list[BlacklistEntry],
    proposals: list[CrossDuplicateSet],
    classifications: dict[str, DocClassification],
) -> tuple[list[StagedRequirement], list[BlacklistEntry], int, int]:
    """Merge confirmed cross-category duplicates, then boost once.

    ``kept`` must not have been boosted yet. The boost reads the source
    count after every merge, including this one. The last two numbers are
    requirements removed and confirmed sets.
    """
    groups = confirm_cross_sets(proposals, kept)
    merged, blacklist, dropped = _apply_cross_duplicates(kept, blacklist, groups)
    boosted = [_apply_boost(item, classifications) for item in merged]
    return boosted, blacklist, dropped, len(groups)


def _drop_untraceable(
    staged: list[StagedRequirement],
    classifications: dict[str, DocClassification],
) -> tuple[list[StagedRequirement], list[BlacklistEntry]]:
    """A requirement that cites nothing in the corpus cannot be traced (OS4)."""
    known = set(classifications)
    kept: list[StagedRequirement] = []
    dropped: list[BlacklistEntry] = []
    for requirement in staged:
        sources = sorted({source for source in requirement.sources if source in known})
        if not sources:
            dropped.append(
                BlacklistEntry(
                    temp_id=requirement.temp_id,
                    name=requirement.name,
                    description=requirement.description,
                    category=requirement.category,
                    sources=list(requirement.sources),
                    kind="nonsensical",
                    reason="No cited source exists in the corpus, so the requirement cannot be traced.",
                    conflicts_with=None,
                )
            )
            continue
        kept.append(requirement.model_copy(update={"sources": sources}))
    return kept, dropped


def _resolve_category(
    group: list[StagedRequirement],
    judgement: CategoryJudgement | None,
    classifications: dict[str, DocClassification],
) -> tuple[list[StagedRequirement], list[BlacklistEntry]]:
    active = {item.temp_id: item for item in group}
    blacklist: list[BlacklistEntry] = []
    redirect = {item.temp_id: item.temp_id for item in group}
    if judgement is not None:
        _merge_duplicates(active, redirect, judgement.duplicate_sets, blacklist)
        _drop_nonsensical(active, judgement.nonsensical, blacklist)
        _resolve_conflicts(
            active, redirect, judgement.conflicts, classifications, blacklist
        )
    return list(active.values()), blacklist


def _apply_cross_duplicates(
    kept: list[StagedRequirement],
    blacklist: list[BlacklistEntry],
    groups: list[DuplicateGroup],
) -> tuple[list[StagedRequirement], list[BlacklistEntry], int]:
    if not groups:
        return list(kept), list(blacklist), 0
    active = {item.temp_id: item for item in kept}
    redirect = {item.temp_id: item.temp_id for item in kept}
    extra: list[BlacklistEntry] = []
    _merge_duplicates(active, redirect, groups, extra, across_categories=True)
    return list(active.values()), [*blacklist, *extra], len(extra)


def _merge_duplicates(
    active: dict[str, StagedRequirement],
    redirect: dict[str, str],
    duplicate_sets: list[DuplicateGroup],
    blacklist: list[BlacklistEntry],
    *,
    across_categories: bool = False,
) -> None:
    parent = {temp_id: temp_id for temp_id in active}

    def find(temp_id: str) -> str:
        while parent[temp_id] != temp_id:
            parent[temp_id] = parent[parent[temp_id]]
            temp_id = parent[temp_id]
        return temp_id

    valid_sets: list[tuple[str, DuplicateGroup]] = []
    for group in duplicate_sets:
        members = [temp_id for temp_id in group.member_ids if temp_id in active]
        if len(set(members)) < 2:
            continue
        root = find(members[0])
        for temp_id in members[1:]:
            parent[find(temp_id)] = root
        valid_sets.append((root, group))

    components: dict[str, list[str]] = {}
    for temp_id in list(active):
        components.setdefault(find(temp_id), []).append(temp_id)

    for member_ids in components.values():
        unique_members = sorted(set(member_ids))
        if len(unique_members) < 2:
            continue
        related = [
            group for root, group in valid_sets if find(root) == find(unique_members[0])
        ]
        keep_id = _choose_keep(unique_members, related, active)
        keeper = active[keep_id]
        others = [active[temp_id] for temp_id in unique_members if temp_id != keep_id]
        merged = keeper.model_copy(
            update={
                "name": _merged_name(keep_id, related, keeper),
                "description": _merged_description(keep_id, related, keeper),
                "priority": _max_priority([keeper, *others]),
                "sources": _union_sources([keeper, *others]),
            }
        )
        scope = ", filed under a different category" if across_categories else ""
        for other in others:
            # KEPT_MARK is bound to a REQ id once those ids exist. The temp id
            # stays in conflicts_with, which is a join key, not published text.
            blacklist.append(
                BlacklistEntry(
                    temp_id=other.temp_id,
                    name=other.name,
                    description=other.description,
                    category=other.category,
                    sources=list(other.sources),
                    kind="duplicate",
                    reason=(
                        f"Same obligation as {KEPT_MARK} ({merged.name}){scope}. "
                        "Sources were united on the surviving requirement and the "
                        "stronger priority was kept."
                    ),
                    conflicts_with=keep_id,
                )
            )
            del active[other.temp_id]
            redirect[other.temp_id] = keep_id
        active[keep_id] = merged
        redirect[keep_id] = keep_id


def _drop_nonsensical(
    active: dict[str, StagedRequirement],
    items: list[NonsensicalItem],
    blacklist: list[BlacklistEntry],
) -> None:
    names = {temp_id: requirement.name for temp_id, requirement in active.items()}
    for item in items:
        requirement = active.get(item.id)
        if requirement is None:
            continue
        why = item.why.strip() or "The judge marked it as not a real requirement."
        why = _redact(why, names)
        blacklist.append(
            BlacklistEntry(
                temp_id=requirement.temp_id,
                name=requirement.name,
                description=requirement.description,
                category=requirement.category,
                sources=list(requirement.sources),
                kind="nonsensical",
                reason=why,
                conflicts_with=None,
            )
        )
        del active[item.id]


def _resolve_conflicts(
    active: dict[str, StagedRequirement],
    redirect: dict[str, str],
    conflicts: list[ConflictPair],
    classifications: dict[str, DocClassification],
    blacklist: list[BlacklistEntry],
) -> None:
    pairs: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for conflict in conflicts:
        left = redirect.get(conflict.a)
        right = redirect.get(conflict.b)
        if left is None or right is None or left == right:
            continue
        key = (left, right) if left <= right else (right, left)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(
            (left, right, conflict.why.strip() or "The two requirements contradict.")
        )

    # A requirement leaves only when the one that beats it is itself staying.
    # Otherwise a discarded winner would drag its opponent out with it.
    names = {temp_id: requirement.name for temp_id, requirement in active.items()}
    while True:
        losers: dict[str, tuple[str, str, OpenConflict | None]] = {}
        for left_id, right_id, why in pairs:
            if left_id not in active or right_id not in active:
                continue
            winner_id, loser_id, note = _compare(
                active[left_id], active[right_id], classifications, why
            )
            losers[loser_id] = (winner_id, why, note)
        removed = False
        for loser_id, (winner_id, why, note) in losers.items():
            if winner_id in losers or loser_id not in active or winner_id not in active:
                continue
            loser = active.pop(loser_id)
            blacklist.append(
                BlacklistEntry(
                    temp_id=loser.temp_id,
                    name=loser.name,
                    description=loser.description,
                    category=loser.category,
                    sources=list(loser.sources),
                    kind="conflict",
                    reason=_redact(why, names, kept_id=winner_id),
                    conflicts_with=winner_id,
                )
            )
            if note is not None:
                winner = active[winner_id]
                # The note is printed on the survivor, so both ids become names.
                active[winner_id] = winner.model_copy(
                    update={
                        "open_conflicts": [
                            *winner.open_conflicts,
                            note.model_copy(update={"why": _redact(note.why, names)}),
                        ]
                    }
                )
            removed = True
        if not removed:
            break


def _compare(
    left: StagedRequirement,
    right: StagedRequirement,
    classifications: dict[str, DocClassification],
    why: str,
) -> tuple[str, str, OpenConflict | None]:
    left_key = _authority_key(left, classifications)
    right_key = _authority_key(right, classifications)
    if left_key != right_key:
        winner, loser = (left, right) if left_key > right_key else (right, left)
        return winner.temp_id, loser.temp_id, None
    if len(left.description) != len(right.description):
        winner, loser = (
            (left, right)
            if len(left.description) > len(right.description)
            else (right, left)
        )
        tie_break = "specificity"
    else:
        winner, loser = (
            (left, right) if left.temp_id <= right.temp_id else (right, left)
        )
        tie_break = "stable_id"
    note = OpenConflict(other_temp_id=loser.temp_id, why=why, tie_break=tie_break)
    return winner.temp_id, loser.temp_id, note


def _authority_key(
    requirement: StagedRequirement,
    classifications: dict[str, DocClassification],
) -> tuple[int, date]:
    """Best source class, then the newest date among sources of that class.

    A missing date sorts as the oldest day, so an undated source does not
    beat a dated source of the same kind.
    """
    best_rank = -1
    best_dates: list[date] = []
    for source in requirement.sources:
        info = classifications.get(source)
        doc_type = info.doc_type if info is not None else "other"
        rank = AUTHORITY_RANK[doc_type]
        parsed = _parse_date(info.date if info is not None else None)
        if rank > best_rank:
            best_rank = rank
            best_dates = [parsed] if parsed is not None else []
        elif rank == best_rank and parsed is not None:
            best_dates.append(parsed)
    newest = max(best_dates) if best_dates else date.min
    return best_rank, newest


def _apply_boost(
    requirement: StagedRequirement,
    classifications: dict[str, DocClassification],
) -> StagedRequirement:
    backed_by_decision = any(
        (info := classifications.get(source)) is not None
        and info.doc_type == "decision"
        for source in requirement.sources
    )
    if backed_by_decision or len(set(requirement.sources)) >= 3:
        raised = PRIORITY_UP[requirement.priority]
        if raised != requirement.priority:
            return requirement.model_copy(update={"priority": raised})
    return requirement


def _redact(text: str, names: dict[str, str], *, kept_id: str | None = None) -> str:
    """A reason is published later. A temporary id in it must not survive."""

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if kept_id is not None and token == kept_id:
            return KEPT_MARK
        name = names.get(token)
        if name:
            return name
        return "a requirement"

    return TEMP_ID_RE.sub(repl, text)


def _combined_description(members: list[StagedRequirement]) -> str:
    """The cross pass never saw the paragraphs, so the code keeps every one.

    Polish turns the pieces back into a single paragraph. Dropping a member's
    text here would lose a condition the name-only judge could not see.
    """
    parts: list[str] = []
    seen: set[str] = set()
    for item in sorted(members, key=lambda requirement: requirement.temp_id):
        text = item.description.strip()
        if text and text not in seen:
            seen.add(text)
            parts.append(text)
    return "\n\n".join(parts)


def _choose_keep(
    member_ids: list[str],
    groups: list[DuplicateGroup],
    active: dict[str, StagedRequirement],
) -> str:
    nominated = [
        group.keep_id
        for group in groups
        if group.keep_id in member_ids and group.keep_id in active
    ]
    pool = nominated or member_ids
    best = pool[0]
    for temp_id in pool[1:]:
        if _outranks(active[temp_id], active[best]):
            best = temp_id
    return best


def _outranks(candidate: StagedRequirement, current: StagedRequirement) -> bool:
    candidate_rank = PRIORITY_RANK[candidate.priority]
    current_rank = PRIORITY_RANK[current.priority]
    if candidate_rank != current_rank:
        return candidate_rank > current_rank
    if len(candidate.description) != len(current.description):
        return len(candidate.description) > len(current.description)
    return candidate.temp_id < current.temp_id


def _merged_name(
    keep_id: str, groups: list[DuplicateGroup], keeper: StagedRequirement
) -> str:
    for group in groups:
        if group.keep_id == keep_id and group.merged_name.strip():
            return group.merged_name.strip()
    worded = [
        group.merged_name.strip() for group in groups if group.merged_name.strip()
    ]
    if not worded:
        return keeper.name
    return max(worded, key=len)


def _merged_description(
    keep_id: str, groups: list[DuplicateGroup], keeper: StagedRequirement
) -> str:
    for group in groups:
        if group.keep_id == keep_id and group.merged_description.strip():
            return group.merged_description.strip()
    worded = [
        group.merged_description.strip()
        for group in groups
        if group.merged_description.strip()
    ]
    if not worded:
        return keeper.description
    return max(worded, key=len)


def _max_priority(requirements: list[StagedRequirement]) -> Priority:
    best = requirements[0].priority
    for requirement in requirements[1:]:
        best = priority_max(best, requirement.priority)
    return best


def _union_sources(requirements: list[StagedRequirement]) -> list[str]:
    return sorted(
        {source for requirement in requirements for source in requirement.sources}
    )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
