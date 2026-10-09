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
