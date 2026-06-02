"""CPT and DRG taxonomy matching."""

from __future__ import annotations

import re

import pandas as pd

from .classification import normalize_column_name


CPT_SOURCE_TABS = ["Raw_MedicalClaims_CPT", "Raw_Outpatient_CPT"]
DRG_SOURCE_TABS = [
    "Raw_MedicalClaims_DRG",
    "Raw_Inpatient_DRG",
    "Raw_Inpatient_Leakage",
    "Raw_Inpatient_MarketShare",
]

CPT_SOURCE_COLUMNS = ["HCPCS/CPT Code", "CPT Code", "HCPCS Code", "CPT/HCPCS Code", "HCPCS CPT Code", "Code"]
DRG_SOURCE_COLUMNS = ["DRG Code", "DRG", "Base DRG Group", "DRG code", "Code"]

CPT_TAXONOMY_COLUMNS = [
    "cpt_code_normalized",
    "ep_category",
    "kpi_domain",
    "include_in_total_ep_charges",
    "include_in_dpci",
    "taxonomy_match_status",
]
DRG_TAXONOMY_COLUMNS = [
    "drg_code_normalized",
    "drg_category",
    "kpi_domain",
    "recommended_use",
    "taxonomy_match_status",
]


def normalize_cpt_code(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    match = re.search(r"[A-Za-z]?\d{4,5}", text)
    return match.group(0).upper() if match else text.upper()


def normalize_drg_code(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    match = re.search(r"\b(\d{3})\b", text)
    return match.group(1) if match else text


def apply_cpt_taxonomy_to_raw_tabs(raw_tab_dataframes: dict[str, pd.DataFrame], cpt_taxonomy: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        source_tab: apply_cpt_taxonomy(df, cpt_taxonomy, source_tab=source_tab)
        for source_tab, df in raw_tab_dataframes.items()
        if source_tab in CPT_SOURCE_TABS
    }


def apply_drg_taxonomy_to_raw_tabs(raw_tab_dataframes: dict[str, pd.DataFrame], drg_taxonomy: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        source_tab: apply_drg_taxonomy(df, drg_taxonomy, source_tab=source_tab)
        for source_tab, df in raw_tab_dataframes.items()
        if source_tab in DRG_SOURCE_TABS
    }


def apply_cpt_taxonomy(df: pd.DataFrame, cpt_taxonomy: pd.DataFrame, source_tab: str = "") -> pd.DataFrame:
    result = df.copy()
    result.insert(0, "source_tab", source_tab)
    source_column = _find_column(result, CPT_SOURCE_COLUMNS)
    if not source_column:
        result["cpt_code_normalized"] = ""
        _add_blank_columns(result, ["ep_category", "kpi_domain", "include_in_total_ep_charges", "include_in_dpci"])
        result["taxonomy_match_status"] = "no_cpt_column"
        return result

    taxonomy = _prepare_cpt_taxonomy(cpt_taxonomy)
    result["cpt_code_normalized"] = result[source_column].map(normalize_cpt_code)
    merged = result.merge(taxonomy, on="cpt_code_normalized", how="left")
    _add_blank_columns(merged, ["ep_category", "kpi_domain", "include_in_total_ep_charges", "include_in_dpci"])
    merged["taxonomy_match_status"] = merged["ep_category"].map(lambda value: "matched" if str(value).strip() else "unmatched")
    return merged


def apply_drg_taxonomy(df: pd.DataFrame, drg_taxonomy: pd.DataFrame, source_tab: str = "") -> pd.DataFrame:
    result = df.copy()
    result.insert(0, "source_tab", source_tab)
    source_column = _find_column(result, DRG_SOURCE_COLUMNS)
    if not source_column:
        result["drg_code_normalized"] = ""
        _add_blank_columns(result, ["drg_category", "kpi_domain", "recommended_use"])
        result["taxonomy_match_status"] = "no_drg_column"
        return result

    taxonomy = _prepare_drg_taxonomy(drg_taxonomy)
    result["drg_code_normalized"] = result[source_column].map(normalize_drg_code)
    merged = result.merge(taxonomy, on="drg_code_normalized", how="left")
    _add_blank_columns(merged, ["drg_category", "kpi_domain", "recommended_use"])
    merged["taxonomy_match_status"] = merged["drg_category"].map(lambda value: "matched" if str(value).strip() else "unmatched")
    return merged


def build_taxonomy_outputs(
    raw_tab_dataframes: dict[str, pd.DataFrame],
    cpt_taxonomy: pd.DataFrame,
    drg_taxonomy: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cpt_matches = apply_cpt_taxonomy_to_raw_tabs(raw_tab_dataframes, cpt_taxonomy)
    drg_matches = apply_drg_taxonomy_to_raw_tabs(raw_tab_dataframes, drg_taxonomy)
    cpt_output = _concat_match_frames(cpt_matches)
    drg_output = _concat_match_frames(drg_matches)
    summary = build_taxonomy_match_summary(cpt_matches, drg_matches)
    return cpt_output, drg_output, summary


def build_taxonomy_match_summary(cpt_matches: dict[str, pd.DataFrame], drg_matches: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for source_tab, df in sorted(cpt_matches.items()):
        rows.append(_summary_row("CPT", source_tab, df, "no_cpt_column"))
    for source_tab, df in sorted(drg_matches.items()):
        rows.append(_summary_row("DRG", source_tab, df, "no_drg_column"))
    return pd.DataFrame(
        rows,
        columns=["taxonomy_type", "source_tab", "total_rows", "matched_rows", "unmatched_rows", "no_code_column_rows", "match_rate"],
    )


def select_cpt_taxonomy_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "source_tab",
        "source_file",
        "source_row_number",
        "detected_file_type",
        "filename_year",
        "reporting_year",
        "cpt_code_normalized",
        "ep_category",
        "kpi_domain",
        "include_in_total_ep_charges",
        "include_in_dpci",
        "taxonomy_match_status",
    ]
    return _select_relevant_columns(df, preferred)


def select_drg_taxonomy_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "source_tab",
        "source_file",
        "source_row_number",
        "detected_file_type",
        "filename_year",
        "reporting_year",
        "drg_code_normalized",
        "drg_category",
        "kpi_domain",
        "recommended_use",
        "taxonomy_match_status",
    ]
    return _select_relevant_columns(df, preferred)


def _prepare_cpt_taxonomy(cpt_taxonomy: pd.DataFrame) -> pd.DataFrame:
    taxonomy = cpt_taxonomy.copy()
    code_column = _find_column(taxonomy, ["cpt_hcpcs_code", "CPT Code", "HCPCS Code", "HCPCS/CPT Code", "code"])
    if not code_column:
        return pd.DataFrame(columns=["cpt_code_normalized", "ep_category", "kpi_domain", "include_in_total_ep_charges", "include_in_dpci"])
    taxonomy["cpt_code_normalized"] = taxonomy[code_column].map(normalize_cpt_code)
    taxonomy = _rename_first_present(taxonomy, ["episode_category", "episode_group"], "ep_category")
    _add_blank_columns(taxonomy, ["ep_category", "kpi_domain", "include_in_total_ep_charges", "include_in_dpci"])
    return taxonomy[["cpt_code_normalized", "ep_category", "kpi_domain", "include_in_total_ep_charges", "include_in_dpci"]].drop_duplicates("cpt_code_normalized")


def _prepare_drg_taxonomy(drg_taxonomy: pd.DataFrame) -> pd.DataFrame:
    taxonomy = drg_taxonomy.copy()
    code_column = _find_column(taxonomy, ["drg_code", "DRG Code", "DRG", "code"])
    if not code_column:
        return pd.DataFrame(columns=["drg_code_normalized", "drg_category", "kpi_domain", "recommended_use"])
    taxonomy["drg_code_normalized"] = taxonomy[code_column].map(normalize_drg_code)
    taxonomy = _rename_first_present(taxonomy, ["episode_category", "episode_group"], "drg_category")
    _add_blank_columns(taxonomy, ["drg_category", "kpi_domain", "recommended_use"])
    return taxonomy[["drg_code_normalized", "drg_category", "kpi_domain", "recommended_use"]].drop_duplicates("drg_code_normalized")


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized = {normalize_column_name(column): column for column in df.columns}
    for candidate in candidates:
        normalized_candidate = normalize_column_name(candidate)
        if normalized_candidate in normalized:
            return normalized[normalized_candidate]
    return None


def _add_blank_columns(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column not in df.columns:
            df[column] = ""
        else:
            df[column] = df[column].fillna("")


def _rename_first_present(df: pd.DataFrame, candidates: list[str], target: str) -> pd.DataFrame:
    if target in df.columns:
        return df
    source = _find_column(df, candidates)
    if source:
        return df.rename(columns={source: target})
    return df


def _concat_match_frames(matches: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if not matches:
        return pd.DataFrame()
    return pd.concat(matches.values(), ignore_index=True, sort=False)


def _summary_row(taxonomy_type: str, source_tab: str, df: pd.DataFrame, no_code_status: str) -> dict[str, object]:
    total_rows = len(df)
    matched_rows = int((df["taxonomy_match_status"] == "matched").sum()) if "taxonomy_match_status" in df.columns else 0
    unmatched_rows = int((df["taxonomy_match_status"] == "unmatched").sum()) if "taxonomy_match_status" in df.columns else 0
    no_code_rows = int((df["taxonomy_match_status"] == no_code_status).sum()) if "taxonomy_match_status" in df.columns else 0
    denominator = total_rows - no_code_rows
    match_rate = round(matched_rows / denominator, 4) if denominator > 0 else 0
    return {
        "taxonomy_type": taxonomy_type,
        "source_tab": source_tab,
        "total_rows": total_rows,
        "matched_rows": matched_rows,
        "unmatched_rows": unmatched_rows,
        "no_code_column_rows": no_code_rows,
        "match_rate": match_rate,
    }


def _select_relevant_columns(df: pd.DataFrame, preferred_columns: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=preferred_columns)
    numeric_columns = [column for column in df.columns if str(column).endswith("__num")]
    selected = [column for column in [*preferred_columns, *numeric_columns] if column in df.columns]
    return df[selected]
