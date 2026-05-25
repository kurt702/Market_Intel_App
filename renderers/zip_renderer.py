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


def generate_zip_infographic(results, output_path):
    zip_df = results["top_zips_df"].copy()

    if zip_df.empty:
        raise ValueError("No ZIP data available to render.")

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

    header_ax = fig.add_subplot(gs[0, :])

    draw_header(
        header_ax,
        "Executive ZIP Geography Intelligence Summary",
        "Patient-origin concentration and market-tier summary generated from uploaded Definitive Healthcare CSV data"
    )

    ax1 = fig.add_subplot(gs[1, 0:3])
    ax2 = fig.add_subplot(gs[1, 3:6])
    ax3 = fig.add_subplot(gs[1, 6:9])
    ax4 = fig.add_subplot(gs[1, 9:12])

    draw_kpi_card(
        ax1,
        "Top ZIP",
        results["top_zip"],
        "Largest patient-origin ZIP",
    )

    draw_kpi_card(
        ax2,
        f"Total {value_label}",
        format_large_value(results["total_value"], value_label),
        "Across selected ZIP files",
    )

    draw_kpi_card(
        ax3,
        "Top ZIP Share",
        f"{results['top_share']:.1f}%",
        "Share from leading ZIP",
    )

    draw_kpi_card(
        ax4,
        "Concentration",
        results["concentration"],
        "Geographic distribution pattern",
    )

    chart_ax = fig.add_subplot(gs[2:5, 0:8])

    chart_df = zip_df.sort_values(
        "Value",
        ascending=True
    ).copy()

    chart_ax.barh(
        chart_df["ZIP"],
        chart_df["Value"],
        color=PHILIPS_BLUE,
        height=0.62,
    )

    style_horizontal_bar_axis(
        chart_ax,
        "Top ZIP Patient-Origin Concentration",
        value_label
    )

    text_ax = fig.add_subplot(gs[2:5, 8:12])

    if results["concentration"] == "Highly Concentrated":
        interpretation = (
            "Patient origin is highly concentrated in a narrow ZIP footprint, "
            "suggesting strong core-market dominance and a focused local draw."
        )

    elif results["concentration"] == "Moderately Concentrated":
        interpretation = (
            "Patient origin is moderately concentrated, suggesting a blend of "
            "core-market strength and broader regional draw."
        )

    else:
        interpretation = (
            "Patient origin is geographically distributed, suggesting a broad "
            "referral footprint, fragmented capture, or wider market opportunity."
        )

    draw_strategy_panel(
        text_ax,
        title="Geographic Interpretation",
        body=interpretation,
        callout=(
            f"Top 5 ZIPs represent "
            f"{results['top_5_share']:.1f}% "
            f"of total identified {value_label.lower()}."
        ),
        methodology=(
            "Cleaned ZIP codes to 5-digit format, grouped patient-origin geography, "
            "summed selected volume metric, and tiered ZIPs by cumulative market share."
        )
    )

    footer_ax = fig.add_subplot(gs[5, :])

    draw_footer(
        footer_ax,
        "Source: Uploaded Definitive Healthcare CSV export | Generated locally using deterministic Python geography analytics"
    )

    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return output_path