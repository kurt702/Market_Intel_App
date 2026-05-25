from pathlib import Path

import streamlit as st

from analytics.leakage_engine import (
    analyze_leakage,
    format_money,
    format_number,
    format_percent,
)

from renderers.leakage_renderer import generate_leakage_infographic
from utils.formatting import shorten_name
from utils.charts import render_horizontal_bar


APP_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = APP_ROOT / "outputs" / "png"


def render_leakage(df):
    st.subheader("Leakage Analysis")

    results = analyze_leakage(df)

    if not results["success"]:
        st.warning(results["error"])

        with st.expander("Available columns"):
            st.write(results.get("columns", list(df.columns)))
        return

    leakage_df = results["top_destinations_df"].copy()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Top Leakage Destination",
            shorten_name(results["top_destination"])
        )

    with col2:
        if results["value_label"] == "Charges":
            st.metric(
                "Total Leakage",
                format_money(results["total_leakage"])
            )
        else:
            st.metric(
                "Total Leakage Volume",
                format_number(results["total_leakage"])
            )

    with col3:
        st.metric(
            "Top Destination Share",
            format_percent(results["top_share"])
        )

    with col4:
        st.metric(
            "Leakage Concentration",
            results["concentration"]
        )

    leakage_df["Destination"] = leakage_df["Destination"].apply(shorten_name)

    display_df = leakage_df.copy()

    if results["value_label"] == "Charges":
        display_df["Formatted Value"] = display_df["Leakage Value"].apply(format_money)
    else:
        display_df["Formatted Value"] = display_df["Leakage Value"].apply(format_number)

    display_df["Share"] = display_df["Share"].apply(format_percent)

    st.dataframe(
        display_df[["Destination", "Formatted Value", "Share"]],
        use_container_width=True
    )

    render_horizontal_bar(
        leakage_df,
        "Leakage Value",
        "Destination",
        "Top Leakage Destinations"
    )

    st.subheader("Preliminary Strategic Interpretation")

    if results["concentration"] == "Highly Concentrated":
        st.info(
            "Leakage appears highly concentrated, suggesting a focused competitor strategy may be more effective than broad market outreach."
        )
    elif results["concentration"] == "Moderately Concentrated":
        st.info(
            "Leakage appears moderately concentrated, suggesting both top-account targeting and broader pathway optimization may be relevant."
        )
    else:
        st.info(
            "Leakage appears distributed, suggesting the opportunity may be driven by fragmented access, referral pathways, or geography rather than a single dominant competitor."
        )

    st.divider()

    st.subheader("Executive Infographic Export")

    if st.button("Generate Executive Leakage Infographic"):
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUTS_DIR / "executive_leakage_infographic.png"

        generate_leakage_infographic(
            results=results,
            output_path=output_path
        )

        st.success("Executive leakage infographic generated successfully.")

        st.image(
            output_path,
            use_container_width=True
        )
