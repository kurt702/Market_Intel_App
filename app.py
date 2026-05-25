from pathlib import Path
import sys

import streamlit as st
import pandas as pd


APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

OUTPUTS_DIR = APP_ROOT / "outputs" / "png"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

from utils.schema import detect_fields, detect_dataset_type
from utils.file_selection import get_module_candidate_files, build_file_profiles
from utils.dataset_router import route_uploaded_datasets

from modules.overview import render_overview
from modules.hospital_volume import render_hospital_volume
from modules.icd_analysis import render_icd_analysis
from modules.leakage import render_leakage
from modules.zip_geography import render_zip_geography
from modules.referral_analysis import render_referral_analysis
from modules.executive_packet import render_executive_packet


st.set_page_config(
    page_title="Market Intelligence Heat Map Generator",
    layout="wide"
)

st.title("Market Intelligence Heat Map Generator")

st.sidebar.title("Analytics Modules")

selected_module = st.sidebar.radio(
    "Select Analysis",
    [
        "Overview",
        "Hospital Volume",
        "ICD Analysis",
        "Leakage",
        "ZIP Geography",
        "Referral Analysis",
        "Executive Packet"
    ]
)

uploaded_files = st.file_uploader(
    "Upload Definitive CSV files",
    type=["csv"],
    accept_multiple_files=True
)


if uploaded_files:
    dataframes = {}

    for uploaded_file in uploaded_files:
        dataframes[uploaded_file.name] = pd.read_csv(uploaded_file)

    # =========================
    # ROUTED DATASET INTELLIGENCE
    # =========================

    routed_datasets = route_uploaded_datasets(dataframes)

    st.session_state["routed_datasets"] = routed_datasets

    file_profiles = build_file_profiles(dataframes)

    module_candidate_files = get_module_candidate_files(
        selected_module,
        file_profiles
    )

    auto_select_module_files = st.checkbox(
        f"Auto-select best files for {selected_module}",
        value=True
    )

    default_files = (
        module_candidate_files
        if auto_select_module_files and module_candidate_files
        else [list(dataframes.keys())[0]]
    )

    selected_file_names = st.multiselect(
        "Select file(s) to analyze",
        list(dataframes.keys()),
        default=default_files
    )

    if not selected_file_names:
        st.warning("Select at least one file to analyze.")
        st.stop()

    selected_dfs = []

    for file_name in selected_file_names:
        temp_df = dataframes[file_name].copy()
        temp_df["_source_file"] = file_name
        selected_dfs.append(temp_df)

    df = pd.concat(
        selected_dfs,
        ignore_index=True,
        sort=False
    )

    selected_file_name = (
        selected_file_names[0]
        if len(selected_file_names) == 1
        else f"{len(selected_file_names)} files combined"
    )

    possible_fields = detect_fields(df)
    dataset_type = detect_dataset_type(possible_fields)

    st.sidebar.success(f"Detected: {dataset_type}")

    st.caption(f"Currently analyzing: **{selected_file_name}**")

    with st.expander("Uploaded File Profiles", expanded=False):
        profile_rows = []

        for file_name, profile in file_profiles.items():
            profile_rows.append({
                "File": file_name,
                "Detected Type": profile["dataset_type"],
                "ZIP Fields": ", ".join(profile["fields"].get("ZIP", [])),
                "Hospital Fields": ", ".join(profile["fields"].get("Hospital", [])),
                "Charges Fields": ", ".join(profile["fields"].get("Charges", [])),
                "Volume Fields": ", ".join(profile["fields"].get("Volume", [])),
            })

        st.dataframe(pd.DataFrame(profile_rows), width="stretch")

    with st.expander("Routed Dataset Intelligence", expanded=False):
        routed_profiles = routed_datasets.get("profiles", [])

        if routed_profiles:
            st.dataframe(
                pd.DataFrame(routed_profiles),
                width="stretch"
            )

        st.write(
            {
                "ZIP File": routed_datasets.get("zip_file"),
                "Leakage File": routed_datasets.get("leakage_file"),
                "Referral File": routed_datasets.get("referral_file"),
            }
        )

    module_expected_types = {
        "Leakage": [
            "Leakage Analysis",
            "Inpatient DRG Leakage",
            "Outpatient HCPCS Leakage"
        ],
        "Hospital Volume": ["Hospital Procedure Volume"],
        "ICD Analysis": ["ICD Procedure Volume"],
        "ZIP Geography": ["ZIP Geography"],
    }

    if selected_module in module_expected_types:
        if dataset_type not in module_expected_types[selected_module]:
            st.warning(
                f"Selected file appears to be **{dataset_type}**, but you are viewing **{selected_module}**. "
                "Choose a matching CSV or switch modules."
            )

    if selected_module == "Overview":
        render_overview(
            df=df,
            possible_fields=possible_fields,
            dataset_type=dataset_type,
            uploaded_files=uploaded_files,
            dataframes=dataframes
        )

    elif selected_module == "Hospital Volume":
        render_hospital_volume(
            df=df,
            possible_fields=possible_fields
        )

    elif selected_module == "ICD Analysis":
        render_icd_analysis(
            df=df,
            possible_fields=possible_fields
        )

    elif selected_module == "Leakage":
        render_leakage(df=df)

    elif selected_module == "ZIP Geography":
        render_zip_geography(df=df)

    elif selected_module == "Referral Analysis":
        render_referral_analysis(df=df)

    elif selected_module == "Executive Packet":
        render_executive_packet(
            df=df,
            routed_datasets=routed_datasets
        )

    st.divider()

    st.download_button(
        label="Download Current Processed CSV",
        data=df.to_csv(index=False),
        file_name=f"processed_{selected_file_name}.csv",
        mime="text/csv"
    )

else:
    st.info("Upload one or more Definitive CSV files to begin analysis.")
