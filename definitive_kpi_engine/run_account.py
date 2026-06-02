from __future__ import annotations

import argparse
from pathlib import Path

from definitive_engine.config_loader import load_taxonomies
from definitive_engine.ingestion import build_raw_tabs
from definitive_engine.raw_tabs import build_raw_tab_summary
from definitive_engine.taxonomy import build_taxonomy_outputs
from definitive_engine.workbooks import write_auditor_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Auditor Workbook generation runner.")
    parser.add_argument("--account", required=True, help="Account name for the source file inventory.")
    parser.add_argument("--input", required=True, help="Folder containing Definitive Healthcare CSV files.")
    parser.add_argument("--output", required=True, help="Reserved output folder argument for later phases.")
    parser.add_argument("--reporting-year", default=None, help="Optional governed reporting year to apply to all loaded files.")
    parser.add_argument("--config", default="config", help="Folder containing CPT and DRG taxonomy config CSVs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    inventory, raw_tabs = build_raw_tabs(account_name=args.account, input_folder=args.input, reporting_year=args.reporting_year)

    print("Source_File_Inventory")
    if inventory.empty:
        print("No CSV files discovered.")
    else:
        print(inventory.to_string(index=False))

    print()
    print("Raw_Tab_Summary")
    raw_tab_summary = build_raw_tab_summary(raw_tabs)
    if raw_tab_summary.empty:
        print("No raw tabs loaded.")
    else:
        print(raw_tab_summary.to_string(index=False))

    cpt_taxonomy, drg_taxonomy = load_taxonomies(args.config)
    cpt_matches, drg_matches, taxonomy_match_summary = build_taxonomy_outputs(raw_tabs, cpt_taxonomy, drg_taxonomy)

    print()
    print("Taxonomy_Match_Summary")
    if taxonomy_match_summary.empty:
        print("No taxonomy-eligible raw tabs loaded.")
    else:
        print(taxonomy_match_summary.to_string(index=False))

    workbook_path = Path(args.output) / "auditor_workbook.xlsx"
    saved_path = write_auditor_workbook(
        output_path=workbook_path,
        account_name=args.account,
        source_file_inventory=inventory,
        raw_tab_dataframes=raw_tabs,
        raw_tab_summary=raw_tab_summary,
        cpt_taxonomy_matches=cpt_matches,
        drg_taxonomy_matches=drg_matches,
        taxonomy_match_summary=taxonomy_match_summary,
    )
    print()
    print(f"Auditor Workbook saved: {saved_path}")


if __name__ == "__main__":
    main()
