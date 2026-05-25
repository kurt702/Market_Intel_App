from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.pyplot as plt

from renderers.components import (
    draw_footer,
    draw_kpi_card,
    wrap_text,
)
from renderers.design_system import (
    CARD_SHADOW,
    COOL_GRAY,
    CORAL,
    DARK_BLUE,
    DARK_TEXT,
    DPI,
    FIGURE_SIZE_16_9,
    GRID_LINE,
    KPI_COLORS,
    LIGHT_BLUE,
    MID_TEXT,
    PHILIPS_BLUE,
    SOFT_BLUE,
    SOFT_CORAL,
    WHITE,
)


def draw_executive_header(ax, title, subtitle):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            facecolor=DARK_BLUE,
            linewidth=0,
        )
    )
    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            0.055,
            facecolor=PHILIPS_BLUE,
            linewidth=0,
        )
    )
    ax.add_patch(
        Rectangle(
            (0.022, 0.18),
            0.010,
            0.64,
            facecolor=SOFT_CORAL,
            linewidth=0,
        )
    )
    ax.text(
        0.045,
        0.63,
        title,
        fontsize=28,
        weight="bold",
        color=WHITE,
        va="center",
    )
    ax.text(
        0.047,
        0.29,
        subtitle,
        fontsize=11.5,
        color=LIGHT_BLUE,
        va="center",
    )
    ax.text(
        0.965,
        0.66,
        "EXECUTIVE PACKET",
        fontsize=8.5,
        color=LIGHT_BLUE,
        weight="bold",
        ha="right",
        va="center",
    )


def create_onepager(title, subtitle):
    fig = plt.figure(
        figsize=FIGURE_SIZE_16_9,
        dpi=DPI,
        facecolor=COOL_GRAY,
    )

    gs = fig.add_gridspec(
        12,
        12,
        left=0.035,
        right=0.965,
        top=0.955,
        bottom=0.055,
        hspace=0.42,
        wspace=0.42,
    )

    header_ax = fig.add_subplot(gs[0:2, :])
    draw_executive_header(header_ax, title, subtitle)

    kpi_axes = [
        fig.add_subplot(gs[2:4, 0:3]),
        fig.add_subplot(gs[2:4, 3:6]),
        fig.add_subplot(gs[2:4, 6:9]),
        fig.add_subplot(gs[2:4, 9:12]),
    ]

    visual_ax = fig.add_subplot(gs[4:10, 0:8])
    insight_ax = fig.add_subplot(gs[4:10, 8:12])
    footer_ax = fig.add_subplot(gs[10:12, :])

    return {
        "fig": fig,
        "kpi_axes": kpi_axes,
        "visual_ax": visual_ax,
        "insight_ax": insight_ax,
        "footer_ax": footer_ax,
    }


def draw_card(ax, x, y, width, height, facecolor=WHITE, edgecolor="#DCE3EC"):
    shadow = FancyBboxPatch(
        (x + 0.006, y - 0.008),
        width,
        height,
        boxstyle="round,pad=0.014,rounding_size=0.022",
        linewidth=0,
        facecolor=CARD_SHADOW,
        alpha=0.32,
    )
    ax.add_patch(shadow)

    card = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.014,rounding_size=0.022",
        linewidth=0.8,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(card)
    return card


def draw_kpi_row(kpi_axes, kpis):
    for idx, ax in enumerate(kpi_axes):
        if idx >= len(kpis):
            ax.axis("off")
            continue

        kpi = kpis[idx]
        draw_kpi_card(
            ax,
            kpi["title"],
            kpi["value"],
            kpi.get("subtitle"),
            accent_color=kpi.get("accent_color", KPI_COLORS[idx % len(KPI_COLORS)]),
        )


def draw_executive_panel(
    ax,
    title,
    interpretation,
    what_this_means,
    methodology=None,
):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    shadow = FancyBboxPatch(
        (0.010, -0.012),
        1,
        1,
        boxstyle="round,pad=0.028,rounding_size=0.032",
        linewidth=0,
        facecolor=CARD_SHADOW,
        alpha=0.28,
        clip_on=False,
    )
    ax.add_patch(shadow)

    panel = FancyBboxPatch(
        (0, 0),
        1,
        1,
        boxstyle="round,pad=0.028,rounding_size=0.032",
        linewidth=0.8,
        edgecolor="#DCE3EC",
        facecolor=WHITE,
    )
    ax.add_patch(panel)

    ax.text(
        0.06,
        0.93,
        title,
        fontsize=15,
        weight="bold",
        color=DARK_BLUE,
        va="top",
    )

    ax.add_patch(
        Rectangle(
            (0.06, 0.82),
            0.16,
            0.012,
            facecolor=PHILIPS_BLUE,
            linewidth=0,
        )
    )

    ax.text(
        0.06,
        0.76,
        wrap_text(interpretation, 42),
        fontsize=10.6,
        color=DARK_TEXT,
        va="top",
        linespacing=1.38,
    )

    callout = FancyBboxPatch(
        (0.055, 0.29),
        0.89,
        0.23,
        boxstyle="round,pad=0.018,rounding_size=0.022",
        linewidth=0,
        facecolor=SOFT_BLUE,
    )
    ax.add_patch(callout)

    ax.text(
        0.08,
        0.47,
        "WHAT THIS MEANS",
        fontsize=8.8,
        weight="bold",
        color=PHILIPS_BLUE,
        va="top",
    )

    ax.text(
        0.08,
        0.40,
        wrap_text(what_this_means, 38),
        fontsize=10,
        color=DARK_BLUE,
        va="top",
        linespacing=1.30,
        weight="bold",
    )

    if methodology:
        ax.text(
            0.06,
            0.19,
            "Methodology",
            fontsize=9,
            color=DARK_BLUE,
            weight="bold",
            va="top",
        )
        ax.text(
            0.06,
            0.12,
            wrap_text(methodology, 42),
            fontsize=8.3,
            color=MID_TEXT,
            va="top",
            linespacing=1.2,
        )


def style_primary_axis(ax, title, xlabel=None):
    ax.set_facecolor(WHITE)
    ax.set_title(
        title,
        fontsize=15,
        weight="bold",
        color=DARK_BLUE,
        loc="left",
        pad=12,
    )
    ax.tick_params(axis="y", labelsize=8.5, colors=DARK_TEXT)
    ax.tick_params(axis="x", labelsize=8.5, colors=MID_TEXT)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID_LINE)
    ax.grid(axis="x", color=GRID_LINE, linewidth=0.8)
    ax.set_axisbelow(True)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=MID_TEXT)


def add_visual_frame(ax):
    shadow = FancyBboxPatch(
        (-0.026, -0.061),
        1.07,
        1.09,
        transform=ax.transAxes,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=0,
        facecolor=CARD_SHADOW,
        alpha=0.26,
        zorder=-30,
        clip_on=False,
    )
    ax.add_patch(shadow)

    frame = FancyBboxPatch(
        (-0.035, -0.045),
        1.07,
        1.09,
        transform=ax.transAxes,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=0.8,
        edgecolor="#DCE3EC",
        facecolor=WHITE,
        zorder=-20,
        clip_on=False,
    )
    ax.add_patch(frame)


def draw_source_footer(ax, source_text):
    draw_footer(ax, source_text)
    ax.text(
        1,
        0.55,
        "Market Intelligence Executive Packet",
        fontsize=8.5,
        color=CORAL,
        weight="bold",
        ha="right",
        va="center",
    )


def save_onepager(fig, output_path):
    fig.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    return output_path
