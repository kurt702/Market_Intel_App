import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from definitive_engine.ingestion import build_raw_tabs, read_csv_metadata, load_csv_with_traceability
from definitive_engine.raw_tabs import (
    add_numeric_companion_columns,
    clean_numeric_value,
    map_detected_file_type_to_raw_tab,
)


MEDICALCLAIMS_CPT_HEADER = [
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


class RawTabsTests(unittest.TestCase):
    def test_raw_tab_name_mapping(self):
        self.assertEqual(map_detected_file_type_to_raw_tab("medicalclaims_cpt_breakdown"), "Raw_MedicalClaims_CPT")
        self.assertEqual(map_detected_file_type_to_raw_tab("outpatient_procedure_breakdown"), "Raw_Outpatient_CPT")
        self.assertEqual(map_detected_file_type_to_raw_tab("medicalclaims_drg_breakdown"), "Raw_MedicalClaims_DRG")
        self.assertEqual(map_detected_file_type_to_raw_tab("inpatient_drg_breakdown"), "Raw_Inpatient_DRG")
        self.assertEqual(map_detected_file_type_to_raw_tab("inpatient_leakage"), "Raw_Inpatient_Leakage")
        self.assertEqual(map_detected_file_type_to_raw_tab("outpatient_hospital_leakage"), "Raw_Outpatient_Leakage")
        self.assertEqual(map_detected_file_type_to_raw_tab("inpatient_marketshare"), "Raw_Inpatient_MarketShare")
        self.assertEqual(map_detected_file_type_to_raw_tab("zip_origination"), "Raw_ZIP_Origination")
        self.assertEqual(map_detected_file_type_to_raw_tab("referrals_from"), "Raw_Referrals_From")
        self.assertEqual(map_detected_file_type_to_raw_tab("referrals_to"), "Raw_Referrals_To")
        self.assertEqual(map_detected_file_type_to_raw_tab("unknown"), "Raw_Unknown")

    def test_traceability_columns_are_added(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "Rush_CPT_2025.csv"
            csv_path.write_text(",".join(MEDICALCLAIMS_CPT_HEADER) + "\n" + ",".join(["value"] * 10) + "\n", encoding="utf-8")
            metadata = read_csv_metadata(csv_path, "Rush", reporting_year="2024")

            df = load_csv_with_traceability(metadata, load_timestamp="2026-06-02T00:00:00+00:00")

        self.assertIn("source_file", df.columns)
        self.assertIn("source_row_number", df.columns)
        self.assertIn("detected_file_type", df.columns)
        self.assertIn("filename_year", df.columns)
        self.assertIn("reporting_year", df.columns)
        self.assertIn("load_timestamp", df.columns)
        self.assertEqual(df.loc[0, "source_file"], "Rush_CPT_2025.csv")
        self.assertEqual(df.loc[0, "source_row_number"], 2)
        self.assertEqual(df.loc[0, "detected_file_type"], "medicalclaims_cpt_breakdown")
        self.assertEqual(df.loc[0, "filename_year"], "2025")
        self.assertEqual(df.loc[0, "reporting_year"], "2024")
        self.assertEqual(df.loc[0, "load_timestamp"], "2026-06-02T00:00:00+00:00")

    def test_numeric_cleaning_values(self):
        self.assertEqual(clean_numeric_value("$1,234.50"), 1234.50)
        self.assertEqual(clean_numeric_value("12.5%"), 12.5)
        self.assertEqual(clean_numeric_value("($500)"), -500)
        self.assertTrue(math.isnan(clean_numeric_value("")))

    def test_add_numeric_companion_columns_without_overwriting_original(self):
        df = pd.DataFrame({"Actual Charges": ["$1,234.50", "($500)", ""], "Name": ["A", "B", "C"]})
        result = add_numeric_companion_columns(df)
        self.assertIn("Actual Charges", result.columns)
        self.assertIn("Actual Charges__num", result.columns)
        self.assertNotIn("Name__num", result.columns)
        self.assertEqual(result.loc[0, "Actual Charges__num"], 1234.50)
        self.assertEqual(result.loc[1, "Actual Charges__num"], -500)
        self.assertTrue(math.isnan(result.loc[2, "Actual Charges__num"]))

    def test_multiple_files_same_type_concatenate_to_one_raw_tab(self):
        with TemporaryDirectory() as temp_dir:
            for index in [1, 2]:
                csv_path = Path(temp_dir) / f"Rush_CPT_2025_{index}.csv"
                csv_path.write_text(",".join(MEDICALCLAIMS_CPT_HEADER) + "\n" + ",".join(["value"] * 10) + "\n", encoding="utf-8")

            _, raw_tabs = build_raw_tabs("Rush", temp_dir, load_timestamp="2026-06-02T00:00:00+00:00")

        self.assertIn("Raw_MedicalClaims_CPT", raw_tabs)
        self.assertEqual(len(raw_tabs["Raw_MedicalClaims_CPT"]), 2)
        self.assertEqual(set(raw_tabs["Raw_MedicalClaims_CPT"]["source_file"]), {"Rush_CPT_2025_1.csv", "Rush_CPT_2025_2.csv"})


if __name__ == "__main__":
    unittest.main()
