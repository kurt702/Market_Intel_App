import pandas as pd


def find_column(df, keywords):
    """
    Finds the first column containing any keyword, honoring keyword order.

    Destination-specific keywords intentionally outrank generic fields like
    "hospital" or "facility" even if the generic column appears earlier in
    the CSV. This prevents source/account hospital columns from being treated
    as leakage destinations.
    """
    for keyword in keywords:
        for col in df.columns:
            col_lower = str(col).lower()

            if keyword in col_lower:
                return col

    return None


def clean_currency_series(series):
    """
    Converts currency / numeric text columns into numeric values.
    Handles $, commas, blanks, and bad values.
    """
    return (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace(["", "nan", "None", "NaN"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def classify_concentration(top_share):
    """
    Classifies leakage concentration based on top destination share.
    """
    if top_share >= 40:
        return "Highly Concentrated"
    elif top_share >= 25:
        return "Moderately Concentrated"
    elif top_share >= 10:
        return "Distributed"
    else:
        return "Highly Distributed"


def analyze_leakage(df, top_n=10):
    """
    Deterministic leakage analytics engine.

    Python owns truth:
    - totals
    - rankings
    - shares
    - concentration
    - top destinations

    Returns a dictionary for Streamlit UI and PNG renderers.
    """

    if df is None or df.empty:
        return {
            "success": False,
            "error": "No data provided."
        }

    destination_col = find_column(
        df,
        [
            "destination",
            "receiving",
            "competitor",
            "external facility",
            "leakage facility",
            "hospital",
            "facility",
            "account",
            "site",
        ],
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
        ],
    )

    volume_col = find_column(
        df,
        [
            "volume",
            "cases",
            "count",
            "patients",
            "# of procedures",
            "procedures",
            "procedure count",
        ],
    )

    if destination_col is None:
        return {
            "success": False,
            "error": "Could not detect leakage destination / hospital column.",
            "columns": list(df.columns),
        }

    working_df = df.copy()

    if charges_col:
        working_df["_leakage_value"] = clean_currency_series(working_df[charges_col])
        value_label = "Charges"
    elif volume_col:
        working_df["_leakage_value"] = clean_currency_series(working_df[volume_col])
        value_label = "Volume"
    else:
        return {
            "success": False,
            "error": "Could not detect charges or volume column.",
            "columns": list(df.columns),
        }

    working_df[destination_col] = (
        working_df[destination_col]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "None", "NaN"], "Unknown")
    )

    grouped = (
        working_df.groupby(destination_col, dropna=False)["_leakage_value"]
        .sum()
        .reset_index()
        .rename(
            columns={
                destination_col: "Destination",
                "_leakage_value": "Leakage Value",
            }
        )
        .sort_values("Leakage Value", ascending=False)
    )

    total_leakage = grouped["Leakage Value"].sum()

    if total_leakage == 0:
        grouped["Share"] = 0
    else:
        grouped["Share"] = grouped["Leakage Value"] / total_leakage * 100

    top_destinations_df = grouped.head(top_n).copy()

    if not top_destinations_df.empty:
        top_destination = top_destinations_df.iloc[0]["Destination"]
        top_destination_value = top_destinations_df.iloc[0]["Leakage Value"]
        top_share = top_destinations_df.iloc[0]["Share"]
    else:
        top_destination = "N/A"
        top_destination_value = 0
        top_share = 0

    top_5_share = grouped.head(5)["Leakage Value"].sum() / total_leakage * 100 if total_leakage else 0

    concentration = classify_concentration(top_share)

    return {
        "success": True,
        "dataset_type": "Leakage Analysis",
        "destination_column": destination_col,
        "charges_column": charges_col,
        "volume_column": volume_col,
        "value_label": value_label,
        "total_leakage": total_leakage,
        "top_destination": top_destination,
        "top_destination_value": top_destination_value,
        "top_share": top_share,
        "top_5_share": top_5_share,
        "concentration": concentration,
        "top_destinations_df": top_destinations_df,
        "full_grouped_df": grouped,
    }


def format_money(value):
    """
    Formats large dollar values for executive display.
    """
    try:
        value = float(value)
    except Exception:
        return "$0"

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:,.0f}"


def format_number(value):
    """
    Formats numeric values for executive display.
    """
    try:
        value = float(value)
    except Exception:
        return "0"

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
