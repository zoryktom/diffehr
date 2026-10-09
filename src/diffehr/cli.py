from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import make_adapter
from .contracts import ContractError, load_contracts
from .dataset import save_dataset_manifest, validate_dataset_manifest
from .discovery import DiffEHRFuzzer, load_fhir_chart, replay_finding, save_fuzz_results
from .models import make_model
from .report import load_results, render_failure_analysis, render_fuzz_findings, render_markdown, save_markdown
from .scoring import run_evaluation, save_results


def _resolve_root(path: Path | None, manifest: Path | None) -> Path:
    if manifest is not None:
        if not manifest.is_file():
            raise ContractError(f"{manifest}: manifest does not exist")
        return manifest.parent
    if path is None:
        raise ContractError("provide a path or --manifest")
    return path


def cmd_validate(args: argparse.Namespace) -> int:
    root = _resolve_root(args.path, args.manifest)
    contracts = load_contracts(root)
    validate_dataset_manifest(root)
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


def cmd_run(args: argparse.Namespace) -> int:
    contracts = load_contracts(args.pack)
    model = make_adapter(args.adapter, args.model)
    payload = run_evaluation(contracts, model)
    save_results(payload, args.output)
    print(
        f"{payload['model']}: {payload['passed']}/{payload['n_contracts']} passed, "
        f"mean_score={payload['mean_score']:.3f}"
    )
    print(f"Wrote {args.output}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    if args.input_dir is not None:
        paths = sorted(args.input_dir.glob("*.json"))
        if not paths:
            raise ContractError(f"{args.input_dir}: no result JSON files found")
        payloads = [load_results(path) for path in paths]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = args.output_dir / "full_benchmark_report.md"
        failure_path = args.output_dir / "failure_analysis.md"
        save_markdown(render_markdown(payloads, title=args.title), report_path)
        save_markdown(_failure_markdown(args, payloads, "DiffEHR Failure Analysis"), failure_path)
        print(f"Wrote {report_path}")
        print(f"Wrote {failure_path}")
        return 0
    if not args.results:
        raise ContractError("provide result files or --input-dir")
    payloads = [load_results(path) for path in args.results]
    markdown = render_markdown(payloads, title=args.title)
    save_markdown(markdown, args.out)
    print(f"Wrote {args.out}")
    return 0


def _failure_markdown(args: argparse.Namespace, payloads: list, title: str) -> str:
    markdown = render_failure_analysis(payloads, title=title, contracts=_load_contracts_if_present(args.contracts))
    fuzz_dir = getattr(args, "fuzz_dir", None)
    if fuzz_dir is not None:
        if not fuzz_dir.is_dir():
            raise ContractError(f"{fuzz_dir}: fuzz directory does not exist")
        fuzz_payloads = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(fuzz_dir.glob("*.json"))]
        markdown += render_fuzz_findings(fuzz_payloads)
    return markdown


def _load_contracts_if_present(root: Path | None) -> list | None:
    if root is None or not root.exists():
        return None
    return load_contracts(root)


def cmd_failures(args: argparse.Namespace) -> int:
    payloads = [load_results(path) for path in args.results]
    save_markdown(_failure_markdown(args, payloads, args.title), args.out)
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
        f"{payload['model']}: {payload['n_findings']} finding(s) across {payload['n_perturbations']} perturbation(s)."
    )
    print(f"Wrote {args.out}")
    return 0


def cmd_replay_finding(args: argparse.Namespace) -> int:
    payload = replay_finding(args.input, args.finding_id, make_model(args.model))
    save_fuzz_results(payload, args.out)
    print(f"Wrote {args.out}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    root = _resolve_root(args.contracts, args.manifest)
    contracts = load_contracts(root)
    if args.manifest is not None:
        validate_dataset_manifest(root)
    model_names = [name.strip() for name in args.adapters.split(",") if name.strip()] if args.adapters else args.models
    outdir = args.output_dir or args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    result_paths = []
    for model_name in model_names:
        model = make_model(model_name)
        payload = run_evaluation(contracts, model)
        safe_name = model.name.replace(":", "-").replace("/", "-")
        out = outdir / f"{safe_name}.json"
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
    validate.add_argument("path", type=Path, nargs="?")
    validate.add_argument("--manifest", type=Path, help="Validate the dataset rooted at this manifest.json.")
    validate.set_defaults(func=cmd_validate)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate a model on contracts.")
    evaluate.add_argument("contracts", type=Path)
    evaluate.add_argument("--model", default="heuristic")
    evaluate.add_argument("--out", type=Path, default=Path("evidence/runs/results.json"))
    evaluate.set_defaults(func=cmd_evaluate)

    report = subparsers.add_parser("report", help="Render a Markdown report.")
    report.add_argument("results", nargs="*", type=Path)
    report.add_argument(
        "--input-dir", type=Path, help="Directory of result JSON files; writes the full report and failure analysis."
    )
    report.add_argument("--output-dir", type=Path, default=Path("evidence/reports"))
    report.add_argument("--contracts", type=Path, default=Path("examples"))
    report.add_argument(
        "--fuzz-dir", type=Path, help="Directory of fuzz result JSON files appended to the failure analysis."
    )
    report.add_argument("--out", type=Path, default=Path("evidence/reports/report.md"))
    report.add_argument("--title", default="DiffEHR Evaluation Report")
    report.set_defaults(func=cmd_report)

    failures = subparsers.add_parser("failures", help="Render a failure-analysis report.")
    failures.add_argument("results", nargs="+", type=Path)
    failures.add_argument("--out", type=Path, default=Path("evidence/reports/failure_analysis.md"))
    failures.add_argument("--title", default="DiffEHR Failure Analysis")
    failures.add_argument("--fuzz-dir", type=Path, help="Directory of fuzz result JSON files.")
    failures.add_argument(
        "--contracts", type=Path, default=Path("examples"), help="Contract root used to render counterfactual deltas."
    )
    failures.set_defaults(func=cmd_failures)

    run = subparsers.add_parser("run", help="Run one adapter on a contract pack.")
    run.add_argument("--adapter", required=True, help="Registry key: oracle, heuristic, openai, local_hf.")
    run.add_argument("--model", help="Model id for openai or local_hf adapters.")
    run.add_argument("--pack", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.set_defaults(func=cmd_run)

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
    benchmark.add_argument("contracts", type=Path, nargs="?")
    benchmark.add_argument("--manifest", type=Path)
    benchmark.add_argument("--adapters", help="Comma-separated model names, e.g. oracle,heuristic,reckless.")
    benchmark.add_argument("--output-dir", type=Path)
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
