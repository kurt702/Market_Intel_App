import streamlit as st
import plotly.express as px


def render_horizontal_bar(df, x_col, y_col, title):
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        orientation="h",
        title=title
    )

    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        height=600,
        margin=dict(l=20, r=20, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)