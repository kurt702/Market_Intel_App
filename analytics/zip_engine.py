import pandas as pd


def find_column(df, keywords):
    """
    Finds the first column containing any keyword.
    Case-insensitive.
    """
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in keywords:
            if keyword in col_lower:
                return col
    return None


def clean_numeric_series(series):
    """
    Converts numeric / currency text into numeric values.
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


def clean_zip_series(series):
    """
    Standardizes ZIP codes to 5-digit strings.
    Handles ZIP+4 and numeric ZIPs.
    """
    return (
        series.astype(str)
        .str.strip()
        .str.replace(".0", "", regex=False)
        .str.split("-")
        .str[0]
        .str.extract(r"(\d{5})")[0]
        .fillna("Unknown")
    )


def classify_zip_tier(share, cumulative_share):
    """
    Classifies ZIPs into strategic geography tiers.
    """
    if cumulative_share <= 40:
        return "Core Market"
    elif cumulative_share <= 70:
        return "Secondary Market"
    elif cumulative_share <= 90:
        return "Peripheral Market"
    else:
        return "Low Presence"


def classify_geographic_concentration(top_share):
    """
    Classifies overall geographic concentration.
    """
    if top_share >= 20:
        return "Highly Concentrated"
    elif top_share >= 10:
        return "Moderately Concentrated"
    else:
        return "Distributed"


def analyze_zip_geography(df, top_n=20):
    """
    Deterministic ZIP geography analytics engine.

    Python owns truth:
    - ZIP detection
    - volume aggregation
    - share calculation
    - cumulative share
    - market tiering
    - geographic concentration

    Returns a dictionary for Streamlit UI and PNG renderers.
    """

    if df is None or df.empty:
        return {
            "success": False,
            "error": "No data provided."
        }

    zip_col = find_column(
        df,
        [
            "zip",
            "zipcode",
            "zip code",
            "postal",
            "patient zip",
            "patient zipcode",
            "origin zip",
            "residence zip",
        ],
    )

    volume_col = find_column(
        df,
        [
            "volume",
            "cases",
            "count",
            "patients",
            "patient count",
            "# of procedures",
            "procedures",
            "procedure count",
            "encounters",
            "discharges",
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

    if zip_col is None:
        return {
            "success": False,
            "error": "Could not detect ZIP / postal code column.",
            "columns": list(df.columns),
        }

    working_df = df.copy()

    working_df["_zip"] = clean_zip_series(working_df[zip_col])

    if volume_col:
        working_df["_value"] = clean_numeric_series(working_df[volume_col])
        value_label = "Volume"
        value_column = volume_col
    elif charges_col:
        working_df["_value"] = clean_numeric_series(working_df[charges_col])
        value_label = "Charges"
        value_column = charges_col
    else:
        # If no metric column is detected, count rows by ZIP.
        working_df["_value"] = 1
        value_label = "Records"
        value_column = None

    working_df = working_df[working_df["_zip"] != "Unknown"]

    if working_df.empty:
        return {
            "success": False,
            "error": "No valid 5-digit ZIP codes found after cleaning.",
            "columns": list(df.columns),
        }

    grouped = (
        working_df.groupby("_zip", dropna=False)["_value"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "_zip": "ZIP",
                "_value": "Value",
            }
        )
        .sort_values("Value", ascending=False)
    )

    grouped = grouped[grouped["Value"] > 0].copy()

    total_value = grouped["Value"].sum()

    if total_value == 0:
        grouped["Share"] = 0
        grouped["Cumulative Share"] = 0
    else:
        grouped["Share"] = grouped["Value"] / total_value * 100
        grouped["Cumulative Share"] = grouped["Share"].cumsum()

    grouped["Tier"] = grouped.apply(
        lambda row: classify_zip_tier(
            row["Share"],
            row["Cumulative Share"]
        ),
        axis=1
    )

    top_zips_df = grouped.head(top_n).copy()

    if not top_zips_df.empty:
        top_zip = top_zips_df.iloc[0]["ZIP"]
        top_zip_value = top_zips_df.iloc[0]["Value"]
        top_share = top_zips_df.iloc[0]["Share"]
    else:
        top_zip = "N/A"
        top_zip_value = 0
        top_share = 0

    top_5_share = (
        grouped.head(5)["Value"].sum() / total_value * 100
        if total_value
        else 0
    )

    concentration = classify_geographic_concentration(top_share)

    core_market_share = grouped[
        grouped["Tier"] == "Core Market"
    ]["Share"].sum()

    secondary_market_share = grouped[
        grouped["Tier"] == "Secondary Market"
    ]["Share"].sum()

    peripheral_market_share = grouped[
        grouped["Tier"] == "Peripheral Market"
    ]["Share"].sum()

    low_presence_share = grouped[
        grouped["Tier"] == "Low Presence"
    ]["Share"].sum()

    return {
        "success": True,
        "dataset_type": "ZIP Geography",
        "zip_column": zip_col,
        "value_column": value_column,
        "value_label": value_label,
        "total_value": total_value,
        "top_zip": top_zip,
        "top_zip_value": top_zip_value,
        "top_share": top_share,
        "top_5_share": top_5_share,
        "concentration": concentration,
        "core_market_share": core_market_share,
        "secondary_market_share": secondary_market_share,
        "peripheral_market_share": peripheral_market_share,
        "low_presence_share": low_presence_share,
        "top_zips_df": top_zips_df,
        "full_grouped_df": grouped,
    }


def format_zip_value(value, value_label="Volume"):
    """
    Formats ZIP geography metric values.
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