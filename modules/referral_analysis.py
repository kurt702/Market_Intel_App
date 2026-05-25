from pathlib import Path

import streamlit as st

from analytics.referral_engine import (
    analyze_referrals,
    format_referral_value,
    format_percent,
)

from renderers.referral_renderer import (
    generate_referral_infographic
)

from utils.charts import render_horizontal_bar
from utils.formatting import shorten_name


APP_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = APP_ROOT / "outputs" / "png"


def render_referral_analysis(df):
    st.subheader("Referral Analysis")

    results = analyze_referrals(df)

    if not results["success"]:
        st.warning(results["error"])

        with st.expander("Available columns"):
            st.write(results.get("columns", list(df.columns)))

        with st.expander("Current dataset preview", expanded=False):
            st.dataframe(df.head(), width="stretch")

        return

    referral_df = results["top_referrals_df"].copy()

    referral_df["Pathway"] = (
        referral_df["Origin"].apply(shorten_name)
        + " → "
        + referral_df["Destination"].apply(shorten_name)
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Top Referral Pathway",
            f"{shorten_name(results['top_origin'])} → {shorten_name(results['top_destination'])}"
        )

    with col2:
        st.metric(
            f"Total {results['value_label']}",
            format_referral_value(
                results["total_value"],
                results["value_label"]
            )
        )

    with col3:
        st.metric(
            "Top Pathway Share",
            format_percent(results["top_share"])
        )

    with col4:
        st.metric(
            "Referral Concentration",
            results["concentration"]
        )

    display_df = referral_df.copy()

    display_df["Formatted Value"] = display_df["Value"].apply(
        lambda x: format_referral_value(
            x,
            results["value_label"]
        )
    )

    display_df["Share"] = display_df["Share"].apply(format_percent)

    st.dataframe(
        display_df[
            [
                "Origin",
                "Destination",
                "Formatted Value",
                "Share",
                "Pathway Type",
            ]
        ],
        width="stretch"
    )

    render_horizontal_bar(
        referral_df,
        "Value",
        "Pathway",
        "Top Referral Pathways"
    )

    st.subheader("Referral Pathway Interpretation")

    if results["concentration"] == "Highly Concentrated":
        st.info(
            "Referral pathways appear highly concentrated, suggesting a small number of dominant directional relationships may be driving network behavior."
        )
    elif results["concentration"] == "Moderately Concentrated":
        st.info(
            "Referral pathways appear moderately concentrated, suggesting a mix of dominant referral lanes and broader network movement."
        )
    else:
        st.info(
            "Referral pathways appear distributed, suggesting fragmented pathway behavior or a broad regional referral network."
        )

    st.divider()

    st.subheader("Internal vs External Pathway Mix")

    mix_col1, mix_col2, mix_col3 = st.columns(3)

    with mix_col1:
        st.metric(
            "Internal Share",
            format_percent(results["internal_share"])
        )

    with mix_col2:
        st.metric(
            "External Share",
            format_percent(results["external_share"])
        )

        with mix_col3:
            st.metric(
            "Top 5 Pathway Share",
            format_percent(results["top_5_share"])
        )

    st.divider()

    st.subheader("Executive Referral Infographic Export")

    if st.button("Generate Executive Referral Infographic"):

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUTS_DIR / "executive_referral_infographic.png"

        generate_referral_infographic(
            results=results,
            output_path=output_path
        )

        st.success(
            "Executive referral infographic generated successfully."
        )

        st.image(
            output_path,
            width="stretch"
        )
