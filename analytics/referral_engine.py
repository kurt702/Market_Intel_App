import pandas as pd


def find_column(df, keywords):
    """
    Finds first matching column based on keyword search.
    """

    for col in df.columns:
        col_lower = str(col).lower()

        for keyword in keywords:
            if keyword in col_lower:
                return col

    return None


def clean_numeric_series(series):
    """
    Cleans numeric / currency text fields.
    """

    return (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace(["", "nan", "None", "NaN"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def classify_referral_concentration(top_share):
    """
    Classifies referral concentration level.
    """

    if top_share >= 40:
        return "Highly Concentrated"

    elif top_share >= 20:
        return "Moderately Concentrated"

    else:
        return "Distributed"


def classify_pathway_type(origin, destination):
    """
    Determines internal vs external pathway.
    """

    if str(origin).strip().lower() == str(destination).strip().lower():
        return "Internal"

    return "External"


def analyze_referrals(df, top_n=20):
    """
    Deterministic referral pathway analytics engine.

    Python owns truth:
    - source detection
    - destination detection
    - referral aggregation
    - directional flow
    - concentration scoring
    - pathway classification
    """

    if df is None or df.empty:
        return {
            "success": False,
            "error": "No data provided."
        }

    origin_col = find_column(
        df,
        [
            "origin",
            "from hospital",
            "from facility",
            "source",
            "referring",
            "referral source",
            "sending",
        ]
    )

    destination_col = find_column(
        df,
        [
            "destination",
            "to hospital",
            "to facility",
            "receiving",
            "competitor",
            "target",
            "referral destination",
            "hospital name",
            "hospital name",
            "network name",
            "idn name",
            "hospital",
            "facility",
            "account",
        ]
    )

    volume_col = find_column(
        df,
        [
            "volume",
            "cases",
            "count",
            "patients",
            "patient count",
            "referrals",
            "encounters",
            "discharges",
            "# of referrals",
            "referrals",
            "unique beneficiaries",
            "claims",
            "total claims",
        ]
    )

    charges_col = find_column(
        df,
        [
            "charge",
            "charges",
            "revenue",
            "payment",
            "cost",
            "dollars",
            "amount",
        ]
    )

    if origin_col is None:
        origin_col = "_synthetic_origin"
        working_df = df.copy()
        working_df[origin_col] = "Selected Market / Account"
    else:
        working_df = df.copy()

    print("\nREFERRAL COLUMNS:")
    for c in df.columns:
        print(c)

    if destination_col is None:
        return {
            "success": False,
            "error": "Could not detect referral destination column.",
            "columns": list(df.columns),
        }

    working_df["_origin"] = (
        working_df[origin_col]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "None"], "Unknown")
    )

    working_df["_destination"] = (
        working_df[destination_col]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "None"], "Unknown")
    )

    if volume_col:
        working_df["_value"] = clean_numeric_series(
            working_df[volume_col]
        )

        value_label = "Volume"
        value_column = volume_col

    elif charges_col:
        working_df["_value"] = clean_numeric_series(
            working_df[charges_col]
        )

        value_label = "Charges"
        value_column = charges_col

    else:
        working_df["_value"] = 1

        value_label = "Referrals"
        value_column = None

    grouped = (
        working_df.groupby(
            ["_origin", "_destination"],
            dropna=False
        )["_value"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "_origin": "Origin",
                "_destination": "Destination",
                "_value": "Value",
            }
        )
        .sort_values("Value", ascending=False)
    )

    grouped["Pathway Type"] = grouped.apply(
        lambda row: classify_pathway_type(
            row["Origin"],
            row["Destination"]
        ),
        axis=1
    )

    grouped = grouped[grouped["Value"] > 0]

    total_value = grouped["Value"].sum()

    if total_value == 0:
        grouped["Share"] = 0

    else:
        grouped["Share"] = (
            grouped["Value"]
            / total_value
            * 100
        )

    top_referrals_df = grouped.head(top_n).copy()

    if not top_referrals_df.empty:
        top_origin = top_referrals_df.iloc[0]["Origin"]

        top_destination = top_referrals_df.iloc[0]["Destination"]

        top_value = top_referrals_df.iloc[0]["Value"]

        top_share = top_referrals_df.iloc[0]["Share"]

    else:
        top_origin = "N/A"
        top_destination = "N/A"
        top_value = 0
        top_share = 0

    top_5_share = (
        grouped.head(5)["Value"].sum()
        / total_value
        * 100
        if total_value
        else 0
    )

    concentration = classify_referral_concentration(
        top_share
    )

    internal_share = (
        grouped[grouped["Pathway Type"] == "Internal"]["Value"].sum()
        / total_value
        * 100
        if total_value
        else 0
    )

    external_share = (
        grouped[grouped["Pathway Type"] == "External"]["Value"].sum()
        / total_value
        * 100
        if total_value
        else 0
    )

    return {
        "success": True,
        "dataset_type": "Referral Analysis",
        "origin_column": origin_col,
        "destination_column": destination_col,
        "value_column": value_column,
        "value_label": value_label,
        "total_value": total_value,
        "top_origin": top_origin,
        "top_destination": top_destination,
        "top_value": top_value,
        "top_share": top_share,
        "top_5_share": top_5_share,
        "concentration": concentration,
        "internal_share": internal_share,
        "external_share": external_share,
        "top_referrals_df": top_referrals_df,
        "full_grouped_df": grouped,
    }


def format_referral_value(value, value_label="Volume"):
    """
    Formats referral metric values.
    """

    try:
        value = float(value)

    except Exception:
        return "0"

    if value_label == "Charges":

        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"

        elif value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"

        elif value >= 1_000:
            return f"${value / 1_000:.1f}K"

        else:
            return f"${value:,.0f}"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"

    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"

    else:
        return f"{value:,.0f}"


def format_percent(value):
    """
    Formats percentage values.
    """

    try:
        value = float(value)

    except Exception:
        return "0.0%"

    return f"{value:.1f}%"
