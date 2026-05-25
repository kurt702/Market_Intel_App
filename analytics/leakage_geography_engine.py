from analytics.leakage_engine import analyze_leakage


def normalize_zip(zip_code):

    try:
        zip_code = str(zip_code).strip()

        if "." in zip_code:
            zip_code = zip_code.split(".")[0]

        if "-" in zip_code:
            zip_code = zip_code.split("-")[0]

        zip_code = zip_code.zfill(5)

        if len(zip_code) != 5:
            return None

        return zip_code

    except Exception:
        return None


def find_column(df, keywords):

    for col in df.columns:

        col_lower = str(col).lower()

        for keyword in keywords:

            if keyword in col_lower:
                return col

    return None


def analyze_leakage_geography(
    leakage_df,
    zip_df,
):
    """
    Combines:
    - leakage intelligence
    - ZIP geography
    - competitor capture

    into:
    geographic leakage overlay intelligence
    """

    if leakage_df is None or leakage_df.empty:

        return {
            "success": False,
            "error": "Leakage dataframe empty."
        }

    if zip_df is None or zip_df.empty:

        return {
            "success": False,
            "error": "ZIP dataframe empty."
        }

    zip_working = zip_df.copy()

    zip_col = find_column(
        zip_working,
        [
            "zip",
            "zipcode",
            "zip code",
            "postal",
        ]
    )

    if zip_col is None:

        return {
            "success": False,
            "error": "Could not identify ZIP column."
        }

    leakage_results = analyze_leakage(leakage_df)

    if not leakage_results["success"]:

        return {
            "success": False,
            "error": leakage_results["error"]
        }

    zip_working["ZIP"] = (
        zip_working[zip_col]
        .apply(normalize_zip)
    )

    zip_working = zip_working.dropna(
        subset=["ZIP"]
    )

    # =========================
    # ZIP INTENSITY
    # =========================

    zip_summary = (
        zip_working
        .groupby("ZIP")
        .size()
        .reset_index(name="ZIP Volume")
        .sort_values(
            "ZIP Volume",
            ascending=False
        )
    )

    total_zip_volume = (
        zip_summary["ZIP Volume"]
        .sum()
    )

    zip_summary["ZIP Share"] = (
        zip_summary["ZIP Volume"]
        / total_zip_volume
        * 100
    )

    # =========================
    # SYNTHETIC OVERLAY
    #
    # Destination and value selection intentionally comes from
    # analyze_leakage(), the same deterministic engine used by the
    # leakage summary PNG. This keeps the overlay aligned with the
    # primary leakage slide and prevents generic columns such as
    # "Hospital Name" from being selected ahead of true destination /
    # receiving / competitor fields.
    # =========================

    destination_summary = leakage_results["full_grouped_df"].copy()

    top_destination = leakage_results["top_destination"]

    top_leakage_value = leakage_results["top_destination_value"]

    zip_summary["Primary Leakage Destination"] = (
        top_destination
    )

    zip_summary["Estimated Leakage Value"] = (
        zip_summary["ZIP Share"]
        / 100
        * top_leakage_value
    )

    return {
        "success": True,
        "destination_column": leakage_results["destination_column"],
        "value_column": (
            leakage_results["charges_column"]
            or leakage_results["volume_column"]
        ),
        "value_label": leakage_results["value_label"],
        "top_destination": top_destination,
        "top_leakage_value": top_leakage_value,
        "overlay_df": zip_summary,
        "destination_summary": destination_summary,
    }
