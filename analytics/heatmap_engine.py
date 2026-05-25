import pandas as pd


def find_column(df, keywords):
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in keywords:
            if keyword in col_lower:
                return col
    return None


def clean_numeric_series(series):
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
    return (
        series.astype(str)
        .str.strip()
        .str.replace(".0", "", regex=False)
        .str.split("-")
        .str[0]
        .str.extract(r"(\d{5})")[0]
        .fillna("Unknown")
    )


def classify_intensity(share):
    if share >= 7.5:
        return "Very High"
    if share >= 5:
        return "High"
    if share >= 2.5:
        return "Moderate"
    return "Low"


def classify_concentration(top_share):
    if top_share >= 20:
        return "Highly Concentrated"
    if top_share >= 10:
        return "Moderately Concentrated"
    return "Distributed"


def analyze_heatmap_geography(df, top_n=25):
    """
    Heat-map-ready geography engine.

    Produces ZIP-level aggregation, share, cumulative share,
    intensity tiering, and a map-ready dataframe.
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
            "# of referrals",
            "referrals",
            "unique beneficiaries",
            "claims",
            "total claims",
        ],
    )

    charges_col = find_column(
        df,
        [
            "charge",
            "charges",
            "revenue",
            "payment",
            "payments",
            "pmts",
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
        .rename(columns={"_zip": "ZIP", "_value": "Value"})
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

    grouped["Intensity"] = grouped["Share"].apply(classify_intensity)

    grouped["Map Label"] = grouped.apply(
        lambda row: (
            f"ZIP {row['ZIP']} | "
            f"{row['Value']:,.0f} {value_label.lower()} | "
            f"{row['Share']:.1f}% share"
        ),
        axis=1
    )

    top_zips_df = grouped.head(top_n).copy()
    map_df = grouped.copy()

    if not grouped.empty:
        top_zip = grouped.iloc[0]["ZIP"]
        top_zip_value = grouped.iloc[0]["Value"]
        top_share = grouped.iloc[0]["Share"]
    else:
        top_zip = "N/A"
        top_zip_value = 0
        top_share = 0

    top_5_share = (
        grouped.head(5)["Value"].sum() / total_value * 100
        if total_value
        else 0
    )

    concentration = classify_concentration(top_share)

    intensity_distribution = (
        grouped.groupby("Intensity")["Value"]
        .sum()
        .reset_index()
        .sort_values("Value", ascending=False)
    )

    if total_value:
        intensity_distribution["Share"] = (
            intensity_distribution["Value"] / total_value * 100
        )
    else:
        intensity_distribution["Share"] = 0

    return {
        "success": True,
        "dataset_type": "Heat Map Geography",
        "zip_column": zip_col,
        "value_column": value_column,
        "value_label": value_label,
        "total_value": total_value,
        "top_zip": top_zip,
        "top_zip_value": top_zip_value,
        "top_share": top_share,
        "top_5_share": top_5_share,
        "concentration": concentration,
        "top_zips_df": top_zips_df,
        "map_df": map_df,
        "full_grouped_df": grouped,
        "intensity_distribution": intensity_distribution,
    }


def format_heatmap_value(value, value_label="Volume"):
    try:
        value = float(value)
    except Exception:
        return "0"

    if value_label == "Charges":
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"${value / 1_000:.1f}K"
        return f"${value:,.0f}"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def format_percent(value):
    try:
        value = float(value)
    except Exception:
        return "0.0%"

    return f"{value:.1f}%"