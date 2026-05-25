def _normalized_columns(df):
    return [
        str(column).strip().lower()
        for column in df.columns
    ]


def _matched_keywords(columns, keywords):
    matches = []

    for column in columns:
        for keyword in keywords:
            keyword_lower = keyword.lower()

            if keyword_lower in column:
                matches.append(column)
                break

    return matches


def _reason(label, matches):
    if not matches:
        return f"No {label} fields detected"

    return f"{label}: " + ", ".join(matches)


def detect_dataset_profile(df):
    """
    Detects the strategic role of a dataframe for multi-dataset intelligence.

    Referral-specific fields are evaluated before generic hospital / charge
    fields so referral extracts do not get swallowed by leakage routing.
    """

    columns = _normalized_columns(df)

    zip_matches = _matched_keywords(
        columns,
        [
            "zip",
            "zipcode",
            "zip code",
            "postal",
            "patient zip",
            "origin zip",
            "residence zip",
        ],
    )

    referral_matches = _matched_keywords(
        columns,
        [
            "# of referrals",
            "% of referrals",
            "in-network referrals",
            "out-of-network referrals",
            "in-network",
            "out-of-network",
            "referral",
            "referrals",
            "unique beneficiaries",
            "network name",
            "idn name",
        ],
    )

    referral_support_matches = _matched_keywords(
        columns,
        [
            "hospital name",
            "definitive id",
            "medicare pmts",
            "medicare payments",
            "medicare charges",
        ],
    )

    leakage_matches = _matched_keywords(
        columns,
        [
            "leakage",
            "outmigration",
            "external facility",
            "leakage facility",
            "receiving",
            "competitor",
            "destination",
        ],
    )

    leakage_support_matches = _matched_keywords(
        columns,
        [
            "hospital",
            "facility",
            "account",
            "charges",
            "charge",
            "pmts",
            "payment",
            "revenue",
        ],
    )

    has_zip = bool(zip_matches)
    has_referral = bool(referral_matches)
    has_leakage = bool(leakage_matches or leakage_support_matches)

    if has_zip and leakage_matches and not has_referral:
        role = "ZIP + Leakage"
        reason = (
            f"{_reason('ZIP fields', zip_matches)} | "
            f"{_reason('Leakage fields', leakage_matches)}"
        )

    elif has_zip and has_referral:
        role = "ZIP + Referral"
        reason = (
            f"{_reason('ZIP fields', zip_matches)} | "
            f"{_reason('Referral fields', referral_matches)}"
        )

    elif has_referral:
        role = "Referral"
        support_reason = ""

        if referral_support_matches:
            support_reason = (
                " | Support fields: "
                + ", ".join(referral_support_matches)
            )

        reason = _reason("Referral fields", referral_matches) + support_reason

    elif has_zip and not has_leakage:
        role = "ZIP Geography"
        reason = _reason("ZIP fields", zip_matches)

    elif has_zip and has_leakage:
        role = "ZIP + Leakage"
        reason = (
            f"{_reason('ZIP fields', zip_matches)} | "
            f"{_reason('Leakage support fields', leakage_matches or leakage_support_matches)}"
        )

    elif has_leakage:
        role = "Leakage"
        reason = _reason(
            "Leakage fields",
            leakage_matches or leakage_support_matches,
        )

    else:
        role = "Unknown"
        reason = "No ZIP, referral, or leakage routing fields detected"

    return {
        "role": role,
        "reason": reason,
        "scores": {
            "zip": len(zip_matches),
            "referral": len(referral_matches) * 10 + len(referral_support_matches),
            "leakage": len(leakage_matches) * 10 + len(leakage_support_matches),
        },
    }


def detect_dataset_role(df):
    """
    Backward-compatible role-only helper.
    """

    return detect_dataset_profile(df)["role"]


def _is_better_profile(candidate, current, score_key):
    if current is None:
        return True

    return candidate["scores"].get(score_key, 0) > current["scores"].get(score_key, 0)


def route_uploaded_datasets(dataframes):
    """
    Routes uploaded dataframes into likely analytic roles.

    Output includes a debug profile table:
        file, role, reason, rows, columns
    """

    routed = {
        "zip_file": None,
        "zip_df": None,
        "leakage_file": None,
        "leakage_df": None,
        "referral_file": None,
        "referral_df": None,
        "profiles": [],
    }

    best_zip = None
    best_leakage = None
    best_referral = None

    for file_name, df in dataframes.items():

        profile = detect_dataset_profile(df)
        role = profile["role"]

        routed["profiles"].append(
            {
                "file": file_name,
                "role": role,
                "reason": profile["reason"],
                "rows": len(df),
                "columns": len(df.columns),
            }
        )

        candidate = {
            "file_name": file_name,
            "df": df,
            "scores": profile["scores"],
        }

        if role in ["ZIP Geography", "ZIP + Leakage", "ZIP + Referral"]:
            if _is_better_profile(candidate, best_zip, "zip"):
                best_zip = candidate

        if role in ["Leakage", "ZIP + Leakage"]:
            if _is_better_profile(candidate, best_leakage, "leakage"):
                best_leakage = candidate

        if role in ["Referral", "ZIP + Referral"]:
            if _is_better_profile(candidate, best_referral, "referral"):
                best_referral = candidate

    if best_zip is not None:
        routed["zip_file"] = best_zip["file_name"]
        routed["zip_df"] = best_zip["df"]

    if best_leakage is not None:
        routed["leakage_file"] = best_leakage["file_name"]
        routed["leakage_df"] = best_leakage["df"]

    if best_referral is not None:
        routed["referral_file"] = best_referral["file_name"]
        routed["referral_df"] = best_referral["df"]

    return routed
