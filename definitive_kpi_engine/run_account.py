from __future__ import annotations

import argparse
from pathlib import Path

from definitive_engine.calculations import build_calculation_outputs
from definitive_engine.config_loader import load_metric_definitions, load_taxonomies
from definitive_engine.final_outputs import write_final_outputs
from definitive_engine.ingestion import build_raw_tabs
from definitive_engine.raw_tabs import build_raw_tab_summary
from definitive_engine.taxonomy import build_taxonomy_outputs
from definitive_engine.validation import build_kpi_eligibility
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

    metric_definitions = load_metric_definitions(args.config)
    kpi_eligibility = build_kpi_eligibility(metric_definitions, raw_tabs, cpt_matches, drg_matches)

    print()
    print("KPI_Eligibility")
    if kpi_eligibility.empty:
        print("No KPI eligibility rows generated.")
    else:
        print(kpi_eligibility[["kpi_name", "eligibility_status", "confidence_status", "eligibility_notes"]].to_string(index=False))

    calculation_outputs = build_calculation_outputs(kpi_eligibility, raw_tabs, cpt_matches, drg_matches)
    kpi_calculation_detail = calculation_outputs["kpi_calculation_detail"]

    print()
    print("KPI_Calculation_Detail")
    if kpi_calculation_detail.empty:
        print("No KPI calculation detail rows generated.")
    else:
        print(kpi_calculation_detail[["kpi_name", "calculation_status", "calculated_value", "unit", "confidence_status", "validation_notes"]].to_string(index=False))

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
        kpi_eligibility=kpi_eligibility,
        calculation_outputs=calculation_outputs,
    )
    print()
    print(f"Auditor Workbook saved: {saved_path}")

    final_paths = write_final_outputs(
        output_folder=args.output,
        account_name=args.account,
        reporting_year=str(args.reporting_year or ""),
        calculation_outputs=calculation_outputs,
        source_workbook_path=saved_path,
    )
    print(f"KPI Workbook saved: {final_paths['kpi_workbook']}")
    print(f"KPI Summary CSV saved: {final_paths['kpi_summary_csv']}")
    print(f"KPI Summary JSON saved: {final_paths['kpi_summary_json']}")


if __name__ == "__main__":
    main()
