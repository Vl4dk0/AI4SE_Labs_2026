"""Coverage and conflict resolution. No model calls."""

from __future__ import annotations

import unittest

from requirements_network.coverage import check_coverage, split_retry
from requirements_network.models import (
    TEMP_ID_RE,
    BlacklistEntry,
    CategoryJudgement,
    ConflictPair,
    CrossDuplicateSet,
    DocClassification,
    DuplicateGroup,
    Extraction,
    NonsensicalItem,
    OpenConflict,
    RawRequirement,
    StagedRequirement,
)
from requirements_network.render import render_document
from requirements_network.resolve import finalize_resolution, resolve_requirements


def _req(
    temp_id: str,
    *,
    priority: str = "Should",
    sources: list[str],
    description: str = "Do the thing in the usual way.",
    name: str | None = None,
    category: str = "reports",
) -> StagedRequirement:
    return StagedRequirement(
        temp_id=temp_id,
        name=name or temp_id,
        description=description,
        category=category,  # type: ignore[arg-type]
        priority=priority,  # type: ignore[arg-type]
        sources=sources,
    )


def _cls(doc_id: str, doc_type: str, when: str | None) -> DocClassification:
    return DocClassification(
        doc_id=doc_id,
        doc_type=doc_type,  # type: ignore[arg-type]
        date=when,
        summary="source",
    )


class CoverageTests(unittest.TestCase):
    def test_coverage_rules(self) -> None:
        docs = ["a.txt", "b.txt", "c.txt", "d.txt"]
        extractions = [
            Extraction(
                doc_id="a.txt",
                requirements=[
                    RawRequirement(
                        name="Login",
                        description="Staff can sign in.",
                        category="staff_admin_security",
                        proposed_priority="Must",
                        sources=["a.txt"],
                    )
                ],
            ),
            Extraction(
                doc_id="b.txt",
                requirements=[],
                no_requirements_reason="Scheduling note only.",
            ),
            Extraction(doc_id="c.txt", requirements=[], no_requirements_reason="  "),
            Extraction(
                doc_id="d.txt",
                requirements=[
                    RawRequirement(
                        name="Ghost",
                        description="Cites a file that is not in the corpus.",
                        category="other",
                        proposed_priority="Could",
                        sources=["missing.txt"],
                    )
                ],
            ),
        ]
        failures = {
            item.doc_id: item.reason for item in check_coverage(docs, extractions)
        }
        self.assertNotIn("a.txt", failures)
        self.assertNotIn("b.txt", failures)
        self.assertIn("no requirements", failures["c.txt"])
        self.assertIn("unknown sources", failures["d.txt"])
        self.assertIn("no requirement lists this document", failures["d.txt"])

    def test_retry_budget(self) -> None:
        failures = check_coverage(
            ["a.txt"],
            [Extraction(doc_id="a.txt", requirements=[], no_requirements_reason=None)],
        )
        requeue, uncovered = split_retry(failures, {"a.txt": 1})
        self.assertEqual(requeue, ["a.txt"])
        self.assertEqual(uncovered, [])
        requeue, uncovered = split_retry(failures, {"a.txt": 2})
        self.assertEqual(requeue, ["a.txt"])
        requeue, uncovered = split_retry(failures, {"a.txt": 3})
        self.assertEqual(requeue, [])
        self.assertEqual(uncovered, ["a.txt"])


class ResolveTests(unittest.TestCase):
    def test_merge_duplicates_unions_sources_and_keeps_stronger_priority(self) -> None:
        staged = [
            _req("T-reports-001", priority="Could", sources=["email.eml"]),
            _req(
                "T-reports-002",
                priority="Must",
                sources=["spec.txt"],
                description="The shelf report must include branch and item count.",
            ),
        ]
        judgement = CategoryJudgement(
            category="reports",
            duplicate_sets=[
                DuplicateGroup(
                    member_ids=["T-reports-001", "T-reports-002"],
                    keep_id="T-reports-001",
                    merged_name="Shelf report",
                    merged_description="The shelf report must include branch and item count.",
                )
            ],
            conflicts=[],
            nonsensical=[],
        )
        classes = {
            "email.eml": _cls("email.eml", "email", "2009-04-01"),
            "spec.txt": _cls("spec.txt", "specification", "2009-01-27"),
        }
        kept, blacklist = resolve_requirements(staged, [judgement], classes)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].temp_id, "T-reports-001")
        self.assertEqual(kept[0].sources, ["email.eml", "spec.txt"])
        self.assertEqual(kept[0].name, "Shelf report")
        # Must from the merge, then one boost because two sources are not three
        # and neither source is a decision. Must stays Must.
        self.assertEqual(kept[0].priority, "Must")
        self.assertEqual(len(blacklist), 1)
        self.assertEqual(blacklist[0].kind, "duplicate")
        self.assertEqual(blacklist[0].conflicts_with, "T-reports-001")
        self.assertTrue(blacklist[0].reason.startswith("Same obligation as [[KEPT]]"))

    def test_conflict_authority_then_date(self) -> None:
        staged = [
            _req(
                "T-reports-001",
                sources=["mail.eml"],
                description="Reports may be public.",
            ),
            _req(
                "T-reports-002",
                sources=["minutes.txt"],
                description="Reports are staff only.",
            ),
            _req(
                "T-reports-003", sources=["old.txt"], description="Export as CSV only."
            ),
            _req(
                "T-reports-004",
                sources=["new.txt"],
                description="Export as CSV and Excel.",
            ),
        ]
        judgement = CategoryJudgement(
            category="reports",
            duplicate_sets=[],
            conflicts=[
                ConflictPair(
                    a="T-reports-001", b="T-reports-002", why="Public and staff-only."
                ),
                ConflictPair(
                    a="T-reports-003", b="T-reports-004", why="Two export formats."
                ),
            ],
            nonsensical=[],
        )
        classes = {
            "mail.eml": _cls("mail.eml", "email", "2009-08-01"),
            "minutes.txt": _cls("minutes.txt", "decision", "2009-03-15"),
            "old.txt": _cls("old.txt", "interview", "2009-05-01"),
            "new.txt": _cls("new.txt", "interview", "2009-07-01"),
        }
        kept, blacklist = resolve_requirements(staged, [judgement], classes)
        kept_ids = {item.temp_id for item in kept}
        self.assertIn("T-reports-002", kept_ids)
        self.assertNotIn("T-reports-001", kept_ids)
        self.assertIn("T-reports-004", kept_ids)
        self.assertNotIn("T-reports-003", kept_ids)
        kinds = {item.temp_id: item.kind for item in blacklist}
        self.assertEqual(kinds["T-reports-001"], "conflict")
        self.assertEqual(kinds["T-reports-003"], "conflict")

    def test_tie_records_open_conflict_and_keeps_longer_text(self) -> None:
        staged = [
            _req("T-reports-001", sources=["a.txt"], description="Short."),
            _req(
                "T-reports-002",
                sources=["b.txt"],
                description="A longer statement of the same contested obligation.",
            ),
        ]
        judgement = CategoryJudgement(
            category="reports",
            duplicate_sets=[],
            conflicts=[
                ConflictPair(a="T-reports-001", b="T-reports-002", why="They disagree.")
            ],
            nonsensical=[],
        )
        classes = {
            "a.txt": _cls("a.txt", "email", "2009-01-01"),
            "b.txt": _cls("b.txt", "email", "2009-01-01"),
        }
        kept, blacklist = resolve_requirements(staged, [judgement], classes)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].temp_id, "T-reports-002")
        self.assertEqual(len(kept[0].open_conflicts), 1)
        self.assertEqual(kept[0].open_conflicts[0].tie_break, "specificity")
        self.assertEqual(blacklist[0].temp_id, "T-reports-001")

    def test_nonsensical_and_priority_boost(self) -> None:
        staged = [
            _req("T-reports-001", priority="Should", sources=["minutes.txt"]),
            _req(
                "T-reports-002", priority="Could", sources=["a.txt", "b.txt", "c.txt"]
            ),
            _req("T-reports-003", priority="Must", sources=["minutes.txt"]),
            _req("T-reports-004", priority="Could", sources=["nowhere.txt"]),
        ]
        judgement = CategoryJudgement(
            category="reports",
            duplicate_sets=[],
            conflicts=[],
            nonsensical=[
                NonsensicalItem(id="T-reports-003", why="This is only a lunch plan.")
            ],
        )
        classes = {
            "minutes.txt": _cls("minutes.txt", "decision", "2009-03-15"),
            "a.txt": _cls("a.txt", "email", None),
            "b.txt": _cls("b.txt", "survey", None),
            "c.txt": _cls("c.txt", "interview", None),
        }
        kept, blacklist = resolve_requirements(staged, [judgement], classes)
        by_id = {item.temp_id: item for item in kept}
        self.assertEqual(by_id["T-reports-001"].priority, "Must")
        self.assertEqual(by_id["T-reports-002"].priority, "Should")
        self.assertNotIn("T-reports-003", by_id)
        self.assertNotIn("T-reports-004", by_id)
        kinds = {item.temp_id: item.kind for item in blacklist}
        self.assertEqual(kinds["T-reports-003"], "nonsensical")
        self.assertEqual(kinds["T-reports-004"], "nonsensical")

    def test_cross_category_merge_unions_sources_then_boosts(self) -> None:
        staged = [
            _req(
                "T-interoperability-001",
                priority="Should",
                sources=["srs.txt"],
                category="interoperability",
                name="Relational database",
                description="Use a relational database.",
            ),
            _req(
                "T-performance_capacity-004",
                priority="Could",
                sources=["mail.eml", "survey.txt"],
                category="performance_capacity",
                name="SQL storage",
                description="The back-end is a relational database.",
            ),
            _req(
                "T-reports-001",
                priority="Could",
                sources=["survey.txt"],
                category="reports",
                name="Shelf report",
                description="Count shelves.",
            ),
            _req(
                "T-reports-002",
                priority="Could",
                sources=["mail.eml"],
                category="reports",
                name="Shelf counts",
                description="Count the shelves.",
            ),
        ]
        proposals = [
            CrossDuplicateSet(
                member_ids=["T-interoperability-001", "T-performance_capacity-004"],
                keep_id="T-performance_capacity-004",
            ),
            CrossDuplicateSet(
                member_ids=["T-reports-001", "T-reports-002"],
                keep_id="T-reports-001",
            ),
        ]
        classes = {
            "srs.txt": _cls("srs.txt", "specification", "2009-01-27"),
            "mail.eml": _cls("mail.eml", "email", "2009-04-01"),
            "survey.txt": _cls("survey.txt", "survey", "2009-04-25"),
        }
        kept, blacklist, dropped, confirmed = finalize_resolution(
            staged, [], proposals, classes
        )
        self.assertEqual(confirmed, 1)
        self.assertEqual(dropped, 1)
        by_id = {item.temp_id: item for item in kept}
        # The judge named the survivor. The merged priority is still the stronger one.
        self.assertNotIn("T-interoperability-001", by_id)
        self.assertIn("T-performance_capacity-004", by_id)
        self.assertIn("T-reports-001", by_id)
        self.assertIn("T-reports-002", by_id)
        survivor = by_id["T-performance_capacity-004"]
        self.assertEqual(survivor.sources, ["mail.eml", "srs.txt", "survey.txt"])
        # Should from the merge, then one boost because the union has three sources.
        self.assertEqual(survivor.priority, "Must")
        self.assertIn("Use a relational database.", survivor.description)
        self.assertIn("The back-end is a relational database.", survivor.description)
        self.assertEqual(len(blacklist), 1)
        self.assertEqual(blacklist[0].kind, "duplicate")
        self.assertEqual(blacklist[0].conflicts_with, "T-performance_capacity-004")
        self.assertIn("[[KEPT]]", blacklist[0].reason)
        self.assertIn("different category", blacklist[0].reason)
        self.assertNotRegex(blacklist[0].reason, TEMP_ID_RE)


class FormTests(unittest.TestCase):
    def test_mail_headers_force_email(self) -> None:
        from requirements_network.nodes import _email_if_threaded

        thread = "From: a@b.c\nSubject: Hello\n\nPlease add this to the spec."
        self.assertEqual(_email_if_threaded(thread, "reference"), "email")
        self.assertEqual(_email_if_threaded(thread, "specification"), "email")
        self.assertEqual(
            _email_if_threaded("A requirements specification.", "specification"),
            "specification",
        )


class RenderTests(unittest.TestCase):
    def test_published_text_cites_final_ids_only(self) -> None:
        requirement = _req(
            "T-patrons-012",
            name="Patron barcodes",
            sources=["a.txt"],
            category="patrons",
            description="Staff scan a patron barcode.",
        ).model_copy(
            update={
                "public_id": "REQ-004",
                "open_conflicts": [
                    OpenConflict(
                        other_temp_id="T-patrons-099",
                        why="See T-patrons-099 for the other wording.",
                        tie_break="specificity",
                    )
                ],
            }
        )
        entry = BlacklistEntry(
            temp_id="T-patrons-099",
            name="Barcode list",
            description="List patron barcodes.",
            category="patrons",
            sources=["b.txt"],
            kind="duplicate",
            reason="This duplicates [[KEPT]].",
            conflicts_with="T-patrons-012",
        )
        text = render_document(
            generated_on="2026-04-20",
            requirements=[("REQ-004", requirement)],
            blacklist=[(entry, entry.reason)],
            classifications=[
                _cls("a.txt", "email", "2009-01-01"),
                _cls("b.txt", "interview", "2009-02-01"),
            ],
            extractions=[],
            uncovered={},
            coverage_rounds=1,
        )
        self.assertIn("This duplicates REQ-004.", text)
        self.assertIn("Duplicate of REQ-004", text)
        self.assertNotIn("[[KEPT]]", text)
        self.assertNotRegex(text, TEMP_ID_RE)
        self.assertIn("Barcode list", text)


if __name__ == "__main__":
    unittest.main()
