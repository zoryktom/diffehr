from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .contracts import ContractError, load_contracts
from .dataset import save_dataset_manifest, validate_dataset_manifest
from .discovery import DiffEHRFuzzer, load_fhir_chart, replay_finding, save_fuzz_results
from .models import make_model
from .report import load_results, render_failure_analysis, render_markdown, save_markdown
from .scoring import run_evaluation, save_results


def cmd_validate(args: argparse.Namespace) -> int:
    contracts = load_contracts(args.path)
    validate_dataset_manifest(args.path)
    print(f"Validated {len(contracts)} contract(s).")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    contracts = load_contracts(args.contracts)
    model = make_model(args.model)
    payload = run_evaluation(contracts, model)
    save_results(payload, args.out)
    print(
        f"{payload['model']}: {payload['passed']}/{payload['n_contracts']} passed, "
        f"mean_score={payload['mean_score']:.3f}"
    )
    print(f"Wrote {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    payloads = [load_results(path) for path in args.results]
    markdown = render_markdown(payloads, title=args.title)
    save_markdown(markdown, args.out)
    print(f"Wrote {args.out}")
    return 0


def cmd_failures(args: argparse.Namespace) -> int:
    payloads = [load_results(path) for path in args.results]
    markdown = render_failure_analysis(payloads, title=args.title)
    save_markdown(markdown, args.out)
    print(f"Wrote {args.out}")
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    path = save_dataset_manifest(args.path)
    print(f"Wrote {path}")
    return 0


def cmd_fuzz(args: argparse.Namespace) -> int:
    chart = load_fhir_chart(args.input)
    model = make_model(args.model)
    fuzzer = DiffEHRFuzzer(model, perturbations=args.perturbations, seed=args.seed)
    payload = fuzzer.run(chart)
    save_fuzz_results(payload, args.out)
    print(
        f"{payload['model']}: {payload['n_findings']} finding(s) across "
        f"{payload['n_perturbations']} perturbation(s)."
    )
    print(f"Wrote {args.out}")
    return 0


def cmd_replay_finding(args: argparse.Namespace) -> int:
    payload = replay_finding(args.input, args.finding_id, make_model(args.model))
    save_fuzz_results(payload, args.out)
    print(f"Wrote {args.out}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    contracts = load_contracts(args.contracts)
    args.outdir.mkdir(parents=True, exist_ok=True)
    result_paths = []
    for model_name in args.models:
        model = make_model(model_name)
        payload = run_evaluation(contracts, model)
        safe_name = model.name.replace(":", "-").replace("/", "-")
        out = args.outdir / f"{safe_name}.json"
        save_results(payload, out)
        result_paths.append(out)
        print(
            f"{payload['model']}: {payload['passed']}/{payload['n_contracts']} passed, "
            f"mean_score={payload['mean_score']:.3f}"
        )
    payloads = [load_results(path) for path in result_paths]
    markdown = render_markdown(payloads, title=args.title)
    save_markdown(markdown, args.report)
    print(f"Wrote {args.report}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diffehr",
        description="Counterfactual contract testing for clinical AI systems.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate contract JSON files.")
    validate.add_argument("path", type=Path)
    validate.set_defaults(func=cmd_validate)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate a model on contracts.")
    evaluate.add_argument("contracts", type=Path)
    evaluate.add_argument("--model", default="heuristic")
    evaluate.add_argument("--out", type=Path, default=Path("evidence/runs/results.json"))
    evaluate.set_defaults(func=cmd_evaluate)

    report = subparsers.add_parser("report", help="Render a Markdown report.")
    report.add_argument("results", nargs="+", type=Path)
    report.add_argument("--out", type=Path, default=Path("evidence/reports/report.md"))
    report.add_argument("--title", default="DiffEHR Evaluation Report")
    report.set_defaults(func=cmd_report)

    failures = subparsers.add_parser("failures", help="Render a failure-analysis report.")
    failures.add_argument("results", nargs="+", type=Path)
    failures.add_argument("--out", type=Path, default=Path("evidence/reports/failure_analysis.md"))
    failures.add_argument("--title", default="DiffEHR Failure Analysis")
    failures.set_defaults(func=cmd_failures)

    manifest = subparsers.add_parser("manifest", help="Generate a dataset manifest with counts and checksums.")
    manifest.add_argument("path", type=Path)
    manifest.set_defaults(func=cmd_manifest)

    fuzz = subparsers.add_parser("fuzz", help="Run automated counterfactual discovery on a FHIR chart.")
    fuzz.add_argument("--input", required=True, type=Path)
    fuzz.add_argument("--perturbations", type=int, default=20)
    fuzz.add_argument("--model", default="heuristic")
    fuzz.add_argument("--seed", type=int, default=2025)
    fuzz.add_argument("--out", type=Path, default=Path("evidence/runs/fuzz_findings.json"))
    fuzz.set_defaults(func=cmd_fuzz)

    replay = subparsers.add_parser("replay-finding", help="Replay one recorded fuzz finding.")
    replay.add_argument("--input", required=True, type=Path)
    replay.add_argument("--finding-id", required=True)
    replay.add_argument("--model", default="heuristic")
    replay.add_argument("--out", type=Path, default=Path("evidence/runs/replayed_finding.json"))
    replay.set_defaults(func=cmd_replay_finding)

    benchmark = subparsers.add_parser("benchmark", help="Evaluate multiple models and render a report.")
    benchmark.add_argument("contracts", type=Path)
    benchmark.add_argument("--models", nargs="+", default=["oracle", "heuristic", "reckless"])
    benchmark.add_argument("--outdir", type=Path, default=Path("evidence/runs"))
    benchmark.add_argument("--report", type=Path, default=Path("evidence/reports/report.md"))
    benchmark.add_argument("--title", default="DiffEHR Benchmark Report")
    benchmark.set_defaults(func=cmd_benchmark)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ContractError as exc:
        print(f"Contract error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
