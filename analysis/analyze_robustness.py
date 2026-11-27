#!/usr/bin/env python3
"""Recompute paper B's reported numbers from the fixed spec and recorded results.

Standard library only. Exits non-zero on inconsistency. No network access.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    spec = load("negative-suite-spec.json")
    results = load("negative-suite-results.json")
    summary = load("negative-suite-summary.json")

    errors = []
    if spec.get("environment", {}).get("toolkit_main") != results.get("toolkit_main"):
        errors.append("negative-suite result toolkit_main does not match the fixed spec")
    case_list = [c["id"] for c in spec["cases"]]
    case_ids = set(case_list)
    judged = [r["id"] for r in results["results"]]
    if len(case_ids) != len(case_list):
        errors.append("fixed spec contains duplicate case IDs")
    if case_ids != set(judged):
        errors.append(f"spec cases {sorted(case_ids)} != judged {sorted(set(judged))}")
    if len(judged) != 23:
        errors.append(f"expected 23 judgments, got {len(judged)}")
    false_accepts = sum(1 for r in results["results"] if r.get("rejected") is False)
    calculated_passes = sum(1 for r in results["results"] if r.get("rejected") is True)
    calculated_fails = len(results["results"]) - calculated_passes
    for index, result in enumerate(results["results"], start=1):
        if result.get("expected") != "REJECTED":
            errors.append(f"result {index} expected value is not REJECTED")
        if type(result.get("rejected")) is not bool:
            errors.append(f"result {index} rejected value is not boolean")
        expected_verdict = "PASS" if result.get("rejected") is True else "FAIL"
        if result.get("verdict") != expected_verdict:
            errors.append(f"result {index} verdict does not match rejection outcome")
    if false_accepts:
        errors.append(f"false accepts: {false_accepts}")
    if results.get("total") != len(judged):
        errors.append("results total does not match judgment rows")
    if results.get("passes") != calculated_passes or results.get("fails") != calculated_fails:
        errors.append("results pass/fail counts do not match judgment rows")
    if results.get("false_accepts") != false_accepts:
        errors.append("results pass/false_accepts mismatch")
    if (
        summary.get("total_judgments") != len(judged)
        or summary.get("passes") != calculated_passes
        or summary.get("false_accepts") != false_accepts
    ):
        errors.append("summary mismatch")

    # The per-case summary is a second representation of the judgment rows.
    summary_by_case = summary.get("by_case", {})
    if set(summary_by_case) != {str(case_id) for case_id in case_ids}:
        errors.append("summary by_case IDs do not match the fixed spec")
    for case_id in case_ids:
        rows = [result for result in results["results"] if result["id"] == case_id]
        summary_rows = summary_by_case.get(str(case_id), [])
        if len(summary_rows) != len(rows):
            errors.append(f"summary by_case {case_id} judgment count mismatch")
            continue
        for row, summary_row in zip(rows, summary_rows):
            if (
                summary_row.get("rejected") is not row.get("rejected")
                or summary_row.get("verdict") != row.get("verdict")
            ):
                errors.append(f"summary by_case {case_id} disagrees with judgment rows")

    # verify PKI-related cases reached a rejection for the right layer
    by_id = {}
    for r in results["results"]:
        by_id.setdefault(r["id"], []).append(r)
    for cid in (13, 14, 15):
        if not by_id.get(cid):
            errors.append(f"PKI case {cid} missing")
        elif not all(r["rejected"] for r in by_id[cid]):
            errors.append(f"PKI case {cid} not rejected")

    out = {
        "spec_cases": len(case_ids),
        "judgments": len(judged),
        "passes": calculated_passes,
        "fails": calculated_fails,
        "false_accepts": false_accepts,
        "pki_cases_tested": [13, 14, 15],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if errors:
        for e in errors:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print("PASS: negative-suite spec/results are internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
