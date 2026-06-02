"""KPI eligibility checks.

Phase 6 only determines whether KPIs are eligible to calculate later. It does
not calculate KPI values.
"""

from __future__ import annotations

import pandas as pd


KPI_ELIGIBILITY_COLUMNS = [
    "kpi_id",
    "kpi_name",
    "domain",
    "required_source_tabs",
    "required_taxonomy_type",
    "required_code_category",
    "required_numeric_fields",
    "source_tabs_present",
    "required_fields_present",
    "taxonomy_matches_present",
    "eligibility_status",
    "confidence_status",
    "eligibility_notes",
]


def build_kpi_eligibility(
    metric_definitions: pd.DataFrame,
    raw_tab_dataframes: dict[str, pd.DataFrame],
    cpt_taxonomy_matches: pd.DataFrame,
    drg_taxonomy_matches: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for _, metric in metric_definitions.iterrows():
        kpi_id = str(metric.get("kpi_id", "")).strip()
        if not kpi_id:
            continue
        rows.append(_evaluate_metric(metric, raw_tab_dataframes, cpt_taxonomy_matches, drg_taxonomy_matches))
    return pd.DataFrame(rows, columns=KPI_ELIGIBILITY_COLUMNS)


def _evaluate_metric(
    metric: pd.Series,
    raw_tabs: dict[str, pd.DataFrame],
    cpt_matches: pd.DataFrame,
    drg_matches: pd.DataFrame,
) -> dict[str, object]:
    kpi_id = str(metric.get("kpi_id", "")).strip()
    required_tabs = _split(metric.get("required_source_tabs", ""))
    required_fields = _split(metric.get("required_numeric_fields", ""))
    required_taxonomy_type = str(metric.get("required_taxonomy_type", "")).strip()
    required_categories = _split(metric.get("required_code_category", ""))

    source_tabs_present = _tabs_present(raw_tabs, required_tabs)
    fields_present = _fields_present(raw_tabs, required_tabs, required_fields)
    taxonomy_present = _taxonomy_present(required_taxonomy_type, required_categories, cpt_matches, drg_matches)

    eligibility_status, confidence_status, notes = _status_for_kpi(
        kpi_id,
        source_tabs_present,
        fields_present,
        taxonomy_present,
        required_categories,
        cpt_matches,
    )

    return {
        "kpi_id": kpi_id,
        "kpi_name": metric.get("kpi_name", ""),
        "domain": metric.get("domain", ""),
        "required_source_tabs": metric.get("required_source_tabs", ""),
        "required_taxonomy_type": required_taxonomy_type,
        "required_code_category": metric.get("required_code_category", ""),
        "required_numeric_fields": metric.get("required_numeric_fields", ""),
        "source_tabs_present": source_tabs_present,
        "required_fields_present": fields_present,
        "taxonomy_matches_present": taxonomy_present,
        "eligibility_status": eligibility_status,
        "confidence_status": confidence_status,
        "eligibility_notes": notes,
    }


def _status_for_kpi(
    kpi_id: str,
    source_tabs_present: bool,
    fields_present: bool,
    taxonomy_present: bool,
    required_categories: list[str],
    cpt_matches: pd.DataFrame,
) -> tuple[str, str, str]:
    cpt_strict = {"device_creation_revenue", "device_lifecycle_revenue", "lead_management_revenue"}
    caution = {"total_ep_charges", "device_implant_revenue", "device_implant_volume", "ep_leakage_revenue", "ep_market_share", "market_rank"}

    if kpi_id == "dpci":
        has_creation = _taxonomy_present("CPT", ["Device Creation"], cpt_matches, pd.DataFrame())
        has_lifecycle = _taxonomy_present("CPT", ["Device Lifecycle"], cpt_matches, pd.DataFrame())
        if source_tabs_present and has_creation and has_lifecycle:
            return "eligible", "green", "Device Creation and Device Lifecycle CPT categories are present."
        return "not_eligible", "red", "DPCI requires both Device Creation and Device Lifecycle CPT categories."

    if kpi_id == "net_referral_balance":
        if source_tabs_present and fields_present:
            return "eligible", "green", "Referral from/to tabs and referral count fields are present."
        return "not_eligible", "red", "Requires both referral tabs and # of referrals numeric fields."

    if kpi_id == "geographic_catchment":
        if source_tabs_present and fields_present:
            return "eligible", "green", "ZIP origination tab and case count field are present."
        return "not_eligible", "red", "Requires ZIP origination tab and Medicare Total # of Cases numeric field."

    if kpi_id in cpt_strict:
        if source_tabs_present and fields_present and taxonomy_present:
            return "eligible", "green", f"{'; '.join(required_categories)} CPT category is present."
        return "not_eligible", "red", "Requires Raw_MedicalClaims_CPT, numeric charge field, and matching CPT taxonomy category."

    if kpi_id in caution:
        if source_tabs_present and (taxonomy_present or kpi_id == "market_rank") and fields_present:
            return "eligible_with_caution", "yellow", "Required source evidence is present; later KPI calculation should validate scope assumptions."
        return "not_eligible", "red", "Required source tabs, fields, or taxonomy matches are missing."

    if source_tabs_present and fields_present and (taxonomy_present or not required_categories):
        return "eligible", "green", "Required source evidence is present."
    return "not_eligible", "red", "Required source evidence is missing."


def _split(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def _tabs_present(raw_tabs: dict[str, pd.DataFrame], tabs: list[str]) -> bool:
    if not tabs:
        return True
    if len(tabs) > 1 and any(tab in {"Raw_Inpatient_Leakage", "Raw_Outpatient_Leakage", "Raw_MedicalClaims_DRG", "Raw_Inpatient_DRG"} for tab in tabs):
        return any(not raw_tabs.get(tab, pd.DataFrame()).empty for tab in tabs)
    return all(not raw_tabs.get(tab, pd.DataFrame()).empty for tab in tabs)


def _fields_present(raw_tabs: dict[str, pd.DataFrame], tabs: list[str], fields: list[str]) -> bool:
    if not fields:
        return True
    relevant_frames = [raw_tabs.get(tab, pd.DataFrame()) for tab in tabs if not raw_tabs.get(tab, pd.DataFrame()).empty]
    if not relevant_frames:
        return False
    available = set()
    for df in relevant_frames:
        available.update(df.columns)
    return any(field in available for field in fields)


def _taxonomy_present(
    taxonomy_type: str,
    categories: list[str],
    cpt_matches: pd.DataFrame,
    drg_matches: pd.DataFrame,
) -> bool:
    if not taxonomy_type or not categories:
        return True
    if taxonomy_type.upper() == "CPT":
        return _category_present(cpt_matches, "ep_category", categories)
    if taxonomy_type.upper() == "DRG":
        return _category_present(drg_matches, "drg_category", categories)
    return False


def _category_present(df: pd.DataFrame, column: str, categories: list[str]) -> bool:
    if df.empty or column not in df.columns or "taxonomy_match_status" not in df.columns:
        return False
    matched = df[df["taxonomy_match_status"] == "matched"]
    return matched[column].isin(categories).any()
