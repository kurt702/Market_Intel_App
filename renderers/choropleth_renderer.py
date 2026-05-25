import plotly.express as px


def render_zip_choropleth(
    choropleth_df,
    geojson_data=None,
    title="ZIP-Level Geographic Heat Map",
    viewport=None,
):
    """
    Renders an interactive ZIP-level choropleth map.

    If geojson_data is provided, renders true ZIP polygon geography.
    If viewport is provided, it dynamically centers/zooms the map.
    """

    if choropleth_df is None or choropleth_df.empty:
        return {
            "success": False,
            "error": "No choropleth dataframe provided."
        }

    if geojson_data is None:
        return {
            "success": False,
            "error": "No ZIP boundary GeoJSON loaded yet."
        }

    fig = px.choropleth(
        choropleth_df,
        geojson=geojson_data,
        locations="ZIP",
        featureidkey="properties.ZCTA5CE10",
        color="Intensity Score",
        hover_name="Map Label",
        hover_data={
            "ZIP": False,
            "Value": ":,.0f",
            "Share": ":.1f",
            "Intensity": True,
            "Map Label": False,
            "Intensity Score": False,
        },
        color_continuous_scale=[
            [0.0, "#DCEBFA"],
            [0.35, "#9CF6FB"],
            [0.65, "#0B5ED7"],
            [1.0, "#00126E"],
        ],
        title=title,
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showland=True,
        landcolor="#F8FAFC",
        bgcolor="white",
    )

    if viewport:
        fig.update_geos(
            center={
                "lat": viewport.get("lat", 39.5),
                "lon": viewport.get("lon", -98.35),
            },
            projection_scale=viewport.get("zoom", 3),
        )

    fig.update_layout(
        height=1050,
        width=1400,
        margin=dict(
            l=0,
            r=0,
            t=70,
            b=0
        ),
        title=dict(
            text=title,
            font=dict(
                size=24,
                color="#00126E",
                family="Arial"
            ),
            x=0.015,
            xanchor="left",
        ),
        coloraxis_colorbar=dict(
            title="Heat Intensity",
            tickvals=[1, 2, 3, 4],
            ticktext=[
                "Low",
                "Moderate",
                "High",
                "Very High"
            ],
            thickness=18,
            len=0.65,
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Arial",
            color="#00126E",
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
    )

    return {
        "success": True,
        "figure": fig
    }