# Definitive KPI Engine Quality Audit Report

- Executive status: PASS WITH WARNINGS
- Audit date/time: 2026-06-02T20:22:56+00:00
- Pass checks: 37
- Warnings: 7
- Failures: 0

## Repo structure findings

- Repository root contains only approved entries
- Rush input folder exists
- Rush output folder exists
- Demo inputs are under samples/demo_inputs
- Demo outputs are under samples/demo_outputs
- No root-level demo folders
- Production Rush auditor workbook exists
- No root-level workbook files
- Auditor workbook contains expected sheets
- Auditor workbook contains no KPI/final summary sheets
- No KPI workbook, KPI summaries, JSON, or PowerPoint artifacts found
- Archived demo auditor workbooks remain under samples/demo_outputs: samples\demo_outputs\_phase4_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_phase5_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_taxonomy_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_year_demo_output\auditor_workbook.xlsx

## Config findings

- Config exists: cpt_ep_taxonomy.csv
- Config exists: drg_ep_taxonomy.csv
- Config exists: expected_file_manifest.csv
- Config exists: metric_definitions.csv
- Config exists: validation_rules.csv
- CPT taxonomy contains all required seed rows
- DRG taxonomy contains all required seed rows
- CPT taxonomy is not template-only
- DRG taxonomy is not template-only

## Rush input findings

- Rush input folder exists
- Rush input files match expected set
- Rush input has no duplicate filenames

## Classification findings

- Rush file classification matches expected map
- No Rush files classified as unknown

## Year governance findings

- Source_File_Inventory includes year governance columns
- Year governance correct for 2024 and 2025 filenames

## Raw tab findings

- Raw_Tab_Summary row counts match expected Rush run

## Traceability findings

- Traceability columns are present and populated except governed filename_year nulls
- Raw_Inpatient_Leakage: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Inpatient_MarketShare: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_ZIP_Origination: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Outpatient_Leakage: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Referrals_From: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Referrals_To: filename_year is null where filename has no embedded year; reporting_year is populated.

## Numeric cleaning findings

- Numeric originals and __num companion columns are present
- Numeric cleaning examples behave correctly

## Workbook findings

- Auditor workbook contains expected sheets
- Auditor workbook contains no KPI/final summary sheets

## Taxonomy findings

- Config exists: cpt_ep_taxonomy.csv
- Config exists: drg_ep_taxonomy.csv
- CPT taxonomy contains all required seed rows
- DRG taxonomy contains all required seed rows
- CPT taxonomy is not template-only
- DRG taxonomy is not template-only
- CPT Raw_MedicalClaims_CPT has nonzero matched rows
- DRG Raw_Inpatient_DRG has nonzero matched rows
- DRG Raw_Inpatient_Leakage has nonzero matched rows
- DRG Raw_Inpatient_MarketShare has nonzero matched rows
- DRG Raw_MedicalClaims_DRG has nonzero matched rows
- Matched CPT rows include configured CPTs when present
- Matched DRG rows include configured DRGs when present
- Configured CPTs matched in Rush data: 33207, 33208, 33225, 33227, 33228, 33229, 33235, 33241, 33244, 33249, 33262, 33263, 33264
- Configured DRGs matched in Rush data: 242, 243, 244, 245, 247, 248, 249, 250, 251

## Test findings

- Tests run: 40
- Passed: 40
- Failed: 0
- Skipped: 0
- Result: OK

## Output hygiene findings

- No root-level workbook files
- No KPI workbook, KPI summaries, JSON, or PowerPoint artifacts found
- Archived demo auditor workbooks remain under samples/demo_outputs: samples\demo_outputs\_phase4_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_phase5_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_taxonomy_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_year_demo_output\auditor_workbook.xlsx

## Open issues

- Archived demo auditor workbooks remain under samples/demo_outputs: samples\demo_outputs\_phase4_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_phase5_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_taxonomy_demo_output\auditor_workbook.xlsx, samples\demo_outputs\_year_demo_output\auditor_workbook.xlsx
- Raw_Inpatient_Leakage: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Inpatient_MarketShare: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_ZIP_Origination: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Outpatient_Leakage: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Referrals_From: filename_year is null where filename has no embedded year; reporting_year is populated.
- Raw_Referrals_To: filename_year is null where filename has no embedded year; reporting_year is populated.

## Recommended fixes before Phase 6

- Decide whether archived demo auditor workbooks under samples/demo_outputs should be retained or purged before packaging.
- Accept filename_year nulls for Rush files without embedded filename years, or add a separate source-period metadata control.
