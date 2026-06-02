"""KPI calculation-detail tables for Phase 7A.

These functions calculate traceable detail outputs only. They do not create
final KPI summaries, executive workbooks, recommendations, or scores.
"""

from __future__ import annotations

import pandas as pd


DETAIL_COLUMNS = [
    "kpi_id",
    "kpi_name",
    "domain",
    "eligibility_status",
    "confidence_status",
    "calculation_status",
    "calculated_value",
    "unit",
    "source_tab",
    "source_file",
    "source_row_count",
    "matched_row_count",
    "calculation_method",
    "source_value_field",
    "source_count_field",
    "taxonomy_filter",
    "validation_notes",
]


def build_calculation_outputs(
    kpi_eligibility: pd.DataFrame,
    raw_tab_dataframes: dict[str, pd.DataFrame],
    cpt_taxonomy_matches: pd.DataFrame,
    drg_taxonomy_matches: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    detail_rows = []
    cpt_detail_frames = []
    drg_detail_frames = []
    referral_detail = _referral_detail(raw_tab_dataframes)
    geo_detail = _geographic_detail(raw_tab_dataframes)

    for _, eligibility in kpi_eligibility.iterrows():
        row, used = _calculate_one(eligibility, raw_tab_dataframes, cpt_taxonomy_matches, drg_taxonomy_matches, referral_detail, geo_detail)
        detail_rows.append(row)
        if used.get("cpt") is not None and not used["cpt"].empty:
            cpt_detail_frames.append(used["cpt"])
        if used.get("drg") is not None and not used["drg"].empty:
            drg_detail_frames.append(used["drg"])

    return {
        "kpi_calculation_detail": pd.DataFrame(detail_rows, columns=DETAIL_COLUMNS),
        "cpt_calculation_detail": _cpt_detail(pd.concat(cpt_detail_frames, ignore_index=True, sort=False) if cpt_detail_frames else pd.DataFrame()),
        "drg_calculation_detail": _drg_detail(pd.concat(drg_detail_frames, ignore_index=True, sort=False) if drg_detail_frames else pd.DataFrame()),
        "referral_calculation_detail": referral_detail,
        "geographic_catchment_detail": geo_detail,
    }


def _calculate_one(eligibility, raw_tabs, cpt_matches, drg_matches, referral_detail, geo_detail):
    kpi_id = eligibility["kpi_id"]
    base = {
        "kpi_id": kpi_id,
        "kpi_name": eligibility["kpi_name"],
        "domain": eligibility["domain"],
        "eligibility_status": eligibility["eligibility_status"],
        "confidence_status": eligibility["confidence_status"],
        "calculation_status": "not_calculated",
        "calculated_value": "",
        "unit": "",
        "source_tab": "",
        "source_file": "",
        "source_row_count": 0,
        "matched_row_count": 0,
        "calculation_method": "",
        "source_value_field": "",
        "source_count_field": "",
        "taxonomy_filter": "",
        "validation_notes": "",
    }
    if eligibility["eligibility_status"] == "not_eligible":
        base["validation_notes"] = "KPI not eligible; no Phase 7A calculation performed."
        return base, {}

    if kpi_id == "device_creation_revenue":
        return _cpt_sum(base, cpt_matches, "Device Creation", "Actual Charges__num", "calculated")
    if kpi_id == "device_lifecycle_revenue":
        return _cpt_sum(base, cpt_matches, "Device Lifecycle", "Actual Charges__num", "calculated")
    if kpi_id == "lead_management_revenue":
        return _cpt_sum(base, cpt_matches, "Lead Management", "Actual Charges__num", "calculated")
    if kpi_id == "total_ep_charges":
        df = cpt_matches[(cpt_matches.get("taxonomy_match_status") == "matched") & (cpt_matches.get("include_in_total_ep_charges").astype(str).str.upper() == "TRUE")]
        return _sum_rows(base, df, "Actual Charges__num", "", "dollars", "calculated_with_caution", "Raw_MedicalClaims_CPT", "sum Actual Charges__num for include_in_total_ep_charges TRUE", "include_in_total_ep_charges = TRUE", "Current value reflects mapped EP/CIED CPT taxonomy only; not full EP program charges until broader EP CPT taxonomy is added.", "cpt")
    if kpi_id == "dpci":
        df = cpt_matches[(cpt_matches.get("taxonomy_match_status") == "matched") & (cpt_matches.get("ep_category").isin(["Device Creation", "Device Lifecycle"]))]
        return _sum_rows(base, df, "Actual Charges__num", "", "dollars", "calculated", "Raw_MedicalClaims_CPT", "Device Creation Revenue + Device Lifecycle Revenue", "ep_category in Device Creation, Device Lifecycle", "Claims-based proxy for future device/lead-management burden.", "cpt")
    if kpi_id in {"device_implant_revenue", "device_implant_volume"}:
        return _device_implant(base, drg_matches, kpi_id)
    if kpi_id == "ep_leakage_revenue":
        df = drg_matches[(drg_matches.get("source_tab") == "Raw_Inpatient_Leakage") & (drg_matches.get("taxonomy_match_status") == "matched")]
        return _sum_rows(base, df, "Total Charges__num", "", "dollars", "calculated_with_caution", "Raw_Inpatient_Leakage", "sum Total Charges__num for matched inpatient leakage DRG rows", "taxonomy_match_status = matched", "Inpatient DRG-based leakage only; broad outpatient leakage excluded without EP category taxonomy.", "drg")
    if kpi_id == "net_referral_balance":
        value = float(referral_detail.loc[referral_detail["component"] == "net_balance", "referrals"].iloc[0]) if not referral_detail.empty else 0
        base.update({"calculation_status": "calculated", "calculated_value": value, "unit": "referrals", "source_tab": "Raw_Referrals_From; Raw_Referrals_To", "source_row_count": int(referral_detail["source_row_count"].sum()) if not referral_detail.empty else 0, "calculation_method": "sum referrals_from # of referrals__num - sum referrals_to # of referrals__num", "source_count_field": "# of referrals__num", "validation_notes": "Incoming, outgoing, and net referral detail rows created."})
        return base, {}
    if kpi_id == "geographic_catchment":
        value = float(geo_detail["Medicare Total # of Cases__num"].sum()) if not geo_detail.empty else 0
        base.update({"calculation_status": "calculated", "calculated_value": value, "unit": "cases", "source_tab": "Raw_ZIP_Origination", "source_row_count": len(raw_tabs.get("Raw_ZIP_Origination", pd.DataFrame())), "matched_row_count": len(geo_detail), "calculation_method": "top 25 ZIP codes by Medicare Total # of Cases__num", "source_count_field": "Medicare Total # of Cases__num", "validation_notes": "Calculated as total cases represented by top 25 ZIPs."})
        return base, {}
    if kpi_id == "ep_market_share":
        return _market_share(base, drg_matches)
    if kpi_id == "market_rank":
        base.update({"calculation_status": "not_calculated", "unit": "rank", "source_tab": "Raw_Inpatient_MarketShare", "validation_notes": "Market rank requires competitor-level market share rows and ranking logic; not calculated in Phase 7A."})
        return base, {}
    return base, {}


def _cpt_sum(base, cpt_matches, category, field, status):
    df = cpt_matches[(cpt_matches.get("taxonomy_match_status") == "matched") & (cpt_matches.get("ep_category") == category)]
    return _sum_rows(base, df, field, "", "dollars", status, "Raw_MedicalClaims_CPT", f"sum {field} for {category}", f"ep_category = {category}", f"{category} CPT rows summed from matched taxonomy detail.", "cpt")


def _device_implant(base, drg_matches, kpi_id):
    categories = ["Core CIED Implant", "Core CIED Implant / Lifecycle"]
    df = drg_matches[(drg_matches.get("taxonomy_match_status") == "matched") & (drg_matches.get("drg_category").isin(categories))]
    med = df[df.get("source_tab") == "Raw_MedicalClaims_DRG"]
    inp = df[df.get("source_tab") == "Raw_Inpatient_DRG"]
    if kpi_id == "device_implant_revenue":
        if "Actual Charges__num" in med.columns and not med.empty:
            return _sum_rows(base, med, "Actual Charges__num", "", "dollars", "calculated_with_caution", "Raw_MedicalClaims_DRG", "sum Actual Charges__num for core CIED DRGs", "drg_category in Core CIED Implant, Core CIED Implant / Lifecycle", "DRG-based measure, not pure CPT procedural revenue.", "drg")
        return _sum_rows(base, inp, "Medicare Total Charges__num", "", "dollars", "calculated_with_caution", "Raw_Inpatient_DRG", "sum Medicare Total Charges__num for core CIED DRGs", "drg_category in Core CIED Implant, Core CIED Implant / Lifecycle", "Fallback inpatient DRG-based measure, not pure CPT procedural revenue.", "drg")
    if " # Actual Claims__num" in med.columns:
        pass
    if "# Actual Claims__num" in med.columns and not med.empty:
        return _sum_rows(base, med, "", "# Actual Claims__num", "cases/claims", "calculated_with_caution", "Raw_MedicalClaims_DRG", "sum # Actual Claims__num for core CIED DRGs", "drg_category in Core CIED Implant, Core CIED Implant / Lifecycle", "DRG-based volume measure.", "drg")
    return _sum_rows(base, inp, "", "Medicare Total # of Claims__num", "cases/claims", "calculated_with_caution", "Raw_Inpatient_DRG", "sum Medicare Total # of Claims__num for core CIED DRGs", "drg_category in Core CIED Implant, Core CIED Implant / Lifecycle", "Fallback inpatient DRG-based volume measure.", "drg")


def _market_share(base, drg_matches):
    categories = ["Core CIED Implant", "Core CIED Implant / Lifecycle", "Broader CV Procedure"]
    df = drg_matches[(drg_matches.get("source_tab") == "Raw_Inpatient_MarketShare") & (drg_matches.get("taxonomy_match_status") == "matched") & (drg_matches.get("drg_category").isin(categories))]
    claim_num = "Total claims - this hospital__num"
    claim_den = "Total claims - patient universe__num"
    charge_num = "Total charges - this hospital__num"
    charge_den = "Total charges - patient universe__num"
    if not df.empty and claim_num in df.columns and claim_den in df.columns:
        numerator = pd.to_numeric(df[claim_num], errors="coerce").fillna(0).sum()
        denominator = pd.to_numeric(df[claim_den], errors="coerce").fillna(0).sum()
        if denominator > 0:
            value = float(numerator / denominator * 100)
            base.update({"calculation_status": "calculated_with_caution", "calculated_value": value, "unit": "percent", "source_tab": "Raw_Inpatient_MarketShare", "source_row_count": len(df), "matched_row_count": len(df), "calculation_method": "sum(Total claims - this hospital__num) / sum(Total claims - patient universe__num) * 100", "source_value_field": claim_num, "source_count_field": claim_den, "taxonomy_filter": "matched configured DRG market-share categories", "validation_notes": "EP Market Share calculated from confirmed claims numerator/denominator aggregation."})
            return base, {"drg": df}
    if not df.empty and charge_num in df.columns and charge_den in df.columns:
        numerator = pd.to_numeric(df[charge_num], errors="coerce").fillna(0).sum()
        denominator = pd.to_numeric(df[charge_den], errors="coerce").fillna(0).sum()
        if denominator > 0:
            value = float(numerator / denominator * 100)
            base.update({"calculation_status": "calculated_with_caution", "calculated_value": value, "unit": "percent", "source_tab": "Raw_Inpatient_MarketShare", "source_row_count": len(df), "matched_row_count": len(df), "calculation_method": "sum(Total charges - this hospital__num) / sum(Total charges - patient universe__num) * 100", "source_value_field": charge_num, "source_count_field": charge_den, "taxonomy_filter": "matched configured DRG market-share categories", "validation_notes": "EP Market Share calculated from confirmed charges numerator/denominator aggregation."})
            return base, {"drg": df}
    base.update({"calculation_status": "not_calculated", "unit": "percent", "source_tab": "Raw_Inpatient_MarketShare", "validation_notes": "EP Market Share requires confirmed numerator/denominator aggregation; not calculated from percentage fields alone."})
    return base, {}


def _sum_rows(base, df, value_field, count_field, unit, status, source_tab, method, tax_filter, notes, detail_type):
    field = value_field or count_field
    if df.empty or field not in df.columns:
        base.update({"calculation_status": "not_calculated", "unit": unit, "source_tab": source_tab, "source_value_field": value_field, "source_count_field": count_field, "taxonomy_filter": tax_filter, "validation_notes": f"Required field {field} missing or no matched rows."})
        return base, {}
    value = float(pd.to_numeric(df[field], errors="coerce").fillna(0).sum())
    base.update({"calculation_status": status, "calculated_value": value, "unit": unit, "source_tab": source_tab, "source_file": _sources(df), "source_row_count": len(df), "matched_row_count": len(df), "calculation_method": method, "source_value_field": value_field, "source_count_field": count_field, "taxonomy_filter": tax_filter, "validation_notes": notes})
    return base, {detail_type: df}


def _referral_detail(raw_tabs):
    from_df = raw_tabs.get("Raw_Referrals_From", pd.DataFrame())
    to_df = raw_tabs.get("Raw_Referrals_To", pd.DataFrame())
    outgoing = float(pd.to_numeric(from_df.get("# of referrals__num", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    incoming = float(pd.to_numeric(to_df.get("# of referrals__num", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    return pd.DataFrame([
        {"component": "outgoing_referrals", "source_tab": "Raw_Referrals_From", "referrals": outgoing, "source_row_count": len(from_df), "source_files": _sources(from_df)},
        {"component": "incoming_referrals", "source_tab": "Raw_Referrals_To", "referrals": incoming, "source_row_count": len(to_df), "source_files": _sources(to_df)},
        {"component": "net_balance", "source_tab": "Raw_Referrals_From; Raw_Referrals_To", "referrals": outgoing - incoming, "source_row_count": len(from_df) + len(to_df), "source_files": "; ".join(filter(None, [_sources(from_df), _sources(to_df)]))},
    ])


def _geographic_detail(raw_tabs):
    df = raw_tabs.get("Raw_ZIP_Origination", pd.DataFrame()).copy()
    if df.empty or "Medicare Total # of Cases__num" not in df.columns:
        return pd.DataFrame(columns=["ZIP Code", "City", "State", "Medicare Total # of Cases__num", "Medicare Total Charges__num", "rank"])
    detail = df.sort_values("Medicare Total # of Cases__num", ascending=False).head(25).copy()
    detail["rank"] = range(1, len(detail) + 1)
    cols = [c for c in ["Zip Code", "ZIP Code", "City", "State", "Medicare Total # of Cases__num", "Medicare Total Charges__num", "rank"] if c in detail.columns]
    return detail[cols]


def _cpt_detail(df):
    cols = [c for c in ["source_file", "source_row_number", "HCPCS/CPT Code", "cpt_code_normalized", "HCPCS/CPT Description", "ep_category", "kpi_domain", "Actual Charges__num", "# Actual Procedures__num"] if c in df.columns]
    return df[cols].drop_duplicates() if cols else pd.DataFrame()


def _drg_detail(df):
    base = ["source_tab", "source_file", "source_row_number", "DRG Code", "DRG", "Base DRG Group", "drg_code_normalized", "drg_category", "kpi_domain", "recommended_use"]
    nums = [c for c in df.columns if c.endswith("__num")]
    cols = [c for c in [*base, *nums] if c in df.columns]
    return df[cols].drop_duplicates() if cols else pd.DataFrame()


def _sources(df):
    if df.empty or "source_file" not in df.columns:
        return ""
    return "; ".join(sorted(set(df["source_file"].dropna().astype(str))))
