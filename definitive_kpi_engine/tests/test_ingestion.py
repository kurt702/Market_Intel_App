import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from definitive_engine.ingestion import discover_csv_files, read_csv_metadata, resolve_data_year


class IngestionTests(unittest.TestCase):
    def test_discovers_csv_files_recursively(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()
            (root / "one.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (nested / "two.csv").write_text("a,b\n3,4\n", encoding="utf-8")
            (root / "ignore.txt").write_text("not a csv\n", encoding="utf-8")

            discovered = discover_csv_files(root)

        self.assertEqual([path.name for path in discovered], ["one.csv", "two.csv"])

    def test_reads_headers_row_count_and_classification(self):
        columns = [
            "Rendering Provider",
            "Definitive ID",
            "Rendering Provider Type",
            "HCPCS/CPT Code",
            "HCPCS/CPT Description",
            "# Actual Procedures",
            "% Actual Procedures",
            "Actual Charges",
            "% Actual Charges",
            "Charge/Procedure (Actual)",
        ]
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "Rush_CPT_2025.csv"
            csv_path.write_text(",".join(columns) + "\n" + ",".join(["value"] * len(columns)) + "\n\n", encoding="utf-8")

            metadata = read_csv_metadata(csv_path, "Rush")

        self.assertEqual(metadata.file_name, "Rush_CPT_2025.csv")
        self.assertEqual(metadata.row_count, 1)
        self.assertEqual(metadata.column_count, 10)
        self.assertEqual(metadata.column_names, columns)
        self.assertEqual(metadata.filename_year, "2025")
        self.assertEqual(metadata.reporting_year, "2025")
        self.assertEqual(metadata.data_year_status, "inferred_from_filename")
        self.assertEqual(metadata.load_status, "loaded")
        self.assertEqual(metadata.detected_file_type, "medicalclaims_cpt_breakdown")

    def test_manual_override_when_reporting_year_differs_from_filename_year(self):
        reporting_year, status, notes = resolve_data_year("2025", "2024")
        self.assertEqual(reporting_year, "2024")
        self.assertEqual(status, "manual_override")
        self.assertEqual(notes, "Reporting year manually set by user; filename year differs.")

    def test_confirmed_when_reporting_year_matches_filename_year(self):
        reporting_year, status, notes = resolve_data_year("2024", "2024")
        self.assertEqual(reporting_year, "2024")
        self.assertEqual(status, "confirmed")
        self.assertEqual(notes, "Reporting year confirmed by user.")

    def test_inferred_from_filename_when_no_reporting_year_passed(self):
        reporting_year, status, notes = resolve_data_year("2025", None)
        self.assertEqual(reporting_year, "2025")
        self.assertEqual(status, "inferred_from_filename")
        self.assertEqual(notes, "Reporting year inferred from filename; not independently confirmed.")

    def test_unknown_when_no_filename_or_reporting_year(self):
        reporting_year, status, notes = resolve_data_year(None, None)
        self.assertIsNone(reporting_year)
        self.assertEqual(status, "unknown")
        self.assertEqual(notes, "No reporting year provided and no filename year detected.")


if __name__ == "__main__":
    unittest.main()
