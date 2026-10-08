from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .contracts import ContractError, load_contracts
from .models import make_model
from .report import load_results, render_markdown, save_markdown
from .scoring import run_evaluation, save_results


def cmd_validate(args: argparse.Namespace) -> int:
    contracts = load_contracts(args.path)
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

