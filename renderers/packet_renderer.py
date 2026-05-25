import math

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

from renderers.components import wrap_text
from renderers.design_system import (
    CARD_SHADOW,
    COOL_GRAY,
    CORAL,
    CYAN,
    DARK_BLUE,
    DARK_TEXT,
    DPI,
    FIGURE_SIZE_16_9,
    GRID_LINE,
    LIGHT_BLUE,
    MID_TEXT,
    PHILIPS_BLUE,
    SOFT_BLUE,
    SOFT_CORAL,
    WHITE,
)


BLUE_RAMP = ["#DCEBFA", "#BDF0FF", "#9CF6FB", "#0B5ED7", "#00126E"]
RISK_RAMP = ["#FFDEDB", "#FFB6AE", "#FF8A7D", "#FF6F61", "#D92332"]


def clean_label(value, max_chars=34):
    value = str(value).split("(")[0].strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3] + "..."


def format_large(value, value_label="Volume"):
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


def create_board(title, subtitle, kicker=None):
    fig = plt.figure(figsize=FIGURE_SIZE_16_9, dpi=DPI, facecolor=COOL_GRAY)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    if kicker:
        ax.text(
            0.020,
            0.973,
            kicker.upper(),
            fontsize=11,
            weight="bold",
            color=PHILIPS_BLUE,
            va="top",
        )

    ax.text(
        0.020,
        0.936,
        title,
        fontsize=30,
        weight="bold",
        color=DARK_BLUE,
        va="top",
    )
    ax.text(
        0.020,
        0.884,
        subtitle,
        fontsize=12.5,
        color=DARK_TEXT,
        va="top",
    )

    return fig, ax


def save_board(fig, output_path):
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def draw_panel(ax, x, y, w, h, title=None, subtitle=None, header=False):
    shadow = FancyBboxPatch(
        (x + 0.004, y - 0.006),
        w,
        h,
        boxstyle="round,pad=0.006,rounding_size=0.010",
        linewidth=0,
        facecolor=CARD_SHADOW,
        alpha=0.32,
    )
    ax.add_patch(shadow)

    panel = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.006,rounding_size=0.010",
        linewidth=0.8,
        edgecolor="#DDE5EF",
        facecolor=WHITE,
    )
    ax.add_patch(panel)

    if header:
        ax.add_patch(
            FancyBboxPatch(
                (x, y + h - 0.045),
                w,
                0.045,
                boxstyle="round,pad=0.006,rounding_size=0.010",
                linewidth=0,
                facecolor=DARK_BLUE,
            )
        )
        if title:
            ax.text(
                x + 0.018,
                y + h - 0.023,
                title.upper(),
                fontsize=10.5,
                weight="bold",
                color=WHITE,
                va="center",
            )
    elif title:
        ax.text(
            x + 0.018,
            y + h - 0.026,
            title.upper(),
            fontsize=12,
            weight="bold",
            color=PHILIPS_BLUE,
            va="center",
        )

    if subtitle and not header:
        ax.text(
            x + 0.018,
            y + h - 0.052,
            subtitle,
            fontsize=9.2,
            color=DARK_TEXT,
            va="center",
        )

    return panel


def draw_icon_circle(ax, cx, cy, label, color=PHILIPS_BLUE, radius=0.024):
    ax.add_patch(
        Circle(
            (cx, cy),
            radius,
            facecolor=color,
            edgecolor=WHITE,
            linewidth=1.4,
        )
    )
    ax.text(
        cx,
        cy,
        label,
        fontsize=12,
        color=WHITE,
        weight="bold",
        ha="center",
        va="center",
    )


def draw_kpi_cards(ax, kpis, x=0.540, y=0.860, w=0.105, h=0.105, gap=0.014):
    for idx, kpi in enumerate(kpis[:4]):
        card_x = x + idx * (w + gap)
        draw_panel(ax, card_x, y, w, h)
        icon = kpi.get("icon", ["P", "F", "$", "T"][idx])
        color = kpi.get("color", PHILIPS_BLUE if idx != 2 else DARK_BLUE)
        draw_icon_circle(ax, card_x + 0.027, y + h - 0.036, icon, color=color, radius=0.019)
        ax.text(
            card_x + 0.058,
            y + h - 0.035,
            str(kpi.get("value", "")),
            fontsize=18 if len(str(kpi.get("value", ""))) < 8 else 14,
            weight="bold",
            color=DARK_BLUE,
            va="center",
        )
        ax.text(
            card_x + 0.018,
            y + 0.025,
            wrap_text(kpi.get("label", ""), 19),
            fontsize=7.7,
            color=DARK_TEXT,
            va="bottom",
            linespacing=1.1,
        )


def _relative_score(value, max_value, min_score=64, max_score=95):
    try:
        value = float(value)
        max_value = float(max_value)
    except Exception:
        return min_score

    if max_value <= 0:
        return min_score

    score = min_score + (value / max_value) * (max_score - min_score)
    return int(round(min(max_score, max(min_score, score))))


def draw_ranked_list(
    ax,
    rows,
    x,
    y,
    w,
    h,
    title,
    subtitle,
    color=PHILIPS_BLUE,
    value_label="Volume",
    max_rows=5,
):
    draw_panel(ax, x, y, w, h, title=title, subtitle=subtitle)
    rows = list(rows)[:max_rows]
    if not rows:
        ax.text(x + 0.020, y + h * 0.50, "No data available", fontsize=10, color=MID_TEXT)
        return

    max_value = max([row["value"] for row in rows]) or 1
    row_gap = (h - 0.100) / max_rows
    start_y = y + h - 0.090

    for idx, row in enumerate(rows):
        row_y = start_y - idx * row_gap
        ax.text(
            x + 0.018,
            row_y,
            f"{idx + 1}.",
            fontsize=10.5,
            color=color,
            weight="bold",
            va="center",
        )
        ax.text(
            x + 0.050,
            row_y,
            clean_label(row["label"], 28),
            fontsize=8.8,
            color=DARK_TEXT,
            va="center",
        )
        bar_x = x + w * 0.56
        bar_w = w * 0.29
        ax.add_patch(
            Rectangle(
                (bar_x, row_y - 0.006),
                bar_w,
                0.012,
                facecolor=GRID_LINE,
                linewidth=0,
            )
        )
        ax.add_patch(
            Rectangle(
                (bar_x, row_y - 0.006),
                bar_w * (float(row["value"]) / max_value),
                0.012,
                facecolor=color,
                linewidth=0,
            )
        )
        ax.text(
            x + w - 0.018,
            row_y,
            format_large(row["value"], value_label),
            fontsize=8.4,
            color=DARK_BLUE,
            weight="bold",
            ha="right",
            va="center",
        )


def draw_dual_flow_summary(ax, left_rows, right_rows, x, y, w, h, title, left_title, right_title, value_label):
    draw_panel(ax, x, y, w, h, title=title, subtitle="Referral volume")
    divider_x = x + w * 0.50
    ax.plot([divider_x, divider_x], [y + 0.055, y + h - 0.070], color="#CBD5E1", linewidth=1)

    ax.text(x + 0.022, y + h - 0.075, left_title, fontsize=9.2, color=PHILIPS_BLUE, weight="bold", va="top")
    ax.text(divider_x + 0.022, y + h - 0.075, right_title, fontsize=9.2, color="#D92332", weight="bold", va="top")

    def draw_side(rows, sx, sw, color):
        rows = list(rows)[:5]
        max_value = max([row["value"] for row in rows]) if rows else 1
        for idx, row in enumerate(rows):
            row_y = y + h - 0.125 - idx * 0.043
            ax.text(sx, row_y, str(idx + 1), fontsize=8, color=WHITE, weight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.18", facecolor=color, edgecolor="none"))
            ax.text(sx + 0.020, row_y, clean_label(row["label"], 25), fontsize=7.9, color=DARK_TEXT, va="center")
            bar_x = sx + sw * 0.56
            bar_w = sw * 0.30
            ax.add_patch(Rectangle((bar_x, row_y - 0.005), bar_w, 0.010, facecolor=GRID_LINE, linewidth=0))
            ax.add_patch(Rectangle((bar_x, row_y - 0.005), bar_w * (row["value"] / max_value), 0.010, facecolor=color, linewidth=0))
            ax.text(sx + sw - 0.010, row_y, format_large(row["value"], value_label), fontsize=7.6, color=DARK_BLUE, ha="right", va="center")

    draw_side(left_rows, x + 0.030, w * 0.43, PHILIPS_BLUE)
    draw_side(right_rows, divider_x + 0.030, w * 0.43, "#E60023")


def draw_intensity_field(ax, rows, x, y, w, h, title, subtitle, center_label="Market", value_label="Volume", risk=False):
    draw_panel(ax, x, y, w, h, title=title, subtitle=subtitle)
    rows = list(rows)[:140]

    plot_x0 = x + 0.018
    plot_y0 = y + 0.050
    plot_w = w - 0.036
    plot_h = h - 0.110

    for gx in range(6):
        px = plot_x0 + plot_w * gx / 5
        ax.plot([px, px], [plot_y0, plot_y0 + plot_h], color="#EEF2F7", linewidth=0.8)
    for gy in range(5):
        py = plot_y0 + plot_h * gy / 4
        ax.plot([plot_x0, plot_x0 + plot_w], [py, py], color="#EEF2F7", linewidth=0.8)

    max_value = max([row["value"] for row in rows]) if rows else 1
    palette = RISK_RAMP if risk else BLUE_RAMP

    for idx, row in enumerate(rows):
        value = row["value"]
        rank = idx + 1
        angle = rank * 2.399
        radius = min(0.48, 0.08 + (rank / max(1, len(rows))) * 0.42)
        px = plot_x0 + plot_w * (0.50 + math.cos(angle) * radius * 0.82)
        py = plot_y0 + plot_h * (0.50 + math.sin(angle) * radius)
        intensity = min(4, int((float(value) / max_value) * 4.99))
        size = 18 + 95 * (float(value) / max_value)
        ax.scatter(px, py, s=size, color=palette[intensity], alpha=0.72, edgecolors=WHITE, linewidths=0.4, zorder=4)

    ax.scatter(plot_x0 + plot_w * 0.53, plot_y0 + plot_h * 0.50, s=520, color=DARK_BLUE, edgecolors=WHITE, linewidths=2.5, zorder=6)
    ax.text(plot_x0 + plot_w * 0.58, plot_y0 + plot_h * 0.50, clean_label(center_label, 24), fontsize=12, weight="bold", color=DARK_BLUE, va="center")

    top_rows = rows[:5]
    for idx, row in enumerate(top_rows):
        lx = plot_x0 + 0.015 + (idx % 2) * plot_w * 0.52
        ly = plot_y0 + plot_h - 0.035 - (idx // 2) * 0.050
        ax.text(lx, ly, clean_label(row["label"], 18), fontsize=7.8, color=DARK_BLUE, weight="bold")

    legend_x = x + 0.030
    legend_y = y + 0.068
    labels = ["Low", "Moderate", "High", "Very High"]
    for idx, label in enumerate(labels):
        ax.scatter(legend_x, legend_y + idx * 0.022, s=52, color=palette[min(idx + 1, 4)], edgecolors=WHITE, linewidths=0.4)
        ax.text(legend_x + 0.018, legend_y + idx * 0.022, label, fontsize=7.4, color=DARK_TEXT, va="center")


def draw_opportunity_table(
    ax,
    rows,
    x,
    y,
    w,
    h,
    title,
    subtitle,
    value_header,
    value_label,
    score_label="Priority Index",
):
    draw_panel(ax, x, y, w, h, title=title, subtitle=subtitle)
    rows = list(rows)[:5]
    max_value = max([row["value"] for row in rows]) if rows else 1

    header_y = y + h - 0.082
    ax.text(x + 0.060, header_y, "Region / likely barrier", fontsize=7.6, color=PHILIPS_BLUE, weight="bold")
    ax.text(x + w * 0.57, header_y, value_header, fontsize=7.6, color=PHILIPS_BLUE, weight="bold", ha="center")
    ax.text(x + w * 0.74, header_y, "Capture", fontsize=7.6, color=PHILIPS_BLUE, weight="bold", ha="center")
    ax.text(x + w - 0.048, header_y, score_label, fontsize=7.6, color=PHILIPS_BLUE, weight="bold", ha="center")
    ax.plot([x + 0.016, x + w - 0.016], [header_y - 0.016, header_y - 0.016], color="#CBD5E1", linewidth=0.8)

    for idx, row in enumerate(rows):
        row_y = header_y - 0.050 - idx * ((h - 0.130) / 5)
        if idx > 0:
            ax.plot([x + 0.016, x + w - 0.016], [row_y + 0.032, row_y + 0.032], color="#E5EAF1", linewidth=0.7)

        icon_color = PHILIPS_BLUE if idx < 2 else "#1D4ED8"
        ax.add_patch(Circle((x + 0.032, row_y), 0.017, facecolor="#F2F7FF", edgecolor=icon_color, linewidth=1.0))
        ax.text(x + 0.032, row_y, str(idx + 1), fontsize=8, color=icon_color, weight="bold", ha="center", va="center")
        ax.text(x + 0.060, row_y + 0.011, clean_label(row["label"], 26), fontsize=8.1, color=DARK_BLUE, weight="bold", va="center")
        ax.text(x + 0.060, row_y - 0.012, row.get("barrier", "Referral pathway friction"), fontsize=7.0, color=DARK_TEXT, va="center")
        ax.text(x + w * 0.57, row_y, format_large(row["value"], value_label), fontsize=9.3, color=PHILIPS_BLUE, weight="bold", ha="center", va="center")
        capture = row.get("capture", 0)
        ax.text(x + w * 0.74, row_y, f"{capture:.0f}%", fontsize=9.0, color=PHILIPS_BLUE, weight="bold", ha="center", va="center")

        score = row.get("score", _relative_score(row["value"], max_value))
        score_color = "#E60023" if score >= 86 else CORAL if score >= 75 else "#FF7A00"
        score_box = FancyBboxPatch(
            (x + w - 0.075, row_y - 0.017),
            0.052,
            0.034,
            boxstyle="round,pad=0.003,rounding_size=0.007",
            linewidth=0,
            facecolor=score_color,
        )
        ax.add_patch(score_box)
        ax.text(x + w - 0.049, row_y, str(score), fontsize=12, color=WHITE, weight="bold", ha="center", va="center")


def draw_priority_strip(ax, items, x=0.020, y=0.040, w=0.960, h=0.080, label="STRATEGIC PRIORITIES"):
    draw_panel(ax, x, y, w, h)
    label_w = 0.115
    ax.add_patch(Rectangle((x, y), label_w, h, facecolor=DARK_BLUE, linewidth=0))
    ax.text(x + label_w / 2, y + h / 2, wrap_text(label, 14), fontsize=8.4, color=WHITE, weight="bold", ha="center", va="center")

    item_w = (w - label_w) / max(1, len(items))
    for idx, item in enumerate(items):
        ix = x + label_w + idx * item_w
        if idx > 0:
            ax.plot([ix, ix], [y + 0.014, y + h - 0.014], color="#BCD0EA", linewidth=0.8)
        draw_icon_circle(ax, ix + 0.032, y + h / 2, str(idx + 1), color=PHILIPS_BLUE, radius=0.022)
        ax.text(ix + 0.062, y + h - 0.024, item["title"].upper(), fontsize=7.6, color=PHILIPS_BLUE, weight="bold", va="top")
        ax.text(ix + 0.062, y + h - 0.044, wrap_text(item["body"], 27), fontsize=6.6, color=DARK_TEXT, va="top", linespacing=1.12)


def dataframe_rows(df, label_col, value_col, max_rows=5, value_label="Volume", barrier_prefix=None):
    if df is None or df.empty:
        return []

    top = df.head(max_rows).copy()
    max_value = top[value_col].max() if value_col in top else 0
    rows = []
    for _, row in top.iterrows():
        value = float(row.get(value_col, 0) or 0)
        share = float(row.get("Share", 0) or row.get("ZIP Share", 0) or 0)
        capture = max(8, min(48, 42 - share))
        rows.append(
            {
                "label": row.get(label_col, "Unknown"),
                "value": value,
                "share": share,
                "capture": capture,
                "score": _relative_score(value, max_value),
                "barrier": barrier_prefix or "Access and referral pathway friction",
                "value_label": value_label,
            }
        )
    return rows
