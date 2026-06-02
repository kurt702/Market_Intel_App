import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from definitive_engine.ingestion import SOURCE_FILE_INVENTORY_COLUMNS, build_source_file_inventory


EXPECTED_COLUMNS = [
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


class SourceFileInventoryTests(unittest.TestCase):
    def test_source_file_inventory_has_exact_columns(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "Acme_Unknown_2025.csv"
            csv_path.write_text("Hospital,Favorite Color\nAcme,Blue\n", encoding="utf-8")

            inventory = build_source_file_inventory("Acme", temp_dir)

        self.assertEqual(SOURCE_FILE_INVENTORY_COLUMNS, EXPECTED_COLUMNS)
        self.assertEqual(list(inventory.columns), EXPECTED_COLUMNS)

    def test_source_file_inventory_contains_expected_values(self):
        columns = [
            "Definitive ID",
            "Hospital name",
            "City",
            "State",
            "Medicare pmts",
            "Medicare charges",
            "# of referrals",
            "% of referrals",
            "# of unique beneficiaries",
            "IDN name",
            "In-network referrals",
        ]
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "Rush_Referrals_To_2025.csv"
            csv_path.write_text(",".join(columns) + "\n" + ",".join(["value"] * len(columns)) + "\n", encoding="utf-8")

            inventory = build_source_file_inventory("Rush", temp_dir, reporting_year="2024")

        row = inventory.iloc[0]
        self.assertEqual(row["account_name"], "Rush")
        self.assertEqual(row["file_name"], "Rush_Referrals_To_2025.csv")
        self.assertTrue(str(row["file_path"]).endswith("Rush_Referrals_To_2025.csv"))
        self.assertEqual(row["row_count"], 1)
        self.assertEqual(row["column_count"], 11)
        self.assertEqual(row["filename_year"], "2025")
        self.assertEqual(row["reporting_year"], "2024")
        self.assertEqual(row["data_year_status"], "manual_override")
        self.assertEqual(row["data_year_notes"], "Reporting year manually set by user; filename year differs.")
        self.assertEqual(row["load_status"], "loaded")
        self.assertEqual(row["detected_file_type"], "referrals_to")


if __name__ == "__main__":
    unittest.main()
