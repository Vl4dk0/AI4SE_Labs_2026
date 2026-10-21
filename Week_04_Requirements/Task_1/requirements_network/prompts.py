"""Instructions for the three model roles.

Each prompt exists so one output spec has an owner: extraction owns completeness
and trace seeds, dedup owns duplicates and conflicts, polish owns one vocabulary.
"""

from __future__ import annotations

import json

from .models import CATEGORIES, DOC_TYPES, PRIORITIES, StagedRequirement

CLASSIFY_SYSTEM = f"""You classify one source document for a library-system requirements effort.

doc_type is the form of the document, not its topic. A text that lists requirements is not a specification just because requirements appear in it. Ignore the doc_id: it is a storage path, not a label.

Absolute rule: if the text has email headers — a line beginning with "From:" and a line beginning with "Subject:", including several of those in one thread — doc_type is email. Stop. A summary of requirements inside the thread, or a statement that they will be added to a requirements document, does not make it a specification or a decision.

Only when there are no email headers, work down this list and stop at the first match. doc_type is exactly one of: {", ".join(DOC_TYPES)}
- email: an email message or a thread of emails. Mail headers (From, To, Cc, Subject, Date) or quoted replies are enough. Classify as email even when the thread summarises requirements, reads like a specification, or records an agreement.
- decision: the document itself is a record of a meeting. The heading or the opening calls it minutes, meeting notes, or a committee, subcommittee, or working-group meeting, and it records what was agreed, decided, or ruled in or out of scope. A meeting that also writes requirements down is still a decision. An email about a meeting is an email, not a decision.
- interview: a question-and-answer conversation with a person about their work. A group meeting is not an interview.
- survey: survey results, a questionnaire, or a write-up of responses (counts, percentages, what respondents asked for).
- specification: a requirements specification or other formal spec as a document in its own right (a spec title, revision, numbered requirements). Not an email, not meeting minutes, not an interview, and not a survey.
- reference: background description of an existing system or product. Not itself the spec for the new work.
- other: none of the above.

date: the date the document was written, as YYYY-MM-DD. For a thread, use the earliest date it states. If it states no date, return null. Do not guess a date from the doc_id.

summary: one sentence describing the document. Do not invent requirements.
"""

EXTRACT_SYSTEM = f"""You extract software requirements for an integrated library system (circulation, catalog, patrons, holds, reports, staff access).

A requirement is something the system must, should, could, or will not do, or a constraint on it. Take it only from the document. Do not invent numbers, actors, or scope.

Return one object per distinct obligation. Do not split one obligation into several, and do not copy it twice. Skip agendas, attendance, and other logistics that never constrain the system.

If the document is a specification, extract the requirements it states, not the surrounding commentary.
If it is a reference description of a current system, extract a requirement only when the text states a need, a gap, or a behavior to carry forward. Do not turn neutral description into a requirement.
If it is an email, interview, survey, or meeting, extract the requests and the decisions about system behavior.

Fields:
- name: a short descriptive name, not a sentence
- description: one paragraph with the concrete actors, conditions, and numbers from the text
- category, exactly one of: {", ".join(CATEGORIES)}
- proposed_priority, exactly one of: {", ".join(PRIORITIES)}
  Must = shall / must / required / decided as in scope
  Should = should / important but not an absolute obligation
  Could = may / could / nice to have / optional
  Won't = explicitly out of scope or will not be done
  When a specification simply states a requirement, use Must. When someone asks or wishes, use Should unless they marked it optional (Could) or refused it (Won't).
- sources: a list containing only the doc_id given in the user message, copied character for character. Never invent another path.

If the document states no software requirement, return an empty requirements list and a non-empty no_requirements_reason that says why. Otherwise set no_requirements_reason to null.
"""

DEDUP_SYSTEM = """You judge one category of candidate requirements. You do not change sources. You rewrite wording only inside a duplicate group you are merging.

Hunt for duplicates. A duplicate is the same obligation said another way: a paraphrase, a shorter restatement, a more formal wording, or the same behavior copied from another document. If implementing one item would already satisfy the other, they are the same requirement even when the sentences share few words. Compare every item with the others. Do not stop after the near-identical sentences.

An added example, a product name, a rationale, or a further constraint on the same behavior is still the same requirement. "Use a relational database" and "Use a relational database, PostgreSQL is the current choice, and do not denormalize reporting" are one requirement. Put every extra condition into merged_description. Do not leave the stricter wording behind as its own row.

They are not duplicates when the obligation itself changes: a different number or threshold, a different actor who must act, a different trigger, or a different scope (one branch versus the whole system). "At most 5 dollars" and "at most 10 dollars" must not be in a duplicate set; they contradict, so they are a conflict. The same topic is not enough to merge. Two statements that cannot both be true are a conflict, not a duplicate. Do not put a pair in both lists.

duplicate_sets: every group you found. For each group, pick keep_id from the group and write merged_name plus merged_description that preserve every concrete condition from every member. Do not shorten away a number or an exception. Do not put ids inside the merged wording.
conflicts: pairs that cannot both be true. Two requirements that can both be built are not a conflict. Say why they contradict, using their names, not their ids.
nonsensical: ids that are not requirements (empty, logistics, or nonsense). Low priority is not nonsense. Out of scope is not nonsense; that is a Won't.

Use only ids from the input. Do not put an id in two duplicate sets. An id may also appear in a conflict. If a list does not apply, return it empty.
"""

CROSS_DEDUP_SYSTEM = """You hunt for duplicate requirements that were filed under different categories.

You receive id, short name, and category only. The within-category pass already ran, so look for the same obligation hiding in two categories: synonyms, a spelling variant, a formal name and a plain name, or a product that implements the requirement. "Relational database back-end" and "Relational PostgreSQL compatibility" are the same obligation. Group them even when the names share few words.

Read every name before you answer. Return every set you find, not only the first.

Do not group items that only share a topic. A different action, scope, actor, or number is a different requirement. "Shelf list" and "overdue fines" are not duplicates.

Return duplicate_sets only. Each set has two or more ids copied exactly from the input, and a keep_id chosen from that set (prefer the more specific name). An id appears in at most one set. If nothing is a cross-category duplicate, return an empty list.
"""

POLISH_SYSTEM = """You normalize wording across library requirements so a reader sees one vocabulary.

The id you are given is the published requirement id. Copy it back unchanged. Do not write any other identifier in the name or the description.

Use these terms:
- patron, not customer, borrower, or user, when the person is a library member
- staff, when the actor works at the library
- item, for a barcoded copy; bibliographic record or title when that is what is meant
- hold, not reserve
- branch, for one library location; library system, for a regional system

Rules:
- Do not add, drop, or merge requirements. Return every id exactly once.
- Do not change sources. Copy each sources list exactly.
- Do not invent facts, numbers, or scope that were not in the text.
- name: a short descriptive name, not a sentence, no trailing period
- description: one paragraph a librarian could implement from, using the concrete details already present. Do not pad with generic filler.

If the source detail is thin, write a shorter paragraph rather than inventing detail.
"""

BLACKLIST_SYSTEM = """You explain why a candidate requirement was discarded.

Write 2 to 4 plain sentences for each entry. Use the kind and the reason you are given. Do not say the requirement was kept. Do not invent sources, meetings, or requirements that are not in the entry. Return every id exactly once, copied from the input.

The id on each entry is a batch index, not a requirement id. A published requirement id looks like REQ-001. If the reason names one, copy that REQ id exactly when you refer to the requirement that survived. Never invent an identifier, and never write an id that starts with T-.
"""


def classify_user(doc_id: str, text: str) -> str:
    # Repeated beside the text. The cheap classifier was labeling a thread
    # as a specification whenever the thread ended in a requirements summary.
    return (
        "If the document has From: and Subject: lines, the type is email. "
        "Do not answer decision or specification for an email. "
        "Minutes or meeting notes are a decision only when the document is not an email.\n\n"
        f"doc_id: {doc_id}\n\nDOCUMENT:\n{text}"
    )


def extract_user(
    doc_id: str,
    text: str,
    *,
    part: int,
    total: int,
    previous_failure: str | None,
) -> str:
    lines = [
        "Copy this doc_id into every sources list, character for character:",
        doc_id,
        "",
    ]
    if total > 1:
        lines.append(
            f"This is part {part} of {total} of one document. "
            "Extract only requirements this part states."
        )
        lines.append("")
    if previous_failure:
        lines.append("The previous extraction failed a deterministic coverage check:")
        lines.append(previous_failure)
        lines.append(
            "Fix that. Every requirement's sources must be exactly "
            f'["{doc_id}"], and at least one requirement must cite it, '
            "or the requirements list must be empty and no_requirements_reason must explain why."
        )
        lines.append("")
    lines.append("DOCUMENT:")
    lines.append(text)
    return "\n".join(lines)


def dedup_user(category: str, requirements: list[StagedRequirement]) -> str:
    payload = [
        {
            "id": item.temp_id,
            "name": item.name,
            "priority": item.priority,
            "sources": item.sources,
            "description": item.description,
        }
        for item in requirements
    ]
    return (
        f"category: {category}\n"
        "Compare every item with the others. Paraphrases of one obligation are duplicates.\n\n"
        f"requirements:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def cross_dedup_user(requirements: list[StagedRequirement], *, partial: bool) -> str:
    payload = [
        {"id": item.temp_id, "name": item.name, "category": item.category}
        for item in requirements
    ]
    # The model only needs the name. Descriptions stay out so the call stays small
    # and the code, not the model, is what unions sources.
    lead = "Find duplicates across categories.\n\n"
    if partial:
        lead = (
            "This is one slice of a larger list, grouped so similar names sit together. "
            "Only return ids from this slice.\n\n"
        )
    return lead + "requirements:\n" + json.dumps(payload, ensure_ascii=False)


def polish_user(requirements: list[StagedRequirement]) -> str:
    # Published ids only. The temporary id is a join key and must not be in the prompt.
    payload = [
        {
            "id": item.public_id or item.temp_id,
            "category": item.category,
            "priority": item.priority,
            "sources": item.sources,
            "name": item.name,
            "description": item.description,
        }
        for item in requirements
    ]
    return json.dumps(payload, ensure_ascii=False)


def blacklist_user(entries: list[dict[str, str]]) -> str:
    return json.dumps(entries, ensure_ascii=False)
