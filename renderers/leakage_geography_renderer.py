import plotly.express as px
import matplotlib.pyplot as plt

from renderers.theme import (
    PHILIPS_BLUE,
    CORAL,
    COOL_GRAY,
    FIGURE_SIZE_16_9,
    DPI,
)

from renderers.components import (
    draw_footer,
    draw_header,
    draw_kpi_card,
    draw_strategy_panel,
    style_horizontal_bar_axis,
)


def render_leakage_geography_overlay(
    overlay_df,
    geojson_data,
    title="Leakage Geography Overlay",
):
    """
    Geographic leakage overlay visualization.

    Combines:
    - patient ZIP intensity
    - estimated leakage opportunity
    - competitor capture geography
    """

    if overlay_df is None or overlay_df.empty:

        return {
            "success": False,
            "error": "Overlay dataframe empty."
        }

    fig = px.choropleth(
        overlay_df,

        geojson=geojson_data,

        locations="ZIP",

        featureidkey="properties.ZCTA5CE10",

        color="Estimated Leakage Value",

        hover_name="ZIP",

        hover_data={
            "ZIP": False,
            "ZIP Volume": ":,.0f",
            "ZIP Share": ":.1f",
            "Estimated Leakage Value": ":,.0f",
            "Primary Leakage Destination": True,
        },

        color_continuous_scale=[
            [0.0, "#DCEBFA"],
            [0.25, "#9CF6FB"],
            [0.55, "#0B5ED7"],
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

    fig.update_layout(
        height=900,

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
            title="Estimated Leakage"
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


def _format_large_value(value):
    try:
        value = float(value)
    except Exception:
        value = 0

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def generate_leakage_geography_infographic(results, output_path):
    overlay_df = results["overlay_df"].copy()

    if overlay_df.empty:
        raise ValueError("No leakage geography data available to render.")

    fig = plt.figure(
        figsize=FIGURE_SIZE_16_9,
        dpi=DPI,
        facecolor=COOL_GRAY,
    )

    gs = fig.add_gridspec(
        6,
        12,
        left=0.035,
        right=0.965,
        top=0.94,
        bottom=0.06,
        hspace=0.65,
        wspace=0.55,
    )

    header_ax = fig.add_subplot(gs[0, :])
    draw_header(
        header_ax,
        "Executive Leakage Geography Intelligence",
        "Estimated leakage opportunity overlaid against patient-origin ZIP demand"
    )

    top_zip = overlay_df.iloc[0]["ZIP"]
    top_zip_volume = overlay_df.iloc[0]["ZIP Volume"]
    top_zip_share = overlay_df.iloc[0]["ZIP Share"]
    total_estimated = overlay_df["Estimated Leakage Value"].sum()

    ax1 = fig.add_subplot(gs[1, 0:3])
    ax2 = fig.add_subplot(gs[1, 3:6])
    ax3 = fig.add_subplot(gs[1, 6:9])
    ax4 = fig.add_subplot(gs[1, 9:12])

    draw_kpi_card(
        ax1,
        "Top ZIP",
        top_zip,
        "Highest origin volume",
    )
    draw_kpi_card(
        ax2,
        "Top ZIP Share",
        f"{top_zip_share:.1f}%",
        f"{top_zip_volume:,.0f} ZIP records",
    )
    draw_kpi_card(
        ax3,
        "Primary Destination",
        str(results["top_destination"])[:24],
        "Largest leakage destination",
    )
    draw_kpi_card(
        ax4,
        "Estimated Leakage",
        _format_large_value(total_estimated),
        "ZIP-weighted opportunity",
        accent_color=CORAL,
    )

    chart_ax = fig.add_subplot(gs[2:5, 0:8])
    chart_df = (
        overlay_df.head(20)
        .sort_values("Estimated Leakage Value", ascending=True)
        .copy()
    )

    chart_ax.barh(
        chart_df["ZIP"],
        chart_df["Estimated Leakage Value"],
        color=PHILIPS_BLUE,
        height=0.62,
    )

    style_horizontal_bar_axis(
        chart_ax,
        "Estimated Leakage Opportunity by ZIP",
        "Estimated Leakage",
    )

    text_ax = fig.add_subplot(gs[2:5, 8:12])
    draw_strategy_panel(
        text_ax,
        title="Strategic Interpretation",
        body=(
            "Leakage geography combines patient-origin ZIP demand with the top "
            "external destination to show where retention and pathway-conversion "
            "work is likely to matter most."
        ),
        callout=(
            f"{results['top_destination']} is the primary identified leakage "
            f"destination, with {_format_large_value(results['top_leakage_value'])} "
            "in top-destination value."
        ),
        methodology=(
            "ZIP records were normalized and summarized, then weighted by ZIP share "
            "against the leading leakage destination value."
        ),
    )

    footer_ax = fig.add_subplot(gs[5, :])
    draw_footer(
        footer_ax,
        "Source: Uploaded Definitive Healthcare CSV export | Generated locally using deterministic Python leakage geography analytics"
    )

    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return output_path
