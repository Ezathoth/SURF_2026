"""Dataset statistics helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class DatasetStats:
    """Summary statistics for a loaded dataset."""

    record_count: int
    column_count: int
    biomarker_count: int
    unique_biomarkers: int


def calculate_stats(frame: pd.DataFrame, biomarker_column: str = "biomarker") -> DatasetStats:
    """Calculate basic dataset statistics."""

    biomarker_series = frame.get(biomarker_column, pd.Series(dtype="object"))
    biomarker_series = biomarker_series.dropna()
    biomarker_series = biomarker_series.astype(str).replace({"": pd.NA}).dropna()
    unique_biomarkers = biomarker_series.nunique()
    biomarker_count = int(biomarker_series.shape[0])
    return DatasetStats(
        record_count=int(frame.shape[0]),
        column_count=int(frame.shape[1]),
        biomarker_count=biomarker_count,
        unique_biomarkers=int(unique_biomarkers),
    )

