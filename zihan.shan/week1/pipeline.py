"""End-to-end data pipeline for the phase-1 prototype."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from dataclasses import asdict

import pandas as pd

from .cleaning import clean_frame
from .io import load_json_records, records_to_frame
from .stats import calculate_stats


def load_clean_frame(input_path: Path, biomarker_column: str = "biomarker") -> pd.DataFrame:
    """Load JSON data and return a cleaned DataFrame."""

    records = load_json_records(input_path)
    frame = records_to_frame(records)
    return clean_frame(frame, biomarker_column=biomarker_column)


def group_by_biomarker(frame: pd.DataFrame, biomarker_column: str = "biomarker") -> dict[str, pd.DataFrame]:
    """Group a DataFrame by biomarker."""

    if biomarker_column not in frame.columns:
        return {}

    grouped: dict[str, pd.DataFrame] = {}
    for biomarker, group in frame.groupby(biomarker_column, dropna=True):
        biomarker_key = str(biomarker).strip()
        if biomarker_key:
            grouped[biomarker_key] = group.copy()
    return grouped


def build_summary(frame: pd.DataFrame, biomarker_column: str = "biomarker") -> dict[str, Any]:
    """Build a compact summary dictionary for reporting."""

    stats = calculate_stats(frame, biomarker_column=biomarker_column)
    biomarker_groups = group_by_biomarker(frame, biomarker_column=biomarker_column)
    return {
        "stats": asdict(stats),
        "biomarker_group_count": len(biomarker_groups),
    }

