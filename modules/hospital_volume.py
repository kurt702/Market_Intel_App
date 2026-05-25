import streamlit as st

from utils.formatting import (
    clean_numeric_column,
    shorten_name,
    classify_concentration
)

from utils.charts import render_horizontal_bar


def render_hospital_volume(df, possible_fields):
    st.subheader("Hospital Procedure Volume Analysis")

    if not possible_fields["Hospital"] or not possible_fields["Volume"]:
        st.warning(
            "Hospital Volume analysis requires a hospital/facility field and a numeric volume/count/cases field."
        )
        return

    hospital_col = possible_fields["Hospital"][0]
    volume_col = possible_fields["Volume"][0]

    df = clean_numeric_column(df, volume_col)

    top_hospitals = (
        df.groupby(hospital_col)[volume_col]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    top_hospitals = top_hospitals[
        top_hospitals[volume_col] > 0
    ]

    top_hospitals[hospital_col] = (
        top_hospitals[hospital_col]
        .apply(shorten_name)
    )

    if top_hospitals.empty:
        st.warning("No positive hospital volume values found.")
        return

    total_volume = top_hospitals[volume_col].sum()

    top_share = (
        top_hospitals[volume_col].iloc[0]
        / total_volume
    ) * 100

    concentration_level = classify_concentration(top_share)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Top Hospital", top_hospitals[hospital_col].iloc[0])

    with col2:
        st.metric("Top Hospital Volume", int(top_hospitals[volume_col].iloc[0]))

    with col3:
        st.metric("Top Hospital Share", f"{top_share:.1f}%")

    with col4:
        st.metric("Market Concentration", concentration_level)

    st.dataframe(top_hospitals, use_container_width=True)

    render_horizontal_bar(
        top_hospitals,
        volume_col,
        hospital_col,
        "Top Hospitals by Procedure Volume"
    )