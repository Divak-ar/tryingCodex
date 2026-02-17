#!/usr/bin/env python3
"""Validator and remediation loop for SAP ABAP requirement-doc RAG designs.

This script evaluates a design spec against requirements and can iteratively
apply deterministic fixes until all checks pass or max iterations is reached.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


REQUIRED_DESIGN_KEYS = {
    "data_sources",
    "chunking",
    "embeddings",
    "vector_store",
    "retrieval",
    "generation",
    "evaluation",
    "feedback_loop",
}

REQUIRED_METADATA_FIELDS = {
    "doc_id",
    "doc_type",
    "module",
    "requirement_id",
    "version",
    "language",
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    fix: str | None = None


@dataclass
class IterationReport:
    iteration: int
    checks: List[CheckResult]
    fixes_applied: List[str]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


class ABAPRAGValidator:
    """Checks whether a RAG design satisfies SAP ABAP requirement-doc needs."""

    def __init__(self, requirements: Dict[str, Any], design: Dict[str, Any]) -> None:
        self.requirements = requirements
        self.design = design

    def evaluate(self) -> List[CheckResult]:
        checks = [
            self._check_top_level_sections(),
            self._check_data_sources(),
            self._check_chunking(),
            self._check_metadata(),
            self._check_retrieval_strategy(),
            self._check_evaluation(),
            self._check_feedback_loop(),
            self._check_security_for_enterprise_docs(),
        ]
        return checks

    def apply_fixes(self, checks: List[CheckResult]) -> List[str]:
        fixes_applied: List[str] = []
        for check in checks:
            if check.passed or not check.fix:
                continue
            if check.fix == "add_missing_top_sections":
                for key in REQUIRED_DESIGN_KEYS:
                    self.design.setdefault(key, {})
                fixes_applied.append("Added missing top-level design sections")
            elif check.fix == "ensure_abap_and_requirements_sources":
                sources = self.design.setdefault("data_sources", {})
                docs = sources.setdefault("supported_doc_types", [])
                for needed in ["ABAP Functional Spec", "ABAP Technical Spec", "Requirement Document"]:
                    if needed not in docs:
                        docs.append(needed)
                sources.setdefault("ingestion_frequency", "daily")
                fixes_applied.append("Added SAP ABAP and requirement-document source coverage")
            elif check.fix == "fix_chunking":
                chunking = self.design.setdefault("chunking", {})
                chunking["strategy"] = "section_aware"
                chunking["max_tokens"] = min(max(chunking.get("max_tokens", 800), 300), 1200)
                chunking["overlap_tokens"] = max(50, min(chunking.get("overlap_tokens", 120), 250))
                fixes_applied.append("Normalized chunking strategy and token window")
            elif check.fix == "add_metadata_fields":
                retr = self.design.setdefault("retrieval", {})
                metadata = retr.setdefault("metadata_fields", [])
                for field in REQUIRED_METADATA_FIELDS:
                    if field not in metadata:
                        metadata.append(field)
                fixes_applied.append("Added ABAP requirement metadata fields")
            elif check.fix == "strengthen_retrieval":
                retr = self.design.setdefault("retrieval", {})
                retr["mode"] = "hybrid"
                retr["reranker"] = retr.get("reranker") or "cross_encoder"
                retr["top_k"] = max(8, int(retr.get("top_k", 0) or 0))
                retr.setdefault("filters", ["module", "language", "version"]) 
                fixes_applied.append("Enabled hybrid retrieval with reranking and filters")
            elif check.fix == "add_eval_metrics":
                ev = self.design.setdefault("evaluation", {})
                metrics = ev.setdefault("metrics", {})
                metrics["groundedness"] = max(float(metrics.get("groundedness", 0.0)), 0.85)
                metrics.setdefault("answer_correctness", 0.80)
                metrics.setdefault("retrieval_recall_at_k", 0.75)
                ev["golden_set_size"] = max(int(ev.get("golden_set_size", 0) or 0), 100)
                fixes_applied.append("Added evaluation metrics and baseline target sizes")
            elif check.fix == "add_feedback_loop":
                fb = self.design.setdefault("feedback_loop", {})
                fb.setdefault("capture_user_feedback", True)
                fb.setdefault("error_taxonomy", ["hallucination", "missed_requirement", "stale_version"])
                fb.setdefault("reindex_trigger", "on_document_update")
                fb.setdefault("prompt_revision_cycle", "weekly")
                fixes_applied.append("Added evaluation-to-improvement feedback loop")
            elif check.fix == "add_security_controls":
                gen = self.design.setdefault("generation", {})
                gen.setdefault("citation_required", True)
                sec = self.design.setdefault("security", {})
                sec.setdefault("row_level_security", True)
                sec.setdefault("pii_redaction", True)
                sec.setdefault("audit_logging", True)
                fixes_applied.append("Added enterprise document security controls")
        return fixes_applied

    def run_improvement_loop(self, max_iterations: int = 3, apply_fixes: bool = True) -> List[IterationReport]:
        reports: List[IterationReport] = []
        for i in range(1, max_iterations + 1):
            checks = self.evaluate()
            fixes: List[str] = []
            if apply_fixes and not all(c.passed for c in checks):
                fixes = self.apply_fixes(checks)
            reports.append(IterationReport(iteration=i, checks=checks, fixes_applied=fixes))
            if all(c.passed for c in checks):
                break
        return reports

    def _check_top_level_sections(self) -> CheckResult:
        missing = sorted(k for k in REQUIRED_DESIGN_KEYS if k not in self.design)
        if missing:
            return CheckResult(
                "top_level_sections",
                False,
                f"Missing design sections: {', '.join(missing)}",
                "add_missing_top_sections",
            )
        return CheckResult("top_level_sections", True, "All top-level sections are present")

    def _check_data_sources(self) -> CheckResult:
        sources = self.design.get("data_sources", {})
        supported = set(sources.get("supported_doc_types", []))
        needed = {"ABAP Functional Spec", "ABAP Technical Spec", "Requirement Document"}
        missing = sorted(needed - supported)
        if missing:
            return CheckResult(
                "data_sources",
                False,
                f"Missing required source doc types: {', '.join(missing)}",
                "ensure_abap_and_requirements_sources",
            )
        return CheckResult("data_sources", True, "Source coverage includes ABAP requirement document types")

    def _check_chunking(self) -> CheckResult:
        cfg = self.design.get("chunking", {})
        strategy = cfg.get("strategy")
        max_tokens = cfg.get("max_tokens", 0)
        overlap = cfg.get("overlap_tokens", 0)
        if strategy != "section_aware" or not (300 <= max_tokens <= 1200) or not (50 <= overlap <= 250):
            return CheckResult(
                "chunking",
                False,
                "Chunking should be section-aware with max_tokens 300-1200 and overlap 50-250",
                "fix_chunking",
            )
        return CheckResult("chunking", True, "Chunking settings look appropriate for requirement docs")

    def _check_metadata(self) -> CheckResult:
        retrieval = self.design.get("retrieval", {})
        metadata = set(retrieval.get("metadata_fields", []))
        missing = sorted(REQUIRED_METADATA_FIELDS - metadata)
        if missing:
            return CheckResult(
                "metadata",
                False,
                f"Missing metadata fields: {', '.join(missing)}",
                "add_metadata_fields",
            )
        return CheckResult("metadata", True, "Metadata fields cover ABAP requirement traceability")

    def _check_retrieval_strategy(self) -> CheckResult:
        retrieval = self.design.get("retrieval", {})
        mode = retrieval.get("mode")
        reranker = retrieval.get("reranker")
        top_k = retrieval.get("top_k", 0)
        if mode != "hybrid" or not reranker or top_k < 5:
            return CheckResult(
                "retrieval_strategy",
                False,
                "Retrieval should use hybrid mode, reranking, and top_k >= 5",
                "strengthen_retrieval",
            )
        return CheckResult("retrieval_strategy", True, "Retrieval strategy meets robustness expectations")

    def _check_evaluation(self) -> CheckResult:
        evaluation = self.design.get("evaluation", {})
        metrics = evaluation.get("metrics", {})
        required = {"groundedness", "answer_correctness", "retrieval_recall_at_k"}
        missing = sorted(required - set(metrics.keys()))
        if missing or evaluation.get("golden_set_size", 0) < 50:
            return CheckResult(
                "evaluation",
                False,
                "Need groundedness/correctness/recall metrics and golden_set_size >= 50",
                "add_eval_metrics",
            )
        return CheckResult("evaluation", True, "Evaluation plan is measurable and sufficient")

    def _check_feedback_loop(self) -> CheckResult:
        fb = self.design.get("feedback_loop", {})
        if not fb.get("capture_user_feedback") or not fb.get("reindex_trigger"):
            return CheckResult(
                "feedback_loop",
                False,
                "Feedback loop must capture user feedback and define a reindex trigger",
                "add_feedback_loop",
            )
        return CheckResult("feedback_loop", True, "Feedback loop supports eval-fix-update-repeat cycle")

    def _check_security_for_enterprise_docs(self) -> CheckResult:
        security = self.design.get("security", {})
        generation = self.design.get("generation", {})
        if not (security.get("row_level_security") and security.get("audit_logging") and generation.get("citation_required")):
            return CheckResult(
                "security",
                False,
                "Enterprise controls require row-level security, audit logging, and citations",
                "add_security_controls",
            )
        return CheckResult("security", True, "Security and citation controls are configured")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def summarize_reports(reports: List[IterationReport]) -> Tuple[bool, List[str]]:
    lines: List[str] = []
    final_passed = reports[-1].passed if reports else False
    for rep in reports:
        lines.append(f"Iteration {rep.iteration}:")
        for check in rep.checks:
            mark = "PASS" if check.passed else "FAIL"
            lines.append(f"  - [{mark}] {check.name}: {check.message}")
        if rep.fixes_applied:
            lines.append("  Fixes applied:")
            for fix in rep.fixes_applied:
                lines.append(f"    * {fix}")
    lines.append(f"Overall status: {'PASS' if final_passed else 'FAIL'}")
    return final_passed, lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate and improve SAP ABAP RAG design.")
    parser.add_argument("--requirements", type=Path, required=False, help="Requirements JSON file (optional)")
    parser.add_argument("--design", type=Path, required=True, help="Design JSON file")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--no-auto-fix", action="store_true", help="Evaluate only, do not apply automatic fixes")
    parser.add_argument("--write-updated-design", action="store_true", help="Persist fixes back to design file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    req = load_json(args.requirements) if args.requirements else {}
    design = load_json(args.design)
    validator = ABAPRAGValidator(req, design)
    reports = validator.run_improvement_loop(max_iterations=args.max_iterations, apply_fixes=not args.no_auto_fix)
    passed, lines = summarize_reports(reports)
    print("\n".join(lines))

    if args.write_updated_design and not args.no_auto_fix:
        write_json(args.design, design)
        print(f"Updated design written to {args.design}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
