import matplotlib.pyplot as plt

from renderers.theme import (
    PHILIPS_BLUE,
    DARK_BLUE,
    LIGHT_BLUE,
    COOL_GRAY,
    DARK_TEXT,
    WHITE,
    CORAL,
    FIGURE_SIZE_16_9,
    DPI,
)

from renderers.components import (
    draw_header,
    draw_kpi_card,
    draw_strategy_panel,
    draw_footer,
    style_horizontal_bar_axis,
)


INTENSITY_COLORS = {
    "Very High": "#00126E",
    "High": "#0B5ED7",
    "Moderate": "#9CF6FB",
    "Low": "#DCEBFA",
}


def format_large_value(value, value_label="Volume"):
    try:
        value = float(value)
    except Exception:
        value = 0

    if value_label == "Charges":
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"

        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"

        if value >= 1_000:
            return f"${value / 1_000:.1f}K"

        return f"${value:,.0f}"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"

    if value >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"


def generate_heatmap_infographic(results, output_path):
    map_df = results["map_df"].copy()

    if map_df.empty:
        raise ValueError("No geography data available.")

    value_label = results.get("value_label", "Volume")

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

    # =========================
    # HEADER
    # =========================

    header_ax = fig.add_subplot(gs[0, :])

    draw_header(
        header_ax,
        "Executive Geographic Heat Map Intelligence",
        "ZIP-level patient-origin concentration and heat intensity analysis"
    )

    # =========================
    # KPI CARDS
    # =========================

    ax1 = fig.add_subplot(gs[1, 0:3])
    ax2 = fig.add_subplot(gs[1, 3:6])
    ax3 = fig.add_subplot(gs[1, 6:9])
    ax4 = fig.add_subplot(gs[1, 9:12])

    draw_kpi_card(
        ax1,
        "Top ZIP",
        results["top_zip"],
        "Highest concentration geography",
    )

    draw_kpi_card(
        ax2,
        f"Total {value_label}",
        format_large_value(
            results["total_value"],
            value_label
        ),
        "Across analyzed ZIP geography",
    )

    draw_kpi_card(
        ax3,
        "Top ZIP Share",
        f"{results['top_share']:.1f}%",
        "Relative market concentration",
    )

    draw_kpi_card(
        ax4,
        "Concentration",
        results["concentration"],
        "Geographic distribution profile",
        accent_color=CORAL
    )

    # =========================
    # HEATMAP BAR VISUAL
    # =========================

    chart_ax = fig.add_subplot(gs[2:5, 0:8])

    chart_df = (
        map_df.head(20)
        .sort_values("Value", ascending=True)
        .copy()
    )

    colors = [
        INTENSITY_COLORS.get(i, PHILIPS_BLUE)
        for i in chart_df["Intensity"]
    ]

    chart_ax.barh(
        chart_df["ZIP"],
        chart_df["Value"],
        color=colors,
        height=0.62,
    )

    style_horizontal_bar_axis(
        chart_ax,
        "Geographic Heat Intensity by ZIP",
        value_label
    )

    # =========================
    # STRATEGIC INTERPRETATION
    # =========================

    text_ax = fig.add_subplot(gs[2:5, 8:12])

    if results["concentration"] == "Highly Concentrated":

        interpretation = (
            "Patient-origin geography is highly concentrated within a relatively "
            "narrow ZIP footprint, suggesting strong dominance in core-market regions."
        )

    elif results["concentration"] == "Moderately Concentrated":

        interpretation = (
            "Patient-origin geography demonstrates moderate concentration, suggesting "
            "a combination of dominant ZIP clusters and broader regional draw."
        )

    else:

        interpretation = (
            "Patient-origin geography appears broadly distributed, suggesting a "
            "regional referral footprint with diffuse market capture."
        )

    callout = (
        f"Top 5 ZIPs represent "
        f"{results['top_5_share']:.1f}% "
        f"of total identified "
        f"{value_label.lower()}."
    )

    methodology = (
        "ZIP codes were standardized to 5-digit geography, aggregated by "
        "selected metric, normalized into market share percentages, and "
        "classified into heat intensity tiers."
    )

    draw_strategy_panel(
        text_ax,
        title="Geographic Interpretation",
        body=interpretation,
        callout=callout,
        methodology=methodology,
    )

    # =========================
    # FOOTER
    # =========================

    footer_ax = fig.add_subplot(gs[5, :])

    draw_footer(
        footer_ax,
        "Source: Uploaded Definitive Healthcare CSV export | Generated locally using deterministic Python geographic heat intelligence"
    )

    # =========================
    # SAVE
    # =========================

    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return output_path