"""CSV discovery and source file inventory assembly."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .classification import classify_file, detect_year_from_filename
from .raw_tabs import add_numeric_companion_columns, build_raw_tab_dataframes


SOURCE_FILE_INVENTORY_COLUMNS = [
    "account_name",
    "file_name",
    "file_path",
    "row_count",
    "column_count",
    "column_names",
    "filename_year",
    "reporting_year",
    "data_year_status",
    "data_year_notes",
    "load_status",
    "detected_file_type",
    "classification_notes",
]


@dataclass(frozen=True)
class CsvFileMetadata:
    account_name: str
    file_name: str
    file_path: str
    row_count: int
    column_count: int
    column_names: list[str]
    filename_year: str | None
    reporting_year: str | None
    data_year_status: str
    data_year_notes: str
    load_status: str
    detected_file_type: str
    classification_notes: str

    def as_inventory_row(self) -> dict[str, object]:
        return {
            "account_name": self.account_name,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "column_names": "; ".join(self.column_names),
            "filename_year": self.filename_year,
            "reporting_year": self.reporting_year,
            "data_year_status": self.data_year_status,
            "data_year_notes": self.data_year_notes,
            "load_status": self.load_status,
            "detected_file_type": self.detected_file_type,
            "classification_notes": self.classification_notes,
        }


def discover_csv_files(input_folder: str | Path) -> list[Path]:
    """Discover CSV files in an input folder."""
    folder = Path(input_folder)
    if not folder.exists():
        raise FileNotFoundError(f"Input folder does not exist: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {folder}")
    return sorted(folder.rglob("*.csv"), key=lambda path: (path.name.lower(), str(path).lower()))


def read_csv_metadata(csv_path: str | Path, account_name: str, reporting_year: str | int | None = None) -> CsvFileMetadata:
    """Read CSV headers and row count without loading full source data."""
    path = Path(csv_path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                columns = next(reader)
            except StopIteration:
                columns = []
                row_count = 0
            else:
                row_count = sum(1 for row in reader if _is_non_empty_row(row))

        classification = classify_file(columns, file_name=path.name)
        load_status = "loaded"
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1", newline="") as handle:
            reader = csv.reader(handle)
            try:
                columns = next(reader)
            except StopIteration:
                columns = []
                row_count = 0
            else:
                row_count = sum(1 for row in reader if _is_non_empty_row(row))
        classification = classify_file(columns, file_name=path.name)
        load_status = "loaded"
    except Exception as exc:
        columns = []
        row_count = 0
        classification = classify_file(columns)
        load_status = f"failed: {exc}"

    filename_year = detect_year_from_filename(path.name) or None
    governed_reporting_year, data_year_status, data_year_notes = resolve_data_year(filename_year, reporting_year)
    return CsvFileMetadata(
        account_name=account_name,
        file_name=path.name,
        file_path=str(path.resolve()),
        row_count=row_count,
        column_count=len(columns),
        column_names=columns,
        filename_year=filename_year,
        reporting_year=governed_reporting_year,
        data_year_status=data_year_status,
        data_year_notes=data_year_notes,
        load_status=load_status,
        detected_file_type=classification.detected_file_type,
        classification_notes=classification.classification_notes,
    )


def build_source_file_inventory(account_name: str, input_folder: str | Path, reporting_year: str | int | None = None) -> pd.DataFrame:
    """Build the Phase 2 Source_File_Inventory table."""
    rows = [
        read_csv_metadata(csv_path, account_name, reporting_year=reporting_year).as_inventory_row()
        for csv_path in discover_csv_files(input_folder)
    ]
    return pd.DataFrame(rows, columns=SOURCE_FILE_INVENTORY_COLUMNS)


def load_csv_with_traceability(metadata: CsvFileMetadata, load_timestamp: str | None = None) -> pd.DataFrame:
    """Load a full CSV while preserving source columns and adding traceability."""
    timestamp = load_timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")
    df = _read_csv_preserve_columns(metadata.file_path)

    df["source_file"] = metadata.file_name
    df["source_row_number"] = range(2, len(df) + 2)
    df["detected_file_type"] = metadata.detected_file_type
    df["filename_year"] = metadata.filename_year
    df["reporting_year"] = metadata.reporting_year
    df["load_timestamp"] = timestamp
    return add_numeric_companion_columns(df)


def build_raw_tabs(
    account_name: str,
    input_folder: str | Path,
    load_timestamp: str | None = None,
    reporting_year: str | int | None = None,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Build Source_File_Inventory and raw tab dataframes for Phase 3."""
    metadata_records = [
        read_csv_metadata(csv_path, account_name, reporting_year=reporting_year)
        for csv_path in discover_csv_files(input_folder)
    ]
    inventory = pd.DataFrame([record.as_inventory_row() for record in metadata_records], columns=SOURCE_FILE_INVENTORY_COLUMNS)

    loaded_frames = []
    timestamp = load_timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")
    for metadata in metadata_records:
        if not metadata.load_status.startswith("loaded"):
            continue
        loaded_frames.append((metadata.detected_file_type, load_csv_with_traceability(metadata, load_timestamp=timestamp)))

    return inventory, build_raw_tab_dataframes(loaded_frames)


def _is_non_empty_row(row: list[str]) -> bool:
    return any(str(cell).strip() for cell in row)


def resolve_data_year(filename_year: str | None, reporting_year: str | int | None) -> tuple[str | None, str, str]:
    reporting_year_value = str(reporting_year) if reporting_year not in (None, "") else None
    if reporting_year_value and filename_year and reporting_year_value != filename_year:
        return (
            reporting_year_value,
            "manual_override",
            "Reporting year manually set by user; filename year differs.",
        )
    if reporting_year_value and filename_year == reporting_year_value:
        return reporting_year_value, "confirmed", "Reporting year confirmed by user."
    if reporting_year_value and not filename_year:
        return reporting_year_value, "confirmed", "Reporting year confirmed by user."
    if filename_year:
        return filename_year, "inferred_from_filename", "Reporting year inferred from filename; not independently confirmed."
    return None, "unknown", "No reporting year provided and no filename year detected."


def _read_csv_preserve_columns(file_path: str | Path) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(file_path, dtype=str, keep_default_na=False, encoding="latin-1")
