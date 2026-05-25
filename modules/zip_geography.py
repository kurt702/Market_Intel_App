import json

import streamlit as st

from analytics.zip_engine import (
    analyze_zip_geography,
    format_zip_value,
    format_percent as format_zip_percent,
)

from analytics.heatmap_engine import (
    analyze_heatmap_geography,
    format_heatmap_value,
    format_percent as format_heatmap_percent,
)

from renderers.zip_renderer import (
    generate_zip_infographic,
)

from renderers.heatmap_renderer import (
    generate_heatmap_infographic,
)

from renderers.choropleth_renderer import (
    render_zip_choropleth,
)

from analytics.geography_join_engine import (
    prepare_choropleth_dataframe,
    calculate_geographic_viewport,
    filter_geojson_to_active_zips,
)

from analytics.leakage_geography_engine import (
    analyze_leakage_geography,
)

from renderers.leakage_geography_renderer import (
    render_leakage_geography_overlay,
)

from utils.charts import render_horizontal_bar


def load_geojson_safely(path):
    """
    Loads GeoJSON safely.

    Prevents app crash when:
    - file does not exist
    - file exists but is empty
    - file contains invalid JSON
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_geojson = f.read().strip()

        if not raw_geojson:
            return {
                "success": False,
                "error": (
                    "ZIP boundary GeoJSON file exists but is empty. "
                    "Add real ZIP boundary data to maps/zip_boundaries.geojson."
                ),
                "data": None,
            }

        geojson_data = json.loads(raw_geojson)

        if not isinstance(geojson_data, dict):
            return {
                "success": False,
                "error": "ZIP boundary GeoJSON is not a valid GeoJSON object.",
                "data": None,
            }

        if "features" not in geojson_data:
            return {
                "success": False,
                "error": "ZIP boundary GeoJSON is missing a 'features' collection.",
                "data": None,
            }

        return {
            "success": True,
            "error": None,
            "data": geojson_data,
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": (
                "ZIP boundary GeoJSON not found. "
                "Add maps/zip_boundaries.geojson to enable choropleth mapping."
            ),
            "data": None,
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": (
                f"ZIP boundary GeoJSON is not valid JSON: {e}. "
                "Replace maps/zip_boundaries.geojson with a valid GeoJSON file."
            ),
            "data": None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected GeoJSON loading error: {e}",
            "data": None,
        }


def render_zip_geography(df):
    st.subheader("ZIP Geography Analysis")

    results = analyze_zip_geography(df)

    if not results["success"]:
        st.warning(results["error"])

        with st.expander("Available columns"):
            st.write(results.get("columns", list(df.columns)))

        return

    zip_df = results["top_zips_df"].copy()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Top ZIP", results["top_zip"])

    with col2:
        st.metric(
            f"Total {results['value_label']}",
            format_zip_value(
                results["total_value"],
                results["value_label"]
            )
        )

    with col3:
        st.metric(
            "Top ZIP Share",
            format_zip_percent(results["top_share"])
        )

    with col4:
        st.metric(
            "Geographic Concentration",
            results["concentration"]
        )

    display_df = zip_df.copy()

    display_df["Formatted Value"] = display_df["Value"].apply(
        lambda x: format_zip_value(
            x,
            results["value_label"]
        )
    )

    display_df["Share"] = display_df["Share"].apply(
        format_zip_percent
    )

    st.dataframe(
        display_df[
            [
                "ZIP",
                "Formatted Value",
                "Share",
                "Tier"
            ]
        ],
        width="stretch"
    )

    render_horizontal_bar(
        zip_df,
        "Value",
        "ZIP",
        "Top ZIP Geography Concentration"
    )

    st.subheader("Geographic Interpretation")

    if results["concentration"] == "Highly Concentrated":
        st.info(
            "Patient origin appears highly concentrated within a relatively narrow geographic footprint, "
            "suggesting strong core-market dominance."
        )

    elif results["concentration"] == "Moderately Concentrated":
        st.info(
            "Patient origin appears moderately concentrated, suggesting a blend of core-market strength "
            "and broader regional draw."
        )

    else:
        st.info(
            "Patient origin appears geographically distributed, suggesting a broad referral footprint "
            "or fragmented market capture."
        )

    st.divider()

    st.subheader("Market Tier Distribution")

    tier_col1, tier_col2, tier_col3, tier_col4 = st.columns(4)

    with tier_col1:
        st.metric(
            "Core Market",
            format_zip_percent(results["core_market_share"])
        )

    with tier_col2:
        st.metric(
            "Secondary",
            format_zip_percent(results["secondary_market_share"])
        )

    with tier_col3:
        st.metric(
            "Peripheral",
            format_zip_percent(results["peripheral_market_share"])
        )

    with tier_col4:
        st.metric(
            "Low Presence",
            format_zip_percent(results["low_presence_share"])
        )

    st.divider()

    st.subheader("Executive ZIP Infographic Export")

    if st.button("Generate Executive ZIP Infographic"):
        output_path = "outputs/png/executive_zip_infographic.png"

        generate_zip_infographic(
            results=results,
            output_path=output_path
        )

        st.success("Executive ZIP infographic generated successfully.")

        st.image(
            output_path,
            width="stretch"
        )

    # =========================
    # HEAT MAP INTELLIGENCE
    # =========================

    st.divider()

    st.subheader("Heat Map Intelligence Layer")

    heatmap_results = analyze_heatmap_geography(df)

    if not heatmap_results["success"]:
        st.warning(heatmap_results["error"])

        with st.expander("Available columns"):
            st.write(heatmap_results.get("columns", list(df.columns)))

        return

    intensity_df = heatmap_results["intensity_distribution"].copy()

    intensity_df["Formatted Value"] = intensity_df["Value"].apply(
        lambda x: format_heatmap_value(
            x,
            heatmap_results["value_label"]
        )
    )

    intensity_df["Share"] = intensity_df["Share"].apply(
        format_heatmap_percent
    )

    st.dataframe(
        intensity_df[
            [
                "Intensity",
                "Formatted Value",
                "Share"
            ]
        ],
        width="stretch"
    )

    st.subheader("Heat Map Ready Geography Preview")

    preview_df = heatmap_results["map_df"].head(25).copy()

    preview_df["Formatted Value"] = preview_df["Value"].apply(
        lambda x: format_heatmap_value(
            x,
            heatmap_results["value_label"]
        )
    )

    preview_df["Share"] = preview_df["Share"].apply(
        format_heatmap_percent
    )

    st.dataframe(
        preview_df[
            [
                "ZIP",
                "Formatted Value",
                "Share",
                "Intensity",
                "Map Label"
            ]
        ],
        width="stretch"
    )

    st.divider()

    st.subheader("Executive Heat Map Infographic Export")

    if st.button("Generate Executive Heat Map Infographic"):
        output_path = "outputs/png/executive_heatmap_infographic.png"

        generate_heatmap_infographic(
            results=heatmap_results,
            output_path=output_path
        )

        st.success("Executive heat map infographic generated successfully.")

        st.image(
            output_path,
            width="stretch"
        )

    # =========================
    # INTERACTIVE CHOROPLETH
    # =========================

    st.divider()

    st.subheader("Interactive ZIP Choropleth Map")

    geojson_result = load_geojson_safely(
        "maps/zip_boundaries.geojson"
    )

    if not geojson_result["success"]:
        st.warning(geojson_result["error"])
        return

    geojson_data = geojson_result["data"]

    choropleth_prep = prepare_choropleth_dataframe(
        heatmap_results,
        geojson_zip_features=geojson_data.get("features", [])
    )

    if not choropleth_prep["success"]:
        st.warning(choropleth_prep["error"])
        return

    viewport = calculate_geographic_viewport(
        choropleth_prep["choropleth_df"],
        geojson_data.get("features", [])
    )

    filtered_geojson = filter_geojson_to_active_zips(
        geojson_data,
        choropleth_prep["choropleth_df"]
    )

    with st.spinner("Rendering interactive ZIP choropleth map..."):

        map_result = render_zip_choropleth(
            choropleth_prep["choropleth_df"],
            geojson_data=filtered_geojson,
            title="ZIP-Level Geographic Heat Map",
            viewport=viewport
        )

    if not map_result["success"]:
        st.warning(map_result["error"])
        return

    st.plotly_chart(
        map_result["figure"],
        width="stretch"
    )

    geo_summary = choropleth_prep["geography_summary"]

    st.caption(
        f"ZIP match rate: {geo_summary['match_rate']:.1f}% "
        f"({geo_summary['matched_zips']} matched, "
        f"{geo_summary['unmatched_zips']} unmatched)"
    )

    # =========================
    # LEAKAGE GEOGRAPHY OVERLAY
    # =========================

    st.divider()

    st.subheader("Leakage Geography Overlay")

    routed_datasets = st.session_state.get(
        "routed_datasets",
        {}
    )

    routed_zip_df = routed_datasets.get("zip_df")
    routed_leakage_df = routed_datasets.get("leakage_df")

    if routed_zip_df is None or routed_leakage_df is None:

        st.info(
            "Upload both a ZIP geography file and a leakage file to generate leakage geography overlays."
        )

    else:

        leakage_geo_results = analyze_leakage_geography(
            leakage_df=routed_leakage_df,
            zip_df=routed_zip_df
        )

        if not leakage_geo_results["success"]:

            st.warning(
                leakage_geo_results["error"]
            )

        else:

            overlay_df = leakage_geo_results["overlay_df"]

            filtered_overlay_geojson = filter_geojson_to_active_zips(
                geojson_data,
                overlay_df
            )

            overlay_map_result = render_leakage_geography_overlay(
                overlay_df=overlay_df,
                geojson_data=filtered_overlay_geojson,
                title="Estimated Leakage Opportunity by Patient ZIP"
            )

            if not overlay_map_result["success"]:

                st.warning(
                    overlay_map_result["error"]
                )

            else:

                st.plotly_chart(
                    overlay_map_result["figure"],
                    width="stretch"
                )

                st.caption(
                    f"Primary leakage destination: "
                    f"{leakage_geo_results['top_destination']} | "
                    f"Estimated top leakage value: "
                    f"{leakage_geo_results['top_leakage_value']:,.0f}"
                )