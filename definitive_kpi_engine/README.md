# Definitive KPI Engine

P# Market Intelligence App

A governed analytics engine for transforming Definitive Healthcare CSV exports into auditable account intelligence for cardiovascular, EP, and Lead Management strategy.

## Core Workflow

CSV Package
   ↓
Auditor Workbook
   ↓
KPI Workbook
   ↓
Deck / Map / PNG Outputs

The engine is built around one principle:


Project Structure
Market_Intel_App/
│
├── definitive_engine/        # Core audit + KPI engine
│   ├── intake/               # CSV loading and file scanning
│   ├── classification/       # File type detection by schema
│   ├── cleaning/             # Numeric cleanup and normalization
│   ├── auditor_workbook/     # Auditor Workbook generation
│   ├── validation/           # Quality checks and eligibility logic
│   ├── taxonomies/           # CPT / DRG mapping logic
│   └── metrics/              # KPI calculations
│
├── config/                   # Metric definitions and code crosswalks
├── accounts/                 # Account-specific input/output folders
├── visualizations/           # Heat maps, leakage maps, PNGs
├── deck_builder/             # Future PowerPoint output
├── archive_legacy/           # Old one-off scripts
└── outputs/                  # Shared exported workbooks/images
Main Outputs
1. Auditor Workbook

The source-of-truth workbook.

It captures:

Uploaded file inventory
File classification
Raw cleaned source tabs
Traceability columns
Data quality issues
KPI eligibility checks
Validation log

The Auditor Workbook does not create recommendations.

2. KPI Workbook

The validated metric workbook.

It calculates:

Total EP Charges
Device Implant Revenue
Device Implant Volume
Device Creation Revenue
Device Lifecycle Revenue
Lead Management Revenue
EP Leakage Revenue
Net Referral Balance
Geographic Catchment
EP Market Share
Market Rank
Device Population Creation Index

Each KPI must include a source, calculation rule, validation rule, and confidence rating.

3. Deck Outputs

Downstream outputs for maps, PNGs, and slides. These should read from the KPI Workbook or validated JSON exports, not raw CSVs.

Governance Rules
The Auditor Workbook is the single source of truth.
Raw CSV data is preserved before calculations.
Every KPI must be traceable to source data.
Every KPI receives a confidence rating.
Do not estimate missing or suppressed values.
Do not mix CPT, DRG, leakage, or market-share data without clear labeling.
Visuals and slides are downstream of validated metrics.
