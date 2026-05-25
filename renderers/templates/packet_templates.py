from datetime import datetime

from renderers.design_system import (
    CORAL,
    CYAN,
    DARK_BLUE,
    DARK_TEXT,
    LIGHT_BLUE,
    MID_TEXT,
    PHILIPS_BLUE,
    SOFT_BLUE,
    WHITE,
)
from renderers.packet_renderer import (
    clean_label,
    create_board,
    dataframe_rows,
    draw_dual_flow_summary,
    draw_icon_circle,
    draw_intensity_field,
    draw_kpi_cards,
    draw_opportunity_table,
    draw_panel,
    draw_priority_strip,
    draw_ranked_list,
    format_large,
    save_board,
)


PRIORITIES = [
    {
        "title": "Identify & Triage Early",
        "body": "Focus outreach on high-signal ZIPs and accounts before leakage hardens.",
    },
    {
        "title": "Capture & Convert",
        "body": "Strengthen referral relationships where outbound movement is concentrated.",
    },
    {
        "title": "Standardize Pathways",
        "body": "Reduce pathway friction with repeatable intake and follow-up workflows.",
    },
    {
        "title": "Grow Volume & Value",
        "body": "Translate retained referrals into service-line growth and margin capture.",
    },
    {
        "title": "Improve Outcomes",
        "body": "Keep care local, improve continuity, and reduce avoidable leakage.",
    },
]


def _source_footer(ax, text):
    ax.text(0.020, 0.016, text, fontsize=7.4, color=MID_TEXT, va="bottom")
    ax.text(
        0.980,
        0.016,
        "Market Intelligence Executive Packet",
        fontsize=7.4,
        color=CORAL,
        weight="bold",
        ha="right",
        va="bottom",
    )


def _share_value(row):
    try:
        return float(row.get("Share", 0) or row.get("ZIP Share", 0) or 0)
    except Exception:
        return 0


def _leakage_rows(results, max_rows=5):
    return dataframe_rows(
        results.get("top_destinations_df"),
        "Destination",
        "Leakage Value",
        max_rows=max_rows,
        value_label=results.get("value_label", "Charges"),
        barrier_prefix="Referral retention and competitor capture risk",
    )


def _zip_rows(results, max_rows=5):
    return dataframe_rows(
        results.get("map_df"),
        "ZIP",
        "Value",
        max_rows=max_rows,
        value_label=results.get("value_label", "Volume"),
        barrier_prefix="Geographic vulnerability and access friction",
    )


def _referral_rows(results, max_rows=5, external_only=False):
    df = results.get("top_referrals_df")

    if df is None or df.empty:
        return []

    working = df.copy()

    if external_only:
        external = working[working["Pathway Type"] == "External"].copy()

        if not external.empty:
            working = external

    working["Pathway"] = (
        working["Origin"].astype(str).apply(lambda value: clean_label(value, 18))
        + " to "
        + working["Destination"].astype(str).apply(lambda value: clean_label(value, 20))
    )

    return dataframe_rows(
        working,
        "Pathway",
        "Value",
        max_rows=max_rows,
        value_label=results.get("value_label", "Volume"),
        barrier_prefix="Relationship, access, and pathway friction",
    )


def _overlay_rows(results, max_rows=5):
    return dataframe_rows(
        results.get("overlay_df"),
        "ZIP",
        "Estimated Leakage Value",
        max_rows=max_rows,
        value_label="Charges",
        barrier_prefix="ZIP-level leakage vulnerability",
    )


def _kpi_icon_cards_for_leakage(results):
    value_label = results.get("value_label", "Charges")
    return [
        {
            "icon": "P",
            "value": clean_label(results.get("top_destination", "N/A"), 16),
            "label": "Top leakage destination",
        },
        {
            "icon": "$" if value_label == "Charges" else "#",
            "value": format_large(results.get("total_leakage", 0), value_label),
            "label": f"Total leakage {value_label.lower()}",
        },
        {
            "icon": "%",
            "value": f"{results.get('top_share', 0):.1f}",
            "label": "Top destination share",
        },
        {
            "icon": "T",
            "value": clean_label(results.get("concentration", "N/A"), 13),
            "label": "Leakage concentration",
        },
    ]


def _draw_strategy_callout(ax, title, body):
    draw_panel(ax, 0.020, 0.132, 0.960, 0.052, title=title)
    draw_icon_circle(ax, 0.053, 0.158, "!", color=PHILIPS_BLUE, radius=0.020)
    ax.text(
        0.083,
        0.158,
        body,
        fontsize=9.6,
        color=DARK_BLUE,
        weight="bold",
        va="center",
    )


def render_cover_packet(packet_context, output_path):
    market_name = packet_context.get("market_name", "Selected Market")
    generated_at = packet_context.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    dataset_count = packet_context.get("dataset_count", 0)
    png_count = packet_context.get("png_count", 0)
    layers = packet_context.get("layers", [])

    fig, ax = create_board(
        "Market Intelligence Executive Packet",
        "Referral retention, pathway friction, service-line growth, and geographic vulnerability intelligence",
        kicker=clean_label(market_name, 72),
    )

    draw_kpi_cards(
        ax,
        [
            {"icon": "D", "value": generated_at.split(" ")[0], "label": "Date generated"},
            {"icon": "#", "value": str(dataset_count), "label": "Uploaded CSV datasets"},
            {"icon": "P", "value": str(png_count), "label": "PowerPoint-ready PNGs"},
            {"icon": "S", "value": "Local", "label": "Deterministic analytics"},
        ],
        x=0.505,
        y=0.852,
        w=0.108,
    )

    draw_panel(ax, 0.020, 0.215, 0.455, 0.575, title="Executive Packet Contents", subtitle="Generated intelligence layers")
    y = 0.715
    for idx, layer in enumerate(layers[:5]):
        color = PHILIPS_BLUE if layer.get("status") == "Generated" else CORAL
        draw_icon_circle(ax, 0.060, y, str(idx + 1), color=color, radius=0.020)
        ax.text(0.090, y + 0.012, layer.get("label", "Layer"), fontsize=12, color=DARK_BLUE, weight="bold", va="center")
        ax.text(
            0.090,
            y - 0.014,
            clean_label(layer.get("status", layer.get("reason", "")), 54),
            fontsize=8.8,
            color=DARK_TEXT,
            va="center",
        )
        y -= 0.083

    draw_panel(ax, 0.505, 0.215, 0.475, 0.575, title="How to Use This Packet", subtitle="Boardroom readout sequence")
    steps = [
        ("1", "Quantify leakage economics and referral retention exposure."),
        ("2", "Locate demand concentration and geographic vulnerability."),
        ("3", "Identify pathway friction and operational conversion opportunities."),
        ("4", "Prioritize outreach, access strategy, and service-line growth actions."),
    ]
    y = 0.705
    for number, body in steps:
        draw_icon_circle(ax, 0.545, y, number, color=DARK_BLUE, radius=0.021)
        ax.text(0.580, y, body, fontsize=10.8, color=DARK_TEXT, va="center")
        y -= 0.092

    _draw_strategy_callout(
        ax,
        "EXECUTIVE USE CASE",
        "Use this packet to align CFO, COO, and service-line leaders around the highest-signal opportunities for market capture and referral retention.",
    )
    draw_priority_strip(ax, PRIORITIES)
    _source_footer(ax, "Source: Uploaded Definitive Healthcare CSV exports | Generated locally using deterministic Python analytics")
    return save_board(fig, output_path)


def render_leakage_packet(results, output_path):
    value_label = results.get("value_label", "Charges")
    leakage_rows = _leakage_rows(results, max_rows=5)
    top_df = results.get("top_destinations_df")
    top_rows = _leakage_rows(results, max_rows=8)

    fig, ax = create_board(
        "Leakage Intelligence Landscape",
        "Where is addressable case value leaving the network, and which destinations should retention strategy prioritize?",
        kicker="Executive Leakage Summary",
    )
    draw_kpi_cards(ax, _kpi_icon_cards_for_leakage(results))

    draw_ranked_list(
        ax,
        top_rows,
        0.020,
        0.305,
        0.455,
        0.475,
        "Dominant Leakage Destinations",
        "Ranked by selected leakage metric from uploaded CSV",
        color=PHILIPS_BLUE,
        value_label=value_label,
        max_rows=8,
    )

    draw_opportunity_table(
        ax,
        leakage_rows,
        0.505,
        0.445,
        0.475,
        0.335,
        "Top Retention Opportunity Zones",
        "High leakage burden, low assumed capture priority",
        "Leakage",
        value_label,
        score_label="Priority",
    )

    draw_panel(ax, 0.505, 0.305, 0.475, 0.110, title="Strategic Interpretation")
    ax.text(
        0.525,
        0.372,
        clean_label(results.get("top_destination", "N/A"), 55),
        fontsize=13,
        color=DARK_BLUE,
        weight="bold",
        va="center",
    )
    ax.text(
        0.525,
        0.340,
        (
            f"Top destination share is {results.get('top_share', 0):.1f}%; "
            f"top five destinations represent {results.get('top_5_share', 0):.1f}%."
        ),
        fontsize=9.4,
        color=DARK_TEXT,
        va="center",
    )

    _draw_strategy_callout(
        ax,
        "WHAT THIS MEANS",
        "Prioritize referral retention against the highest-value destinations before broad outreach dilutes operational focus.",
    )
    draw_priority_strip(ax, PRIORITIES)
    _source_footer(ax, f"Source: Uploaded leakage CSV | Destination/value logic: {results.get('destination_column')} + {results.get('charges_column') or results.get('volume_column')}")
    return save_board(fig, output_path)


def render_heatmap_packet(results, output_path):
    value_label = results.get("value_label", "Volume")
    zip_rows = _zip_rows(results, max_rows=5)
    heat_rows = [
        {"label": row.get("ZIP"), "value": row.get("Value", 0)}
        for _, row in results.get("map_df").head(80).iterrows()
    ]

    fig, ax = create_board(
        "ZIP Geography Referral Landscape",
        "Which patient-origin geographies define core demand, secondary reach, and geographic vulnerability?",
        kicker="Patient Origin Heat Intelligence",
    )
    draw_kpi_cards(
        ax,
        [
            {"icon": "Z", "value": results.get("top_zip", "N/A"), "label": "Top patient-origin ZIP"},
            {"icon": "#", "value": format_large(results.get("total_value", 0), value_label), "label": f"Total {value_label.lower()}"},
            {"icon": "%", "value": f"{results.get('top_share', 0):.1f}", "label": "Top ZIP share"},
            {"icon": "T", "value": clean_label(results.get("concentration", "N/A"), 13), "label": "Geographic concentration"},
        ],
    )

    draw_intensity_field(
        ax,
        heat_rows,
        0.020,
        0.200,
        0.455,
        0.580,
        "Referral ZIP Code Heat Map",
        "Patient-origin demand intensity by ZIP code",
        center_label=f"Top ZIP {results.get('top_zip', 'N/A')}",
        value_label=value_label,
    )

    draw_opportunity_table(
        ax,
        zip_rows,
        0.505,
        0.385,
        0.475,
        0.395,
        "Geographic Opportunity Zones",
        "High demand ZIPs with operational capture priority",
        value_label,
        value_label,
        score_label="Index",
    )

    draw_panel(ax, 0.505, 0.200, 0.475, 0.150, title="Market Tier Interpretation")
    ax.text(0.530, 0.296, f"Core market share: {results.get('core_market_share', 0):.1f}%", fontsize=10.5, color=DARK_BLUE, weight="bold")
    ax.text(0.530, 0.265, f"Secondary market share: {results.get('secondary_market_share', 0):.1f}%", fontsize=10.0, color=PHILIPS_BLUE)
    ax.text(0.530, 0.235, f"Peripheral plus low-presence share: {results.get('peripheral_market_share', 0) + results.get('low_presence_share', 0):.1f}%", fontsize=10.0, color=DARK_TEXT)

    _draw_strategy_callout(
        ax,
        "WHAT THIS MEANS",
        "Use high-intensity ZIPs to focus access strategy, physician outreach, and market capture resources.",
    )
    draw_priority_strip(ax, PRIORITIES)
    _source_footer(ax, f"Source: Uploaded ZIP CSV | ZIP/value logic: {results.get('zip_column')} + {results.get('value_column')}")
    return save_board(fig, output_path)


def render_referral_packet(results, output_path):
    value_label = results.get("value_label", "Volume")
    top_rows = _referral_rows(results, max_rows=5)
    external_rows = _referral_rows(results, max_rows=5, external_only=True)

    fig, ax = create_board(
        "Referral Pathway Landscape",
        "Which directional referral lanes reveal pathway friction, retention risk, and conversion opportunity?",
        kicker="Referral Flow Intelligence",
    )
    draw_kpi_cards(
        ax,
        [
            {"icon": "P", "value": clean_label(results.get("top_origin", "N/A"), 14), "label": "Top pathway origin"},
            {"icon": "#", "value": format_large(results.get("total_value", 0), value_label), "label": f"Total {value_label.lower()}"},
            {"icon": "%", "value": f"{results.get('external_share', 0):.1f}", "label": "External pathway share"},
            {"icon": "T", "value": clean_label(results.get("concentration", "N/A"), 13), "label": "Pathway concentration"},
        ],
    )

    draw_dual_flow_summary(
        ax,
        top_rows,
        external_rows,
        0.020,
        0.485,
        0.960,
        0.295,
        "Referral Flow Summary",
        "Top directional pathways",
        "External / friction pathways",
        value_label,
    )

    draw_opportunity_table(
        ax,
        top_rows,
        0.020,
        0.200,
        0.960,
        0.250,
        "Top Referral Conversion Opportunities",
        "Directional pathways ranked by observed movement",
        value_label,
        value_label,
        score_label="Index",
    )

    _draw_strategy_callout(
        ax,
        "WHAT THIS MEANS",
        "Concentrated pathways should become named account plans with access checks, referral follow-up, and relationship ownership.",
    )
    draw_priority_strip(ax, PRIORITIES)
    _source_footer(ax, f"Source: Uploaded referral CSV | Pathway logic: {results.get('origin_column')} to {results.get('destination_column')}")
    return save_board(fig, output_path)


def render_leakage_geography_packet(results, output_path):
    overlay_rows = _overlay_rows(results, max_rows=5)
    field_rows = [
        {"label": row.get("ZIP"), "value": row.get("Estimated Leakage Value", 0)}
        for _, row in results.get("overlay_df").head(80).iterrows()
    ]
    top_destination = results.get("top_destination", "Unknown")
    total_estimated = results.get("overlay_df")["Estimated Leakage Value"].sum()

    fig, ax = create_board(
        "Leakage Geography Landscape",
        "Where do high-demand ZIPs overlap with addressable leakage opportunity and geographic vulnerability?",
        kicker="Geographic Vulnerability Intelligence",
    )
    draw_kpi_cards(
        ax,
        [
            {"icon": "P", "value": clean_label(top_destination, 14), "label": "Primary leakage destination"},
            {"icon": "$", "value": format_large(total_estimated, "Charges"), "label": "ZIP-weighted opportunity"},
            {"icon": "Z", "value": clean_label(results.get("overlay_df").iloc[0]["ZIP"], 10), "label": "Highest vulnerability ZIP"},
            {"icon": "T", "value": format_large(results.get("top_leakage_value", 0), "Charges"), "label": "Top destination value"},
        ],
    )

    draw_intensity_field(
        ax,
        field_rows,
        0.020,
        0.200,
        0.455,
        0.580,
        "Estimated Leakage Opportunity by ZIP",
        "ZIP-weighted leakage exposure using the same top destination as leakage summary",
        center_label=clean_label(top_destination, 22),
        value_label="Charges",
        risk=True,
    )

    draw_opportunity_table(
        ax,
        overlay_rows,
        0.505,
        0.385,
        0.475,
        0.395,
        "Top Geographic Vulnerability Zones",
        "High ZIP volume weighted by primary leakage destination",
        "Est. Leakage",
        "Charges",
        score_label="Index",
    )

    draw_panel(ax, 0.505, 0.200, 0.475, 0.150, title="Strategic Interpretation")
    ax.text(
        0.530,
        0.302,
        clean_label(top_destination, 54),
        fontsize=12.5,
        color=DARK_BLUE,
        weight="bold",
    )
    ax.text(
        0.530,
        0.263,
        "Primary capture signal is inherited from the leakage summary engine.",
        fontsize=9.2,
        color=DARK_TEXT,
    )
    ax.text(
        0.530,
        0.232,
        "This prevents generic facility columns from overriding true leakage destination logic.",
        fontsize=8.8,
        color=MID_TEXT,
    )

    _draw_strategy_callout(
        ax,
        "WHAT THIS MEANS",
        "Treat the top ZIPs as geographic vulnerability zones for access redesign, referral retention, and targeted market capture.",
    )
    draw_priority_strip(ax, PRIORITIES)
    _source_footer(ax, f"Source: Uploaded ZIP + leakage CSVs | Overlay logic: {results.get('destination_column')} + {results.get('value_column')}")
    return save_board(fig, output_path)
