from pathlib import Path

import pandas as pd
import streamlit as st

from analytics.executive_packet_engine import generate_executive_packet


APP_ROOT = Path(__file__).resolve().parents[1]


def render_executive_packet(df, routed_datasets=None):
    st.subheader("Executive Packet")

    st.write(
        "Generate a complete executive output packet from the uploaded CSVs."
    )

    routed_datasets = routed_datasets or st.session_state.get(
        "routed_datasets",
        {}
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "ZIP Dataset",
            "Available" if routed_datasets.get("zip_df") is not None else "Not routed",
        )

    with col2:
        st.metric(
            "Leakage Dataset",
            "Available" if routed_datasets.get("leakage_df") is not None else "Not routed",
        )

    with col3:
        st.metric(
            "Referral Dataset",
            "Available" if routed_datasets.get("referral_df") is not None else "Not routed",
        )

    routed_profiles = routed_datasets.get("profiles", [])

    if routed_profiles:
        with st.expander("Routed Dataset Debug", expanded=False):
            st.dataframe(
                pd.DataFrame(routed_profiles)[
                    ["file", "role", "reason", "rows", "columns"]
                ],
                width="stretch",
            )

    if st.button("Generate Executive Packet", type="primary"):
        with st.spinner("Generating executive packet..."):
            packet = generate_executive_packet(
                routed_datasets=routed_datasets,
                app_root=APP_ROOT,
                fallback_df=df,
            )

        st.success("Executive packet generated.")

        st.subheader("Packet Preview")

        preview_tabs = [
            ("cover", "Cover"),
            ("leakage_summary", "Leakage"),
            ("zip_geography", "ZIP Geography"),
            ("referral_pathways", "Referral Pathways"),
            ("leakage_geography", "Leakage Geography"),
        ]
        generated_by_key = {
            output["key"]: output
            for output in packet["generated"]
        }
        skipped_by_key = {
            output["key"]: output
            for output in packet["skipped"]
        }
        tabs = st.tabs([label for _, label in preview_tabs])

        for tab, (key, label) in zip(tabs, preview_tabs):
            with tab:
                output = generated_by_key.get(key)

                if output:
                    path = Path(output["path"])
                    st.image(path, width="stretch")
                    st.caption(f"{label} PNG: `{path}`")
                else:
                    skipped = skipped_by_key.get(key, {})
                    st.info(
                        skipped.get(
                            "reason",
                            "This packet layer was not generated.",
                        )
                    )

        if packet["skipped"]:
            with st.expander("Skipped Outputs", expanded=False):
                for skipped in packet["skipped"]:
                    st.write(
                        f"{skipped['label']}: {skipped['reason']}"
                    )

        with st.expander("Generated File Paths", expanded=False):
            for output in packet["generated"]:
                path = Path(output["path"])
                st.write(f"{output['label']}: `{path}`")

        st.subheader("Executive Summary")

        for bullet in packet["summary_bullets"]:
            st.write(bullet)

        summary_path = Path(packet["summary_path"])
        st.download_button(
            "Download Executive Summary",
            data=summary_path.read_text(encoding="utf-8"),
            file_name=summary_path.name,
            mime="text/plain",
        )

        zip_path = Path(packet["zip_path"])

        if zip_path.exists():
            st.download_button(
                "Download Executive Packet ZIP",
                data=zip_path.read_bytes(),
                file_name=zip_path.name,
                mime="application/zip",
                type="primary",
            )
