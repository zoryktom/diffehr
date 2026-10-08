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
    lines.extend(["", "## Contract Results", ""])
    for payload in result_sets:
        lines.append(f"### {payload['model']}")
        lines.append("")
        lines.append("| Contract | Type | Score | Passed | Base | Variant | Relation |")
        lines.append("|---|---|---:|---|---|---|---|")
        for item in payload["results"]:
            base = item["base"]
            variant = item["variant"]
            relation = "pass" if item["relation_correct"] else "fail"
            lines.append(
                f"| {item['contract_id']} | {item['contract_type']} | {item['total_score']:.3f} | "
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


def save_markdown(markdown: str, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")

