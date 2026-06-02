# Definitive KPI Engine

Phase 1 scaffold for an auditable KPI engine for Definitive Healthcare CSV files.

This repository is intentionally not feature-complete yet. Phase 1 establishes the project structure, configuration templates, placeholder package modules, placeholder tests, and a runnable command-line entrypoint.

## Scope

Planned outputs:

- Auditor Workbook
- KPI Workbook
- KPI Summary CSV
- KPI Summary JSON

Out of scope:

- PowerPoint automation
- Slide deck generation
- Recommendations
- Opportunity scores
- Strategy narratives

## Setup

```powershell
cd "C:\Users\gries\OneDrive\Desktop\AI Workflows\Market_Intel_App\definitive_kpi_engine"
pip install -r requirements.txt
```

## Run CLI Scaffold

```powershell
python run_account.py --input-folder "C:\path\to\csvs" --output-folder "C:\path\to\outputs" --account-name "Example Account"
```

The Phase 1 CLI only prints the arguments it receives.

## Project Layout

- `config/`: template CSV configuration files
- `definitive_engine/`: placeholder Python package modules
- `tests/`: placeholder test files
- `run_account.py`: runnable CLI scaffold

## Next Phase

Phase 2 should implement CSV discovery and column-signature file classification, then populate `Source_File_Inventory`.
