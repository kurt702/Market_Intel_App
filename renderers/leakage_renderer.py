import matplotlib.pyplot as plt

from renderers.theme import (
    PHILIPS_BLUE,
    COOL_GRAY,
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


def format_large_value(value, value_label="Charges"):
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


def generate_leakage_infographic(results, output_path):
    leakage_df = results["top_destinations_df"].copy()

    if leakage_df.empty:
        raise ValueError("No leakage data available to render.")

    value_label = results.get("value_label", "Charges")

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
        "Executive Leakage Intelligence Summary",
        "Deterministic market intelligence summary generated from uploaded Definitive Healthcare CSV data"
    )

    ax1 = fig.add_subplot(gs[1, 0:3])
    ax2 = fig.add_subplot(gs[1, 3:6])
    ax3 = fig.add_subplot(gs[1, 6:9])
    ax4 = fig.add_subplot(gs[1, 9:12])

    draw_kpi_card(
        ax1,
        "Top Destination",
        str(results["top_destination"])[:26],
        "Largest identified leakage target",
    )

    draw_kpi_card(
        ax2,
        "Total Leakage",
        format_large_value(results["total_leakage"], value_label),
        value_label,
    )

    draw_kpi_card(
        ax3,
        "Top Share",
        f"{results['top_share']:.1f}%",
        "Share captured by top destination",
    )

    draw_kpi_card(
        ax4,
        "Concentration",
        results["concentration"],
        "Market distribution pattern",
    )

    chart_ax = fig.add_subplot(gs[2:5, 0:8])

    chart_df = leakage_df.sort_values(
        "Leakage Value",
        ascending=True
    ).copy()

    chart_df["Destination"] = (
        chart_df["Destination"]
        .astype(str)
        .apply(lambda x: x.split("(")[0].strip())
    )

    chart_ax.barh(
        chart_df["Destination"],
        chart_df["Leakage Value"],
        color=PHILIPS_BLUE,
        height=0.62,
    )

    style_horizontal_bar_axis(
        chart_ax,
        "Top Leakage Destinations",
        value_label
    )

    text_ax = fig.add_subplot(gs[2:5, 8:12])

    if results["concentration"] == "Highly Concentrated":
        interpretation = (
            "Leakage is highly concentrated among a small number of dominant competitors, "
            "suggesting focused referral retention and strategic account engagement opportunities."
        )

    elif results["concentration"] == "Moderately Concentrated":
        interpretation = (
            "Leakage is moderately concentrated, suggesting a blend of targeted account strategy "
            "and broader referral pathway optimization."
        )

    else:
        interpretation = (
            "Leakage appears broadly distributed across the market, suggesting fragmented referral "
            "behavior, access variability, or geographic dispersion."
        )

    draw_strategy_panel(
        text_ax,
        title="Strategic Interpretation",
        body=interpretation,
        callout=(
            f"Top 5 destinations represent "
            f"{results['top_5_share']:.1f}% "
            f"of total identified leakage."
        ),
        methodology=(
            "Grouped destination field and summed selected leakage metric."
        )
    )

    footer_ax = fig.add_subplot(gs[5, :])

    draw_footer(
        footer_ax,
        "Source: Uploaded Definitive Healthcare CSV export | Generated locally using deterministic Python analytics"
    )

    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return output_path