from datetime import datetime
from pathlib import Path

from analytics.heatmap_engine import analyze_heatmap_geography
from analytics.leakage_engine import (
    analyze_leakage,
    format_money,
    format_number,
)
from analytics.leakage_geography_engine import analyze_leakage_geography
from analytics.referral_engine import analyze_referrals
from renderers.templates.packet_templates import (
    render_cover_packet,
    render_heatmap_packet,
    render_leakage_geography_packet,
    render_leakage_packet,
    render_referral_packet,
)
from utils.export_utils import build_packet_zip


PACKET_OUTPUTS = {
    "cover": "01_cover.png",
    "leakage_summary": "02_leakage_summary.png",
    "zip_geography": "03_zip_geography.png",
    "referral_pathways": "04_referral_pathways.png",
    "leakage_geography": "05_leakage_geography.png",
}

LAYER_LABELS = {
    "leakage_summary": "Leakage Summary",
    "zip_geography": "ZIP Geography",
    "referral_pathways": "Referral Pathways",
    "leakage_geography": "Leakage Geography",
}


def _packet_dirs(app_root):
    output_root = Path(app_root) / "outputs"
    png_dir = output_root / "png"
    packet_dir = output_root / "packets"

    png_dir.mkdir(parents=True, exist_ok=True)
    packet_dir.mkdir(parents=True, exist_ok=True)

    return png_dir, packet_dir


def _first_available(*dataframes):
    for df in dataframes:
        if df is not None and not df.empty:
            return df
    return None


def _add_result(packet, key, label, path=None, error=None):
    if path:
        packet["generated"].append(
            {
                "key": key,
                "label": label,
                "path": str(path),
            }
        )
    else:
        packet["skipped"].append(
            {
                "key": key,
                "label": label,
                "reason": error or "Required dataset was not available.",
            }
        )


def _clean_label(value):
    value = str(value).strip()
    if not value or value.lower() in {"nan", "none", "unknown", "not available"}:
        return None
    return value


def _first_market_value(df):
    if df is None or df.empty:
        return None

    preferred_keywords = [
        "market",
        "account",
        "health system",
        "organization",
        "parent",
        "hospital name",
        "hospital",
        "facility",
    ]
    skipped_keywords = [
        "destination",
        "competitor",
        "receiving",
        "leakage",
    ]

    for keyword in preferred_keywords:
        for col in df.columns:
            col_lower = str(col).lower()

            if keyword not in col_lower:
                continue

            if any(skip in col_lower for skip in skipped_keywords):
                continue

            values = (
                df[col]
                .dropna()
                .astype(str)
                .str.strip()
            )
            values = values[
                ~values.str.lower().isin(["", "nan", "none", "unknown"])
            ]

            if not values.empty:
                return _clean_label(values.value_counts().index[0])

    return None


def _fallback_name_from_file(file_name):
    if not file_name:
        return None

    stem = Path(file_name).stem
    cleaned = (
        stem.replace("_", " ")
        .replace("-", " ")
        .replace("definitive", "")
        .replace("Definitive", "")
        .strip()
    )
    return _clean_label(cleaned.title())


def infer_market_name(routed_datasets, fallback_df=None):
    routed_datasets = routed_datasets or {}

    for df_key in ["referral_df", "zip_df", "leakage_df"]:
        market_name = _first_market_value(routed_datasets.get(df_key))
        if market_name:
            return market_name

    market_name = _first_market_value(fallback_df)
    if market_name:
        return market_name

    for file_key in ["referral_file", "zip_file", "leakage_file"]:
        market_name = _fallback_name_from_file(routed_datasets.get(file_key))
        if market_name:
            return market_name

    return "Selected Market"


def _layer_context(packet):
    generated_by_key = {
        item["key"]: item
        for item in packet["generated"]
    }
    skipped_by_key = {
        item["key"]: item
        for item in packet["skipped"]
    }

    layers = []

    for key, label in LAYER_LABELS.items():
        if key in generated_by_key:
            layers.append(
                {
                    "key": key,
                    "label": label,
                    "status": "Generated",
                    "reason": "Included in packet",
                }
            )
        else:
            reason = skipped_by_key.get(key, {}).get(
                "reason",
                "Required source data was not available.",
            )
            layers.append(
                {
                    "key": key,
                    "label": label,
                    "status": "Unavailable",
                    "reason": reason,
                }
            )

    return layers


def build_executive_summary(packet):
    bullets = []

    leakage = packet["analytics"].get("leakage")
    heatmap = packet["analytics"].get("heatmap")
    referral = packet["analytics"].get("referral")
    leakage_geo = packet["analytics"].get("leakage_geography")

    if leakage and leakage.get("success"):
        value = (
            format_money(leakage["total_leakage"])
            if leakage["value_label"] == "Charges"
            else format_number(leakage["total_leakage"])
        )
        bullets.append(
            f"- Referral retention opportunity is measurable: identified leakage totals {value}, led by {leakage['top_destination']}."
        )
        bullets.append(
            f"- Leakage concentration is {leakage['concentration'].lower()}; the top destination represents {leakage['top_share']:.1f}% of outflow and should anchor near-term service-line growth and market capture planning."
        )

    if heatmap and heatmap.get("success"):
        bullets.append(
            f"- ZIP geography is led by {heatmap['top_zip']} with {heatmap['top_share']:.1f}% of analyzed {heatmap['value_label'].lower()}, giving leadership a focused access strategy footprint."
        )
        bullets.append(
            f"- Geographic concentration is {heatmap['concentration'].lower()}, highlighting where geographic vulnerability, access friction, or uneven referral reach may be limiting capture."
        )

    if referral and referral.get("success"):
        bullets.append(
            f"- The leading referral pathway is {referral['top_origin']} to {referral['top_destination']}, representing {referral['top_share']:.1f}% of observed movement and a practical relationship-management target."
        )
        bullets.append(
            f"- External pathways account for {referral['external_share']:.1f}% of activity, signaling pathway friction and operational opportunity for conversion, scheduling, and retention workflows."
        )

    if leakage_geo and leakage_geo.get("success"):
        bullets.append(
            f"- Leakage geography aligns patient-origin demand with {leakage_geo['top_destination']} as the primary external capture signal, clarifying where geographic vulnerability should be converted into action."
        )

    missing_layers = [
        item["label"]
        for item in packet["skipped"]
        if item["key"] in LAYER_LABELS
    ]

    if missing_layers:
        bullets.append(
            f"- Missing layer note: {', '.join(missing_layers)} was not generated because the required routed dataset was unavailable or unreadable."
        )

    if len(bullets) < 5:
        fallback_bullets = [
            "- Use this packet as a CFO/COO triage view for referral retention, service-line growth, access strategy, and operational opportunity.",
            "- Highest-signal segments should be translated into account outreach, scheduling access checks, referral workflow redesign, and market capture goals.",
            "- Additional claims extracts can extend this packet into a fuller service-line growth roadmap with quantified pathway friction and capture targets.",
        ]

        for bullet in fallback_bullets:
            if len(bullets) >= 5:
                break
            bullets.append(bullet)

    return bullets[:7]


def generate_executive_packet(
    routed_datasets,
    app_root,
    fallback_df=None,
):
    png_dir, packet_dir = _packet_dirs(app_root)

    packet = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "generated": [],
        "skipped": [],
        "analytics": {},
        "summary_path": None,
        "zip_path": None,
        "market_name": None,
    }

    routed_datasets = routed_datasets or {}
    packet["market_name"] = infer_market_name(
        routed_datasets,
        fallback_df=fallback_df,
    )

    dataset_count = len(routed_datasets.get("profiles", []))
    if dataset_count == 0 and fallback_df is not None and not fallback_df.empty:
        dataset_count = 1

    leakage_df = _first_available(
        routed_datasets.get("leakage_df"),
        fallback_df,
    )
    zip_df = _first_available(
        routed_datasets.get("zip_df"),
        fallback_df,
    )
    referral_df = routed_datasets.get("referral_df")

    if leakage_df is not None:
        leakage_results = analyze_leakage(leakage_df)
        packet["analytics"]["leakage"] = leakage_results

        if leakage_results["success"]:
            output_path = png_dir / PACKET_OUTPUTS["leakage_summary"]
            render_leakage_packet(leakage_results, output_path)
            _add_result(packet, "leakage_summary", "Leakage summary PNG", output_path)
        else:
            _add_result(packet, "leakage_summary", "Leakage summary PNG", error=leakage_results["error"])
    else:
        _add_result(packet, "leakage_summary", "Leakage summary PNG")

    if zip_df is not None:
        heatmap_results = analyze_heatmap_geography(zip_df)
        packet["analytics"]["heatmap"] = heatmap_results

        if heatmap_results["success"]:
            output_path = png_dir / PACKET_OUTPUTS["zip_geography"]
            render_heatmap_packet(heatmap_results, output_path)
            _add_result(packet, "zip_geography", "ZIP geography PNG", output_path)
        else:
            _add_result(packet, "zip_geography", "ZIP geography PNG", error=heatmap_results["error"])
    else:
        _add_result(packet, "zip_geography", "ZIP geography PNG")

    if referral_df is not None:
        referral_results = analyze_referrals(referral_df)
        packet["analytics"]["referral"] = referral_results

        if referral_results["success"]:
            output_path = png_dir / PACKET_OUTPUTS["referral_pathways"]
            render_referral_packet(referral_results, output_path)
            _add_result(packet, "referral_pathways", "Referral pathways PNG", output_path)
        else:
            _add_result(packet, "referral_pathways", "Referral pathways PNG", error=referral_results["error"])
    else:
        _add_result(
            packet,
            "referral_pathways",
            "Referral pathways PNG",
            error="Requires a routed referral dataset.",
        )

    routed_zip_df = routed_datasets.get("zip_df")
    routed_leakage_df = routed_datasets.get("leakage_df")

    if routed_zip_df is not None and routed_leakage_df is not None:
        leakage_geo_results = analyze_leakage_geography(
            leakage_df=routed_leakage_df,
            zip_df=routed_zip_df,
        )
        packet["analytics"]["leakage_geography"] = leakage_geo_results

        if leakage_geo_results["success"]:
            output_path = png_dir / PACKET_OUTPUTS["leakage_geography"]
            render_leakage_geography_packet(leakage_geo_results, output_path)
            _add_result(packet, "leakage_geography", "Leakage geography PNG", output_path)
        else:
            _add_result(packet, "leakage_geography", "Leakage geography PNG", error=leakage_geo_results["error"])
    else:
        _add_result(
            packet,
            "leakage_geography",
            "Leakage geography PNG",
            error="Requires both routed ZIP and leakage datasets.",
        )

    cover_path = png_dir / PACKET_OUTPUTS["cover"]
    render_cover_packet(
        {
            "market_name": packet["market_name"],
            "generated_at": packet["generated_at"],
            "dataset_count": dataset_count,
            "png_count": len(
                [
                    item
                    for item in packet["generated"]
                    if str(item.get("path", "")).lower().endswith(".png")
                ]
            ) + 1,
            "layers": _layer_context(packet),
        },
        cover_path,
    )
    packet["generated"].insert(
        0,
        {
            "key": "cover",
            "label": "Cover PNG",
            "path": str(cover_path),
        },
    )

    bullets = build_executive_summary(packet)
    summary_path = packet_dir / "executive_summary.txt"
    summary_text = "\n".join(bullets) + "\n"
    summary_path.write_text(summary_text, encoding="utf-8")

    packet["summary_path"] = str(summary_path)
    packet["summary_bullets"] = bullets

    _add_result(
        packet,
        "executive_summary",
        "Executive summary TXT",
        summary_path,
    )

    zip_path = packet_dir / "executive_packet.zip"
    packet_files = [
        item["path"]
        for item in packet["generated"]
        if Path(item["path"]).suffix.lower() in {".png", ".txt"}
    ]
    build_packet_zip(packet_files, zip_path)
    packet["zip_path"] = str(zip_path)

    return packet
