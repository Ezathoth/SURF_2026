"""Sensitivity testing and rank-shift reporting utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .aggregation import build_biomarker_features
from .scoring import ScoringConfig, score_biomarker_features


def load_flattened_tables(flattened_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load biomarker and experiment tables from a flattened output directory."""

    biomarker_path = flattened_dir / "biomarker_table.csv"
    experiment_path = flattened_dir / "experiment_table.csv"
    if not biomarker_path.exists():
        raise FileNotFoundError(f"Missing biomarker table: {biomarker_path}")
    if not experiment_path.exists():
        raise FileNotFoundError(f"Missing experiment table: {experiment_path}")
    return pd.read_csv(biomarker_path), pd.read_csv(experiment_path)


def build_rank_shift_report(
    biomarker_table: pd.DataFrame | list[dict[str, Any]],
    experiment_table: pd.DataFrame | list[dict[str, Any]],
    baseline_config: ScoringConfig,
    comparison_config: ScoringConfig,
    *,
    top_n: int = 20,
) -> dict[str, Any]:
    """Compare biomarker ranks under two scoring configurations."""

    features = build_biomarker_features(biomarker_table, experiment_table)
    baseline_scores = _rank_scores(score_biomarker_features(features, baseline_config), "baseline")
    comparison_scores = _rank_scores(score_biomarker_features(features, comparison_config), "comparison")
    merged = baseline_scores.merge(comparison_scores, on="canonical_biomarker_name", how="outer")
    merged["rank_change"] = merged["baseline_rank"] - merged["comparison_rank"]
    merged["score_change"] = merged["comparison_total_score"] - merged["baseline_total_score"]
    merged = merged.sort_values(
        ["comparison_rank", "canonical_biomarker_name"],
        ascending=[True, True],
        kind="mergesort",
    )

    top_rows = merged.head(top_n).copy()
    return {
        "metadata": {
            "biomarker_count": int(merged.shape[0]),
            "top_n": top_n,
            "rank_change_definition": "baseline_rank - comparison_rank; positive means the biomarker moved up in the comparison config.",
        },
        "top_rank_shift": top_rows.to_dict(orient="records"),
    }


def export_rank_shift_report(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    """Write rank-shift report to JSON and CSV."""

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "rank_shift_report.json"
    csv_path = output_dir / "rank_shift_top20.csv"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(report["top_rank_shift"]).to_csv(csv_path, index=False, encoding="utf-8-sig")
    return {"json": json_path, "csv": csv_path}


def _rank_scores(scores: pd.DataFrame, label: str) -> pd.DataFrame:
    """Return deterministic ranks for a scored biomarker table."""

    ranked = scores.sort_values(
        ["total_score", "canonical_biomarker_name"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked[f"{label}_rank"] = ranked.index + 1
    selected = ranked[
        [
            "canonical_biomarker_name",
            f"{label}_rank",
            "total_score",
            "diagnostic_performance_score",
            "sample_support_score",
            "evidence_completeness_score",
            "consistency_score",
            "clinical_status_score",
        ]
    ].copy()
    selected = selected.rename(
        columns={
            "total_score": f"{label}_total_score",
            "diagnostic_performance_score": f"{label}_diagnostic_performance_score",
            "sample_support_score": f"{label}_sample_support_score",
            "evidence_completeness_score": f"{label}_evidence_completeness_score",
            "consistency_score": f"{label}_consistency_score",
            "clinical_status_score": f"{label}_clinical_status_score",
        }
    )
    return selected
