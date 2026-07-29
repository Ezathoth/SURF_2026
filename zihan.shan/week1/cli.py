"""Command-line entry point for the prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import AppConfig
from .batch import summarize_resolution_statuses
from .batch import iter_input_records
from .export import export_flattened_tables
from .evaluation import build_rank_shift_report
from .evaluation import export_rank_shift_report
from .evaluation import load_flattened_tables
from .flatten import flatten_all_records
from .pipeline import build_summary, load_clean_frame
from .scoring import ScoringConfig


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="MPM biomarker evidence prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Load JSON and print dataset summary")
    summary_parser.add_argument("--input", required=True, help="Path to structured JSON input")
    summary_parser.add_argument("--output-dir", default="outputs", help="Directory for generated outputs")

    audit_parser = subparsers.add_parser("audit", help="Audit synonym resolution across a file or directory")
    audit_parser.add_argument("--input", required=True, help="Path to a JSON file or directory of JSON files")
    audit_parser.add_argument("--output", help="Optional path to write the audit JSON report")
    audit_parser.add_argument("--output-dir", default="outputs", help="Directory for generated outputs")

    flatten_parser = subparsers.add_parser("flatten", help="Export biomarker and experiment tables")
    flatten_parser.add_argument("--input", required=True, help="Path to a JSON file or directory of JSON files")
    flatten_parser.add_argument("--output-dir", default="outputs", help="Directory for generated outputs")

    compare_parser = subparsers.add_parser("compare", help="Compare biomarker ranks across two scoring configs")
    compare_parser.add_argument(
        "--flattened-dir",
        required=True,
        help="Directory containing biomarker_table.csv and experiment_table.csv",
    )
    compare_parser.add_argument(
        "--baseline-config",
        default="configs/scoring_config_v1.json",
        help="Baseline scoring config path",
    )
    compare_parser.add_argument(
        "--comparison-config",
        default="configs/scoring_config_v2_balanced.json",
        help="Comparison scoring config path",
    )
    compare_parser.add_argument("--top-n", type=int, default=20, help="Number of comparison-ranked rows to report")
    compare_parser.add_argument("--output-dir", default="outputs/sensitivity_v2", help="Directory for report outputs")
    return parser.parse_args()


def _run_summary(args: argparse.Namespace) -> int:
    """Run the summary command."""

    config = AppConfig(
        input_path=Path(args.input),
        output_dir=Path(args.output_dir),
    )
    config.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        frame = load_clean_frame(config.input_path, biomarker_column=config.biomarker_column)
        summary = build_summary(frame, biomarker_column=config.biomarker_column)
    except FileNotFoundError:
        print(f"错误：找不到输入文件：{config.input_path}", file=sys.stderr)
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 格式无效，无法解析输入文件：{exc}", file=sys.stderr)
        raise SystemExit(1)
    except ValueError as exc:
        print(f"错误：数据校验失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

    summary_path = config.output_dir / "dataset_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Summary written to: {summary_path}")
    return 0


def _run_audit(args: argparse.Namespace) -> int:
    """Run the audit command."""

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = summarize_resolution_statuses(input_path)
    except FileNotFoundError:
        print(f"错误：找不到输入路径：{input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 格式无效，无法解析输入文件：{exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"错误：数据校验失败：{exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else output_dir / "audit_report.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Audit written to: {output_path}")
    return 0


def _run_flatten(args: argparse.Namespace) -> int:
    """Run the flatten export command."""

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    try:
        records = iter_input_records(input_path)
        flattened = flatten_all_records(records)
        paths = export_flattened_tables(flattened, output_dir)
    except FileNotFoundError:
        print(f"错误：找不到输入路径：{input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 格式无效，无法解析输入文件：{exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"错误：数据校验失败：{exc}", file=sys.stderr)
        return 1

    summary = {
        "biomarker_rows": len(flattened["biomarker_table"]),
        "experiment_rows": len(flattened["experiment_table"]),
        "outputs": {key: str(path) for key, path in paths.items()},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _run_compare(args: argparse.Namespace) -> int:
    """Run rank-shift comparison between two scoring configs."""

    flattened_dir = Path(args.flattened_dir)
    output_dir = Path(args.output_dir)
    try:
        biomarker_table, experiment_table = load_flattened_tables(flattened_dir)
        baseline_config = ScoringConfig.from_json(Path(args.baseline_config))
        comparison_config = ScoringConfig.from_json(Path(args.comparison_config))
        report = build_rank_shift_report(
            biomarker_table,
            experiment_table,
            baseline_config,
            comparison_config,
            top_n=args.top_n,
        )
        paths = export_rank_shift_report(report, output_dir)
    except FileNotFoundError as exc:
        print(f"错误：找不到输入文件：{exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 格式无效，无法解析配置文件：{exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"错误：配置或数据校验失败：{exc}", file=sys.stderr)
        return 1

    rows = report["top_rank_shift"]
    print(json.dumps({"metadata": report["metadata"], "outputs": {k: str(v) for k, v in paths.items()}}, ensure_ascii=False, indent=2))
    if rows:
        print(_format_rank_shift_table(rows))
    return 0


def _format_rank_shift_table(rows: list[dict[str, object]]) -> str:
    """Format rank shift rows as a compact Markdown table."""

    headers = [
        "comparison_rank",
        "baseline_rank",
        "rank_change",
        "canonical_biomarker_name",
        "baseline_total_score",
        "comparison_total_score",
    ]
    lines = [
        "| comparison_rank | baseline_rank | rank_change | biomarker | v1_score | v2_score |",
        "|---:|---:|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['comparison_rank']} | "
            f"{row['baseline_rank']} | "
            f"{row['rank_change']} | "
            f"{row['canonical_biomarker_name']} | "
            f"{float(row['baseline_total_score']):.3f} | "
            f"{float(row['comparison_total_score']):.3f} |"
        )
    return "\n".join(lines)


def main() -> None:
    """Run the CLI entry point."""

    args = parse_args()
    if args.command == "summary":
        raise SystemExit(_run_summary(args))
    if args.command == "audit":
        raise SystemExit(_run_audit(args))
    if args.command == "flatten":
        raise SystemExit(_run_flatten(args))
    if args.command == "compare":
        raise SystemExit(_run_compare(args))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
