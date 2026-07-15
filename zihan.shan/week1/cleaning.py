"""Cleaning helpers for structured biomarker records."""

from __future__ import annotations

from typing import Any

import pandas as pd


def normalize_text(value: Any) -> str:
    """Convert values to cleaned string form."""

    if value is None:
        return ""
    text = str(value).strip()
    return " ".join(text.split())


def clean_frame(frame: pd.DataFrame, biomarker_column: str = "biomarker") -> pd.DataFrame:
    """Return a cleaned copy of the input DataFrame."""

    cleaned = frame.copy()
    if biomarker_column in cleaned.columns:
        cleaned[biomarker_column] = cleaned[biomarker_column].map(normalize_text)
    cleaned = cleaned.dropna(how="all")
    return cleaned


