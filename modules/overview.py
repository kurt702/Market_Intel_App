import streamlit as st

from utils.formatting import (
    clean_numeric_column,
    shorten_name,
    build_recommended_groupings,
    build_recommended_metrics
)

from utils.charts import render_horizontal_bar


def render_overview(df, possible_fields, dataset_type, uploaded_files, dataframes):
    st.subheader("Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Files Uploaded", len(uploaded_files))

    with col2:
        st.metric("Rows", len(df))

    with col3:
        st.metric("Columns", len(df.columns))

    with col4:
        st.metric("Detected Dataset Type", dataset_type)

    with st.expander("Uploaded Files", expanded=False):
        st.write(list(dataframes.keys()))

    with st.expander("View Raw Dataset Preview", expanded=False):
        st.dataframe(df.head(), use_container_width=True)

    with st.expander("View Detected Healthcare Intelligence Fields", expanded=False):
        st.json(possible_fields)

    st.divider()

    st.subheader("Guided Custom Analysis")

    recommended_groupings = build_recommended_groupings(possible_fields)
    recommended_metrics = build_recommended_metrics(possible_fields)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    for col in recommended_metrics:
        if col not in numeric_cols:
            try:
                df = clean_numeric_column(df, col)
            except Exception:
                pass

    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    metric_options = [
        c for c in recommended_metrics
        if c in numeric_cols
    ]

    if not metric_options:
        metric_options = numeric_cols

    group_options = recommended_groupings

    if not group_options:
        group_options = df.columns.tolist()

    if metric_options and group_options:
        selected_metric = st.selectbox(
            "Select Recommended Metric",
            metric_options
        )

        group_col = st.selectbox(
            "Select Recommended Grouping",
            group_options
        )

        guided_df = (
            df.groupby(group_col)[selected_metric]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        guided_df = guided_df[
            guided_df[selected_metric] > 0
        ]

        display_df = guided_df.copy()
        display_df[group_col] = display_df[group_col].apply(shorten_name)

        st.dataframe(display_df, use_container_width=True)

        render_horizontal_bar(
            display_df,
            selected_metric,
            group_col,
            f"Top 10 {group_col} by {selected_metric}"
        )

    else:
        st.warning("No valid metric/grouping combination detected.")