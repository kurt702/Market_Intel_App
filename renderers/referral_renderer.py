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


def shorten_label(value, max_chars=48):
    value = str(value).split("(")[0].strip()

    if len(value) <= max_chars:
        return value

    return value[: max_chars - 3] + "..."


def generate_referral_infographic(results, output_path):
    referral_df = results["top_referrals_df"].copy()

    if referral_df.empty:
        raise ValueError("No referral data available to render.")

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
        "Executive Referral Pathway Intelligence Summary",
        "Directional referral pathway and network-retention summary generated from uploaded Definitive Healthcare CSV data"
    )

    ax1 = fig.add_subplot(gs[1, 0:3])
    ax2 = fig.add_subplot(gs[1, 3:6])
    ax3 = fig.add_subplot(gs[1, 6:9])
    ax4 = fig.add_subplot(gs[1, 9:12])

    top_pathway = (
        f"{shorten_label(results['top_origin'], 18)} → "
        f"{shorten_label(results['top_destination'], 18)}"
    )

    draw_kpi_card(
        ax1,
        "Top Pathway",
        top_pathway,
        "Largest directional referral lane",
    )

    draw_kpi_card(
        ax2,
        f"Total {value_label}",
        format_large_value(results["total_value"], value_label),
        "Across selected referral files",
    )

    draw_kpi_card(
        ax3,
        "External Share",
        f"{results['external_share']:.1f}%",
        "Share of pathways leaving origin",
    )

    draw_kpi_card(
        ax4,
        "Concentration",
        results["concentration"],
        "Referral distribution pattern",
    )

    chart_ax = fig.add_subplot(gs[2:5, 0:8])

    chart_df = referral_df.sort_values(
        "Value",
        ascending=True
    ).copy()

    chart_df["Pathway"] = (
        chart_df["Origin"]
        .astype(str)
        .apply(lambda x: shorten_label(x, 22))
        + " → "
        + chart_df["Destination"]
        .astype(str)
        .apply(lambda x: shorten_label(x, 32))
    )

    chart_ax.barh(
        chart_df["Pathway"],
        chart_df["Value"],
        color=PHILIPS_BLUE,
        height=0.62,
    )

    style_horizontal_bar_axis(
        chart_ax,
        "Top Referral Pathways",
        value_label
    )

    text_ax = fig.add_subplot(gs[2:5, 8:12])

    if results["concentration"] == "Highly Concentrated":
        interpretation = (
            "Referral pathways are highly concentrated, suggesting a small number "
            "of dominant directional relationships may be shaping network behavior."
        )

    elif results["concentration"] == "Moderately Concentrated":
        interpretation = (
            "Referral pathways are moderately concentrated, suggesting a mix of "
            "dominant lanes and broader network movement."
        )

    else:
        interpretation = (
            "Referral pathways are distributed, suggesting fragmented movement, "
            "a broad regional referral network, or diffuse leakage behavior."
        )

    callout = (
        f"Top 5 pathways represent {results['top_5_share']:.1f}% "
        f"of total identified {value_label.lower()}. "
        f"External pathways represent {results['external_share']:.1f}% "
        f"of observed pathway volume."
    )

    methodology = (
        "Detected source and destination fields where available; when a true origin "
        "field was absent, assigned a synthetic origin based on the selected market/account. "
        "Grouped directional pathways and summed the selected referral metric."
    )

    draw_strategy_panel(
        text_ax,
        title="Pathway Interpretation",
        body=interpretation,
        callout=callout,
        methodology=methodology,
    )

    footer_ax = fig.add_subplot(gs[5, :])

    draw_footer(
        footer_ax,
        "Source: Uploaded Definitive Healthcare CSV export | Generated locally using deterministic Python referral pathway analytics"
    )

    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return output_path