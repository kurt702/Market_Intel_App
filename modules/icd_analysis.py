import streamlit as st

from utils.formatting import clean_numeric_column, classify_concentration
from utils.charts import render_horizontal_bar


def render_icd_analysis(df, possible_fields):
    st.subheader("ICD Procedure Volume Analysis")

    if not possible_fields["ICD"] or not possible_fields["Volume"]:
        st.warning(
            "ICD Analysis requires an ICD field and a numeric volume/count/cases field."
        )
        return

    icd_col = possible_fields["ICD"][0]
    volume_col = possible_fields["Volume"][0]

    df = clean_numeric_column(df, volume_col)

    top_codes = (
        df.groupby(icd_col)[volume_col]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    top_codes = top_codes[
        top_codes[volume_col] > 0
    ]

    if top_codes.empty:
        st.warning("No positive ICD volume values found.")
        return

    total_volume = top_codes[volume_col].sum()

    top_share = (
        top_codes[volume_col].iloc[0]
        / total_volume
    ) * 100

    concentration_level = classify_concentration(top_share)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Top ICD Code", top_codes[icd_col].iloc[0])

    with col2:
        st.metric("Top ICD Volume", int(top_codes[volume_col].iloc[0]))

    with col3:
        st.metric("Top ICD Share", f"{top_share:.1f}%")

    with col4:
        st.metric("Concentration", concentration_level)

    st.dataframe(top_codes, use_container_width=True)

    render_horizontal_bar(
        top_codes,
        volume_col,
        icd_col,
        "Top ICD Codes by Procedure Volume"
    )