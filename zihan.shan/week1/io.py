"""JSON loading and normalization utilities."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import pandas as pd


def load_json_records(path: Path) -> list[dict[str, Any]]:
    """Load a JSON file and return a list of records.

    Supports either:
    - a top-level list of record objects
    - a top-level object containing one list-valued field
    """

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return _filter_dict_records(payload, source_label="顶层 list")

    if isinstance(payload, dict):
        list_fields = [(key, value) for key, value in payload.items() if isinstance(value, list)]
        if list_fields:
            selected_key, selected_value = list_fields[0]
            if len(list_fields) > 1:
                field_names = ", ".join(key for key, _ in list_fields)
                warnings.warn(
                    f"JSON 顶层包含多个 list 字段，默认选择第一个字段 '{selected_key}'。可选字段：{field_names}",
                    UserWarning,
                    stacklevel=2,
                )
            return _filter_dict_records(selected_value, source_label=f"字段 '{selected_key}'")

    raise ValueError("Unsupported JSON structure: expected a list or dict containing a list.")


def _filter_dict_records(records: list[Any], source_label: str) -> list[dict[str, Any]]:
    """Keep only dict records and warn when non-dict items are skipped."""

    dict_records = [item for item in records if isinstance(item, dict)]
    skipped_count = len(records) - len(dict_records)
    if skipped_count > 0:
        warnings.warn(
            f"在{source_label}中跳过了 {skipped_count} 条非 dict 记录。",
            UserWarning,
            stacklevel=2,
        )
    return dict_records


def records_to_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert raw records into a pandas DataFrame."""

    if not records:
        return pd.DataFrame()
    return pd.json_normalize(records)

