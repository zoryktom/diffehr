from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import Contract
from .dataset import summarize_counterfactual_differences
from .metrics.computation import ContractResult, headline_metrics


def load_results(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload: dict[str, Any] = json.load(handle)
    return payload


def _is_fixture(payload: dict[str, Any]) -> bool:
    return bool(payload.get("run_metadata", {}).get("fixture", False))


def render_markdown(result_sets: list[dict[str, Any]], title: str = "DiffEHR Evaluation Report") -> str:
    real = [payload for payload in result_sets if not _is_fixture(payload)]
    fixtures = [payload for payload in result_sets if _is_fixture(payload)]
    markdown = _render_markdown(real, title)
    if fixtures:
        markdown += "\n## Harness Smoke Test (offline fixtures, not model results)\n\n"
        markdown += (
            "Weights for these models were unavailable (`HF_OFFLINE=1`, not cached). The adapter returned a fixed "
            "fixture response, so these rows only show that the harness runs end to end and say nothing about the models.\n\n"
        )
        markdown += "| Model | Contracts | Passed |\n|---|---:|---:|\n"
        for payload in fixtures:
            markdown += f"| {payload['model']} | {payload['n_contracts']} | {payload['passed']} |\n"
    return markdown


def _render_markdown(result_sets: list[dict[str, Any]], title: str) -> str:
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
    lines.extend(["", "## Executive Summary", ""])
    lines.append("| Adapter/Model | Total Contracts | CFA % | IFR % | TDV % | Mean SDI |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for payload in result_sets:
        metrics = payload.get("metrics", {})
        errors = metrics.get("standard_errors", {})
        intervals = metrics.get("confidence_intervals", {})
        lines.append(
            f"| {payload['model']} | {payload['n_contracts']} | "
            f"{_fmt_with_error(metrics.get('counterfactual_flip_accuracy'), errors.get('counterfactual_flip_accuracy'))} | "
            f"{_fmt_with_error(metrics.get('invariance_failure_rate'), errors.get('invariance_failure_rate'))} | "
            f"{_fmt_with_error(metrics.get('temporal_directional_violation'), errors.get('temporal_directional_violation'))} | "
            f"{float(metrics.get('safety_divergence_index', 0.0)):.3f} "
            f"(SE {float(errors.get('safety_divergence_index', 0.0)):.3f}, "
            f"95% CI {_fmt_decimal_interval(intervals.get('safety_divergence_index'))}) |"
        )
    lines.extend(
        [
            "",
            "Values are percentages with binomial standard error (SE) in parentheses; SDI is a weighted error "
            "fraction (lower is safer) with bootstrap SE and 95% CI. See `docs/METRICS.md`.",
            "",
        ]
    )
    lines.extend(_output_validity_section(result_sets))
    lines.extend(["## Contracts Per Pack And Runtime", ""])
    lines.append(
        "| Model | Policy / architecture | Oncology | Cardiology | Infectious disease | Total | Elapsed (s) | Latency (ms/contract) |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for payload in result_sets:
        counts: dict[str, int] = {}
        for item in payload["results"]:
            counts[item.get("domain", "unknown")] = counts.get(item.get("domain", "unknown"), 0) + 1
        meta = payload.get("run_metadata", {})
        lines.append(
            f"| {payload['model']} | {meta.get('adapter', 'unknown')} | {counts.get('oncology', 0)} | "
            f"{counts.get('cardiology', 0)} | {counts.get('infectious_disease', 0)} | {payload['n_contracts']} | "
            f"{float(meta.get('elapsed_seconds', 0.0)):.3f} | {float(meta.get('mean_latency_ms_per_contract', 0.0)):.3f} |"
        )
    lines.append("")
    lines.extend(["## Metric 95% Bootstrap Confidence Intervals", ""])
    lines.append("| Model | CFA | IFR | TDV |")
    lines.append("|---|---:|---:|---:|")
    for payload in result_sets:
        intervals = payload.get("metrics", {}).get("confidence_intervals", {})
        lines.append(
            f"| {payload['model']} | {_fmt_interval(intervals.get('counterfactual_flip_accuracy'))} | "
            f"{_fmt_interval(intervals.get('invariance_failure_rate'))} | "
            f"{_fmt_interval(intervals.get('temporal_directional_violation'))} |"
        )
    lines.extend(["", "## Breakdown By Domain", ""])
    lines.append("| Model | Domain | Contracts | Passed | CFA % | IFR % | TDV % | Mean SDI |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for payload in result_sets:
        by_domain: dict[str, list[dict[str, Any]]] = {}
        for item in payload["results"]:
            by_domain.setdefault(item.get("domain", "unknown"), []).append(item)
        for domain, items in sorted(by_domain.items()):
            values = headline_metrics([ContractResult.model_validate(item) for item in items])
            lines.append(
                f"| {payload['model']} | {domain} | {len(items)} | {sum(1 for i in items if i['passed'])} | "
                f"{_fmt_rate(values['counterfactual_flip_accuracy'])} | {_fmt_rate(values['invariance_failure_rate'])} | "
                f"{_fmt_rate(values['temporal_directional_violation'])} | {values['safety_divergence_index']:.3f} |"
            )
    lines.extend(["", "## Research Metrics", ""])
    lines.append(
        "| Model | IVR | IVR 95% CI | DSS | DSS 95% CI | Evidence precision | Evidence recall | Temporal leakage |"
    )
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


def _output_validity_section(result_sets: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Output Validity And Decision Accuracy",
        "",
        "Side-level statistics over both charts of every contract. A decision of `unknown` means the output could "
        "not be parsed into an allowed decision; two `unknown` answers on an invariance pair count as unchanged, so "
        "read IFR and TDV together with the unparseable rate. Contract pass additionally requires full citation recall.",
        "",
        "| Model | Decision accuracy | Unparseable decisions | Pairs with changed decision | Mean citation recall |",
        "|---|---:|---:|---:|---:|",
    ]
    for payload in result_sets:
        rows = payload.get("results", [])
        sides = [side for item in rows for side in (item["base"], item["variant"])]
        responses = [item[key] for item in rows for key in ("base_response", "variant_response")]
        if not sides:
            continue
        accuracy = sum(1 for side in sides if side["decision_correct"]) / len(sides)
        unknown = sum(1 for resp in responses if resp["decision"] == "unknown")
        changed = sum(1 for item in rows if item["base_response"]["decision"] != item["variant_response"]["decision"])
        recall = sum(side["citation_recall"] for side in sides) / len(sides)
        lines.append(
            f"| {payload['model']} | {accuracy:.2%} | {unknown}/{len(responses)} ({unknown / len(responses):.2%}) | "
            f"{changed}/{len(rows)} | {recall:.3f} |"
        )
    lines.append("")
    return lines


def render_failure_analysis(
    result_sets: list[dict[str, Any]],
    title: str = "DiffEHR Failure Analysis",
    contracts: list[Contract] | None = None,
    max_details_per_model: int = 12,
) -> str:
    result_sets = [payload for payload in result_sets if not _is_fixture(payload)]
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
    lines.append(
        "| Model | Contract | Domain | Category | Failed assertion | Severity | Expected | Observed | Evidence issue | Reproduce |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for row in all_rows:
        lines.append(
            f"| {row['model']} | {row['contract_id']} | {row['domain']} | {row['category']} | "
            f"{row['failed_assertion']} | {row['severity']} | {row['expected']} | {row['observed']} | "
            f"{row['evidence_issue']} | `{row['reproduce']}` |"
        )
    if not all_rows:
        lines.append("| none | none | none | none | none | none | none | none | none | none |")
    by_id = {contract.id: contract for contract in contracts or []}
    if by_id:
        lines.extend(["", "## Counterfactual Deltas For Failed Contracts", ""])
        lines.append(
            f"Up to {max_details_per_model} highest-severity failures per model are shown with the exact chart delta, "
            "the expected clinical pivot, and the model's recommendation."
        )
        for payload in result_sets:
            rows = [_failure_row(payload, item) for item in payload.get("results", []) if not item.get("passed", False)]
            rows.sort(key=lambda row: {"high": 0, "medium": 1, "low": 2}[row["severity"]])
            for row in rows[:max_details_per_model]:
                contract = by_id.get(row["contract_id"])
                if contract is None:
                    continue
                lines.extend(_failure_detail(payload["model"], row, contract))
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


SAFETY_CONSEQUENCES = {
    "invariance_violation": (
        "A non-clinical attribute changed the recommendation; identical clinical facts would receive different "
        "care by payer or demographics, an equity and liability hazard."
    ),
    "temporal_leakage": (
        "The model cited evidence dated after the decision time; a deployed system would rely on information "
        "that did not yet exist, invalidating retrospective validation and prospective safety claims."
    ),
    "clinical_insensitivity": (
        "A documented pre-decision contraindication (renal, cardiac, hematologic or troponin threshold) did not "
        "change the recommendation; the patient could be treated despite a guideline stop signal."
    ),
}


def _fhir_diff(base: dict[str, Any], variant: dict[str, Any]) -> list[str]:
    def index(chart: dict[str, Any]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for entry in chart.get("entry", []):
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            out[f"{resource.get('resourceType')}/{resource.get('id')}"] = resource
        return out

    before, after = index(base), index(variant)
    lines = []
    for key in sorted(after.keys() - before.keys()):
        lines.append(f"  - added `{key}`: `{json.dumps(after[key], sort_keys=True)}`")
    for key in sorted(before.keys() - after.keys()):
        lines.append(f"  - removed `{key}`")
    for key in sorted(before.keys() & after.keys()):
        if before[key] != after[key]:
            fields = sorted(f for f in set(before[key]) | set(after[key]) if before[key].get(f) != after[key].get(f))
            for field in fields:
                lines.append(
                    f"  - changed `{key}.{field}`: `{json.dumps(before[key].get(field))}` -> `{json.dumps(after[key].get(field))}`"
                )
    return lines or ["  - (no resource-level difference)"]


def render_fuzz_findings(fuzz_payloads: list[dict[str, Any]]) -> str:
    lines = [
        "",
        "## Discovery Fuzzer Findings",
        "",
        "Automated sweeps over `examples/discovery/base_chart.json` (demographic, insurance, clinical-threshold and "
        "temporal-injection families). Each finding shows the FHIR perturbation diff and its safety consequence.",
        "",
        "| Model | Perturbations | Findings | Invariance | Temporal leakage | Clinical insensitivity |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for payload in fuzz_payloads:
        kinds = [f["finding"] for f in payload["findings"]]
        lines.append(
            f"| {payload['model']} | {payload['n_perturbations']} | {payload['n_findings']} | "
            f"{kinds.count('invariance_violation')} | {kinds.count('temporal_leakage')} | "
            f"{kinds.count('clinical_insensitivity')} |"
        )
    for payload in fuzz_payloads:
        for finding in payload["findings"]:
            lines.extend(
                [
                    "",
                    f"### {payload['model']}: {finding['id']} ({finding['finding']})",
                    "",
                    f"- Mutation: `{finding['mutation']}`",
                    f"- Decision: `{finding['base_decision']}` -> `{finding['variant_decision']}`",
                ]
            )
            if finding.get("future_citations"):
                lines.append(f"- Future-dated citations: {', '.join(f'`{c}`' for c in finding['future_citations'])}")
            lines.append("- FHIR perturbation diff:")
            lines.extend(_fhir_diff(finding["base_chart"], finding["variant_chart"]))
            lines.append(f"- Safety consequence: {SAFETY_CONSEQUENCES.get(finding['finding'], 'Needs human review.')}")
    return "\n".join(lines) + "\n"


def _failure_detail(model: str, row: dict[str, Any], contract: Contract) -> list[str]:
    diff = summarize_counterfactual_differences(contract)
    base_items = {item.id: item for item in contract.base_patient.record}
    variant_items = {item.id: item for item in contract.variant_patient.record}
    lines = [
        "",
        f"### {model}: {contract.id}",
        "",
        f"- Task: {contract.task}",
        f"- Failed assertion: {row['failed_assertion']} ({row['severity']})",
    ]
    for key, change in diff["attribute_changes"].items():
        lines.append(f"- Delta (attribute `{key}`): `{change['base']}` -> `{change['variant']}`")
    for entry in diff["record_items_changed"]:
        lines.append(
            f'- Delta (`{entry["id"]}`): "{base_items[entry["id"]].text}" -> "{variant_items[entry["id"]].text}"'
        )
    for item_id in diff["record_items_added"]:
        item = variant_items[item_id]
        lines.append(
            f'- Delta (added `{item_id}`, dated {item.date.isoformat()}, decision date {contract.variant_patient.as_of.isoformat()}): "{item.text}"'
        )
    for item_id in diff["record_items_removed"]:
        lines.append(f"- Delta (removed `{item_id}`)")
    lines.append(f"- Expected clinical pivot: `{row['expected']}`")
    lines.append(f"- Model recommendation: `{row['observed']}`")
    lines.append(f"- Evidence issue: {row['evidence_issue']}")
    return lines


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
    if (
        temporal
        or base["expected_decision"] in safety_terms
        or variant["expected_decision"] in safety_terms
        or decision_failure
    ):
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


def _fmt_with_error(value: Any, error: Any) -> str:
    try:
        return f"{float(value):.2%} (SE {float(error or 0.0) * 100:.2f})"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_decimal_interval(value: Any) -> str:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return "n/a"
    return f"{float(value[0]):.3f}-{float(value[1]):.3f}"


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
