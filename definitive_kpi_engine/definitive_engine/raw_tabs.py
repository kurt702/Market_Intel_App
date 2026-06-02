"""Raw tab mapping, numeric cleaning, and raw tab summaries."""

from __future__ import annotations

import re
from collections import defaultdict

import pandas as pd


RAW_TAB_BY_FILE_TYPE = {
    "medicalclaims_cpt_breakdown": "Raw_MedicalClaims_CPT",
    "outpatient_procedure_breakdown": "Raw_Outpatient_CPT",
    "medicalclaims_drg_breakdown": "Raw_MedicalClaims_DRG",
    "inpatient_drg_breakdown": "Raw_Inpatient_DRG",
    "inpatient_leakage": "Raw_Inpatient_Leakage",
    "outpatient_hospital_leakage": "Raw_Outpatient_Leakage",
    "inpatient_marketshare": "Raw_Inpatient_MarketShare",
    "zip_origination": "Raw_ZIP_Origination",
    "referrals_from": "Raw_Referrals_From",
    "referrals_to": "Raw_Referrals_To",
    "unknown": "Raw_Unknown",
}

TRACEABILITY_COLUMNS = [
    "source_file",
    "source_row_number",
    "detected_file_type",
    "filename_year",
    "reporting_year",
    "load_timestamp",
]

UNAVAILABLE_VALUES = {"", "na", "n/a", "null", "none", "suppressed", "unavailable", "--", "-"}


def map_detected_file_type_to_raw_tab(detected_file_type: str) -> str:
    return RAW_TAB_BY_FILE_TYPE.get(detected_file_type, "Raw_Unknown")


def clean_numeric_value(value: object) -> float:
    if pd.isna(value):
        return float("nan")

    text = str(value).strip()
    if text.lower() in UNAVAILABLE_VALUES:
        return float("nan")

    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()")
    cleaned = re.sub(r"[$,%]", "", cleaned)
    cleaned = cleaned.replace(",", "").strip()

    if cleaned.lower() in UNAVAILABLE_VALUES:
        return float("nan")

    try:
        number = float(cleaned)
    except ValueError:
        return float("nan")
    return -number if negative else number


def add_numeric_companion_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in list(result.columns):
        if column in TRACEABILITY_COLUMNS or column.endswith("__num"):
            continue

        cleaned = result[column].map(clean_numeric_value)
        non_blank_original = result[column].map(lambda value: not _is_blank_or_unavailable(value))
        numeric_ratio = cleaned[non_blank_original].notna().mean() if non_blank_original.any() else 0
        if numeric_ratio >= 0.6:
            result[f"{column}__num"] = cleaned
    return result


def build_raw_tab_dataframes(loaded_frames: list[tuple[str, pd.DataFrame]]) -> dict[str, pd.DataFrame]:
    grouped: dict[str, list[pd.DataFrame]] = defaultdict(list)
    for detected_file_type, df in loaded_frames:
        grouped[map_detected_file_type_to_raw_tab(detected_file_type)].append(df)

    return {
        raw_tab_name: pd.concat(frames, ignore_index=True, sort=False)
        for raw_tab_name, frames in grouped.items()
    }


def build_raw_tab_summary(raw_tabs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for raw_tab_name, df in sorted(raw_tabs.items()):
        detected_types = sorted(set(df["detected_file_type"].dropna().astype(str))) if "detected_file_type" in df.columns else []
        source_files = sorted(set(df["source_file"].dropna().astype(str))) if "source_file" in df.columns else []
        rows.append(
            {
                "raw_tab_name": raw_tab_name,
                "detected_file_type": "; ".join(detected_types),
                "row_count": len(df),
                "column_count": len(df.columns),
                "source_files": "; ".join(source_files),
            }
        )
    return pd.DataFrame(rows, columns=["raw_tab_name", "detected_file_type", "row_count", "column_count", "source_files"])


def _is_blank_or_unavailable(value: object) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip().lower() in UNAVAILABLE_VALUES
