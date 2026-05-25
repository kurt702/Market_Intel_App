import pandas as pd


def shorten_name(name):
    return str(name).split("(")[0].strip()


def clean_numeric_column(df, col):
    df[col] = (
        df[col]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
    )

    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def classify_concentration(top_share):
    if top_share > 60:
        return "Highly Concentrated"
    if top_share > 35:
        return "Moderately Concentrated"
    return "Distributed"


def build_recommended_groupings(fields):
    groupings = []

    for key in [
        "Hospital", "Destination", "Origin", "Physician", "Procedure",
        "Geography", "ZIP", "DRG", "CPT", "HCPCS", "ICD"
    ]:
        groupings.extend(fields.get(key, []))

    return list(dict.fromkeys(groupings))


def build_recommended_metrics(fields):
    metrics = []

    for key in ["Charges", "Volume", "Leakage", "Referral", "Quality"]:
        metrics.extend(fields.get(key, []))

    return list(dict.fromkeys(metrics))