import textwrap

from matplotlib.patches import FancyBboxPatch, Rectangle

from renderers.theme import (
    PHILIPS_BLUE,
    DARK_BLUE,
    LIGHT_BLUE,
    DARK_TEXT,
    WHITE,
)


def wrap_text(text, width=44):
    return "\n".join(textwrap.wrap(str(text), width=width))


def draw_header(ax, title, subtitle=None):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            facecolor=DARK_BLUE,
            linewidth=0
        )
    )

    ax.text(
        0.035,
        0.62,
        title,
        fontsize=25,
        weight="bold",
        color=WHITE,
        va="center"
    )

    if subtitle:
        ax.text(
            0.037,
            0.24,
            subtitle,
            fontsize=10.5,
            color=LIGHT_BLUE,
            va="center"
        )


def draw_kpi_card(ax, title, value, subtitle=None, accent_color=PHILIPS_BLUE):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    card = FancyBboxPatch(
        (0, 0),
        1,
        1,
        boxstyle="round,pad=0.018,rounding_size=0.035",
        linewidth=0.7,
        edgecolor="#E5E7EB",
        facecolor=WHITE,
    )
    ax.add_patch(card)

    ax.add_patch(
        Rectangle(
            (0.04, 0.12),
            0.012,
            0.76,
            facecolor=accent_color,
            linewidth=0
        )
    )

    ax.text(
        0.08,
        0.73,
        str(title).upper(),
        fontsize=8.8,
        color=DARK_BLUE,
        weight="bold",
        va="center"
    )

    value_text = str(value)
    value_fontsize = 19

    if len(value_text) > 24:
        value_fontsize = 12.5
    elif len(value_text) > 18:
        value_fontsize = 14.5
    elif len(value_text) > 14:
        value_fontsize = 16.5

    ax.text(
        0.08,
        0.43,
        value_text,
        fontsize=value_fontsize,
        color=DARK_TEXT,
        weight="bold",
        va="center"
    )

    if subtitle:
        ax.text(
            0.08,
            0.17,
            str(subtitle),
            fontsize=8.2,
            color="#6B7280",
            va="center"
        )


def draw_strategy_panel(
    ax,
    title,
    body,
    callout=None,
    methodology=None,
    body_width=44
):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    panel = FancyBboxPatch(
        (0, 0),
        1,
        1,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        linewidth=0.7,
        edgecolor="#E5E7EB",
        facecolor=WHITE,
    )
    ax.add_patch(panel)

    ax.text(
        0.06,
        0.91,
        title,
        fontsize=15,
        weight="bold",
        color=DARK_BLUE,
        va="top"
    )

    ax.text(
        0.06,
        0.74,
        wrap_text(body, body_width),
        fontsize=11,
        color=DARK_TEXT,
        va="top",
        linespacing=1.35
    )

    if callout:
        ax.text(
            0.06,
            0.40,
            wrap_text(callout, body_width),
            fontsize=10.8,
            color=PHILIPS_BLUE,
            weight="bold",
            va="top",
            linespacing=1.35
        )

    if methodology:
        ax.text(
            0.06,
            0.18,
            "Methodology",
            fontsize=9.5,
            color=DARK_BLUE,
            weight="bold",
            va="top"
        )

        ax.text(
            0.06,
            0.10,
            wrap_text(methodology, body_width),
            fontsize=8.3,
            color="#6B7280",
            va="top",
            linespacing=1.25
        )


def draw_footer(ax, source_text):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0,
        0.55,
        source_text,
        fontsize=8.8,
        color="#6B7280",
        va="center"
    )


def style_horizontal_bar_axis(ax, title, xlabel):
    ax.set_title(
        title,
        fontsize=16,
        weight="bold",
        color=DARK_BLUE,
        pad=14,
        loc="left",
    )

    ax.tick_params(axis="y", labelsize=8.5)
    ax.tick_params(axis="x", labelsize=8.5, colors="#6B7280")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#D1D5DB")

    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, fontsize=9, color="#6B7280")
