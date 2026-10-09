from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_results(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_markdown(result_sets: list[dict[str, Any]], title: str = "DiffEHR Evaluation Report") -> str:
    lines = [
        f"# {title}",
        "",
        "DiffEHR evaluates whether clinical AI systems satisfy counterfactual contracts: "
        "they should change answers for clinically meaningful record changes and remain "
        "stable for irrelevant or temporally invalid changes.",
        "",
        "## Summary",
        "",
        "| Model | Contracts | Passed | Pass rate | Mean score |",
        "|---|---:|---:|---:|---:|",
    ]
    for payload in result_sets:
        lines.append(
            f"| {payload['model']} | {payload['n_contracts']} | {payload['passed']} | "
            f"{payload['pass_rate']:.2%} | {payload['mean_score']:.3f} |"
        )
    lines.extend(["", "## Research Metrics", ""])
    lines.append("| Model | IVR | IVR 95% CI | DSS | DSS 95% CI | Evidence precision | Evidence recall | Temporal leakage |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for payload in result_sets:
        metrics = payload.get("metrics", {})
        intervals = metrics.get("confidence_intervals", {})
        lines.append(
            f"| {payload['model']} | "
            f"{_fmt_rate(metrics.get('invariance_violation_rate', 0.0))} | "
            f"{_fmt_interval(intervals.get('invariance_violation_rate'))} | "
            f"{_fmt_rate(metrics.get('decisive_sensitivity_score', 0.0))} | "
            f"{_fmt_interval(intervals.get('decisive_sensitivity_score'))} | "
            f"{_fmt_rate(metrics.get('evidence_citation_precision', 0.0))} | "
            f"{_fmt_rate(metrics.get('evidence_citation_recall', 0.0))} | "
            f"{metrics.get('temporal_leakage_violations', 0)} |"
        )
    lines.extend(["", "## Specialty Summary", ""])
    lines.append("| Model | Specialty | Category | Passed | Total | Pass rate |")
    lines.append("|---|---|---|---:|---:|---:|")
    for payload in result_sets:
        for (domain, contract_type), items in _bucket_results(payload).items():
            passed = sum(1 for item in items if item["passed"])
            lines.append(
                f"| {payload['model']} | {domain} | {contract_type} | "
                f"{passed} | {len(items)} | {passed / len(items):.2%} |"
            )
    lines.extend(["", "## Failure Matrix", ""])
    lines.append("| Model | Specialty | Category | Fail rate | Chart |")
    lines.append("|---|---|---|---:|---|")
    matrix_rows: list[tuple[float, str]] = []
    for payload in result_sets:
        for (domain, contract_type), items in _bucket_results(payload).items():
            failed = sum(1 for item in items if not item["passed"])
            rate = failed / len(items)
            matrix_rows.append(
                (
                    rate,
                    f"| {payload['model']} | {domain} | {contract_type} | {rate:.2%} | {_ascii_bar(rate)} |",
                )
            )
    for _, row in sorted(matrix_rows, key=lambda item: item[0], reverse=True):
        lines.append(row)
    lines.extend(["", "## Failure Modes", ""])
    lines.append("| Model | Domain | Contract type | Failed | Total |")
    lines.append("|---|---|---|---:|---:|")
    for payload in result_sets:
        for (domain, contract_type), items in _bucket_results(payload).items():
            failed = sum(1 for item in items if not item["passed"])
            lines.append(f"| {payload['model']} | {domain} | {contract_type} | {failed} | {len(items)} |")
    lines.extend(["", "## Contract Results", ""])
    for payload in result_sets:
        lines.append(f"### {payload['model']}")
        lines.append("")
        lines.append("| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |")
        lines.append("|---|---|---|---:|---|---|---|---|")
        for item in payload["results"]:
            base = item["base"]
            variant = item["variant"]
            relation = "pass" if item["relation_correct"] else "fail"
            lines.append(
                f"| {item['contract_id']} | {item.get('domain', 'unknown')} | {item['contract_type']} | {item['total_score']:.3f} | "
                f"{'yes' if item['passed'] else 'no'} | "
                f"{base['observed_decision']} / {base['expected_decision']} | "
                f"{variant['observed_decision']} / {variant['expected_decision']} | {relation} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "A high static task score does not prove clinical deployment readiness. DiffEHR "
            "separates clinical sensitivity from invariance, temporal validity, and evidence "
            "localization so failures can be traced to concrete chart changes.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_failure_analysis(result_sets: list[dict[str, Any]], title: str = "DiffEHR Failure Analysis") -> str:
    lines = [
        f"# {title}",
        "",
        "This report is generated from machine-readable DiffEHR run outputs. Severity is assigned by benchmark rules, not by autonomous clinical adjudication.",
        "",
        "## Aggregate Patterns",
        "",
        "| Model | Failures | High | Medium | Low | Human review needed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    all_rows: list[dict[str, Any]] = []
    for payload in result_sets:
        rows = [_failure_row(payload, item) for item in payload.get("results", []) if not item.get("passed", False)]
        all_rows.extend(rows)
        severities = {level: sum(1 for row in rows if row["severity"] == level) for level in ("high", "medium", "low")}
        review = sum(1 for row in rows if row["human_review_needed"])
        lines.append(
            f"| {payload['model']} | {len(rows)} | {severities['high']} | "
            f"{severities['medium']} | {severities['low']} | {review} |"
        )

    lines.extend(["", "## Case-Level Failures", ""])
    lines.append("| Model | Contract | Domain | Category | Failed assertion | Severity | Expected | Observed | Evidence issue | Reproduce |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for row in all_rows:
        lines.append(
            f"| {row['model']} | {row['contract_id']} | {row['domain']} | {row['category']} | "
            f"{row['failed_assertion']} | {row['severity']} | {row['expected']} | {row['observed']} | "
            f"{row['evidence_issue']} | `{row['reproduce']}` |"
        )
    if not all_rows:
        lines.append("| none | none | none | none | none | none | none | none | none | none |")
    lines.extend(
        [
            "",
            "## Severity Rules",
            "",
            "- `high`: temporal leakage, safety-related expected decisions, or incorrect task decisions.",
            "- `medium`: relation failure without a temporal or safety marker.",
            "- `low`: evidence-only failure where decisions and relation were correct.",
            "",
            "All failures are marked as needing human review before making any real clinical interpretation.",
        ]
    )
    return "\n".join(lines) + "\n"


def _failure_row(payload: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    base = item["base"]
    variant = item["variant"]
    evidence_issue = _evidence_issue(base, variant)
    temporal = bool(base.get("temporal_leakage_violations") or variant.get("temporal_leakage_violations"))
    decision_failure = not base.get("decision_correct", False) or not variant.get("decision_correct", False)
    relation_failure = not item.get("relation_correct", False)
    failed = []
    if decision_failure:
        failed.append("decision")
    if relation_failure:
        failed.append("relation")
    if evidence_issue != "none":
        failed.append("evidence")
    if temporal:
        failed.append("temporal")
    expected = f"{base['expected_decision']} -> {variant['expected_decision']}"
    observed = f"{base['observed_decision']} -> {variant['observed_decision']}"
    safety_terms = {"unsafe", "contraindicated", "avoid_beta_lactam", "defer"}
    if temporal or base["expected_decision"] in safety_terms or variant["expected_decision"] in safety_terms or decision_failure:
        severity = "high"
    elif relation_failure:
        severity = "medium"
    else:
        severity = "low"
    return {
        "model": payload["model"],
        "contract_id": item["contract_id"],
        "domain": item.get("domain", "unknown"),
        "category": item["contract_type"],
        "failed_assertion": "+".join(failed) if failed else "unknown",
        "severity": severity,
        "expected": expected,
        "observed": observed,
        "evidence_issue": evidence_issue,
        "human_review_needed": True,
        "reproduce": f"PYTHONPATH=src python -m diffehr evaluate examples --model {payload['model']} --out /tmp/{payload['model'].replace(':', '-')}.json",
    }


def _evidence_issue(base: dict[str, Any], variant: dict[str, Any]) -> str:
    issues = []
    if not base.get("citation_correct", False):
        issues.append("base citations")
    if not variant.get("citation_correct", False):
        issues.append("variant citations")
    if base.get("temporal_leakage_violations"):
        issues.append("base temporal leakage")
    if variant.get("temporal_leakage_violations"):
        issues.append("variant temporal leakage")
    return ", ".join(issues) if issues else "none"


def _fmt_rate(value: Any) -> str:
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_interval(value: Any) -> str:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return "n/a"
    return f"{_fmt_rate(value[0])}-{_fmt_rate(value[1])}"


def _ascii_bar(rate: float, width: int = 10) -> str:
    filled = round(rate * width)
    filled = min(width, max(0, filled))
    return "#" * filled + "." * (width - filled)


def _bucket_results(payload: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in payload["results"]:
        key = (item.get("domain", "unknown"), item["contract_type"])
        buckets.setdefault(key, []).append(item)
    return dict(sorted(buckets.items()))


def save_markdown(markdown: str, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
