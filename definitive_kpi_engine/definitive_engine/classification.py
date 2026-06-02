"""CSV file classification by column signature.

Phase 2 intentionally limits classification to header-level evidence. File
names may help with year detection, but file type detection is based on the
columns present in each CSV.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


YEAR_PATTERN = re.compile(r"(?<!\d)(20\d{2})(?!\d)")

@dataclass(frozen=True)
class ClassificationResult:
    detected_file_type: str
    classification_notes: str


@dataclass(frozen=True)
class ColumnSignature:
    detected_file_type: str
    required_columns: tuple[str, ...]
    filename_hints: tuple[str, ...] = ()


RUSH_COLUMN_SIGNATURES: tuple[ColumnSignature, ...] = (
    ColumnSignature(
        "inpatient_leakage",
        ("hospital_name", "base_drg_group", "total_pmts", "total_charges", "total_claims", "unique_patients", "network", "network_parent"),
        ("leakage", "inpatient"),
    ),
    ColumnSignature(
        "inpatient_marketshare",
        (
            "drg_code",
            "description",
            "total_pmts_this_hospital",
            "total_pmts_patient_universe",
            "pmts_at_this_hospital",
            "total_charges_this_hospital",
            "total_charges_patient_universe",
            "charges_at_this_hospital",
            "total_claims_this_hospital",
            "total_claims_patient_universe",
            "claims_at_this_hospital",
        ),
        ("market", "share"),
    ),
    ColumnSignature(
        "zip_origination",
        ("zip_code", "city", "state", "medicare_total_charges", "medicare_avg_charge_case", "medicare_total_of_cases", "medicare_total_days_of_care"),
        ("zip", "origination"),
    ),
    ColumnSignature(
        "outpatient_hospital_leakage",
        ("hospital_name", "hcpcs_category", "total_pmts", "total_charges", "total_claims", "unique_patients", "network", "network_parent", "definitive_id"),
        ("outpatient", "leakage"),
    ),
    ColumnSignature(
        "referrals_from",
        ("definitive_id", "hospital_name", "city", "state", "medicare_pmts", "medicare_charges", "of_referrals", "of_unique_beneficiaries", "network_name", "in_network_referrals"),
        ("referrals", "from"),
    ),
    ColumnSignature(
        "referrals_to",
        ("definitive_id", "hospital_name", "city", "state", "medicare_pmts", "medicare_charges", "of_referrals", "of_unique_beneficiaries", "idn_name", "in_network_referrals"),
        ("referrals", "to"),
    ),
    ColumnSignature(
        "inpatient_drg_breakdown",
        (
            "drg",
            "drg_description",
            "attending_physician_npi",
            "first_name",
            "last_name",
            "primary_specialty",
            "primary_hospital_affiliation",
            "medicare_total_pmts",
            "medicare_avg_pmt_claim",
            "medicare_total_charges",
            "medicare_charge_claim",
            "medicare_total_of_claims",
        ),
        ("inpatient", "drg"),
    ),
    ColumnSignature(
        "medicalclaims_cpt_breakdown",
        (
            "rendering_provider",
            "definitive_id",
            "rendering_provider_type",
            "hcpcs_cpt_code",
            "hcpcs_cpt_description",
            "actual_procedures",
            "actual_charges",
            "charge_procedure_actual",
        ),
        ("medicalclaims", "cpt"),
    ),
    ColumnSignature(
        "outpatient_procedure_breakdown",
        ("outpatient", "procedure", "hcpcs_cpt_code", "actual_procedures"),
        ("outpatient", "procedure"),
    ),
    ColumnSignature(
        "medicalclaims_drg_breakdown",
        (
            "drg_code",
            "drg_description",
            "definitive_id",
            "facility_name",
            "firm_type",
            "actual_claims",
            "actual_unique_patients",
            "actual_charges",
            "charge_claim_actual",
        ),
        ("medicalclaims", "drg"),
    ),
)


def normalize_column_name(column_name: object) -> str:
    """Normalize a source column name for signature matching."""
    return re.sub(r"[^a-z0-9]+", "_", str(column_name).strip().lower()).strip("_")


def detect_year_from_filename(file_name: str) -> str:
    """Return the first 20xx year found in a file name, or an empty string."""
    match = YEAR_PATTERN.search(file_name)
    return match.group(1) if match else ""


def classify_file(columns: list[str], file_name: str = "") -> ClassificationResult:
    """Classify a CSV from its column signature."""
    normalized_columns = {normalize_column_name(column) for column in columns}
    matches = [
        signature
        for signature in RUSH_COLUMN_SIGNATURES
        if set(signature.required_columns).issubset(normalized_columns)
    ]

    if not matches:
        return ClassificationResult(
            detected_file_type="unknown",
            classification_notes="No configured column signature matched.",
        )

    selected = _break_tie(matches, file_name)
    required_columns = ", ".join(selected.required_columns)
    return ClassificationResult(
        detected_file_type=selected.detected_file_type,
        classification_notes=f"Matched required columns: {required_columns}.",
    )


def _break_tie(matches: list[ColumnSignature], file_name: str) -> ColumnSignature:
    if len(matches) == 1:
        return matches[0]

    normalized_file_name = normalize_column_name(file_name)
    hinted_matches = [
        match
        for match in matches
        if match.filename_hints and all(hint in normalized_file_name for hint in match.filename_hints)
    ]
    if hinted_matches:
        return hinted_matches[0]
    return matches[0]
