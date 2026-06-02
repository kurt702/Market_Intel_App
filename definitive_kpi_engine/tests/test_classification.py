import unittest

from definitive_engine.classification import classify_file, detect_year_from_filename


INPATIENT_DRG_COLUMNS = [
    "DRG",
    "DRG Description",
    "Attending Physician NPI",
    "First Name",
    "Last Name",
    "Primary Specialty",
    "Primary Hospital Affiliation",
    "Medicare Total Pmts",
    "Medicare Avg Pmt/Claim",
    "Medicare Total Charges",
    "Medicare Charge/Claim",
    "Medicare Total # of Claims",
]

INPATIENT_LEAKAGE_COLUMNS = [
    "Hospital Name",
    "Base DRG Group",
    "Total Pmts",
    "Total Charges",
    "Total Claims",
    "Unique Patients",
    "Network",
    "Network Parent",
]

INPATIENT_MARKETSHARE_COLUMNS = [
    "DRG code",
    "Description",
    "Total pmts - this hospital",
    "Total pmts - patient universe",
    "% pmts at this hospital",
    "Total charges - this hospital",
    "Total charges - patient universe",
    "% charges at this hospital",
    "Total claims - this hospital",
    "Total claims - patient universe",
    "% claims at this hospital",
]

ZIP_ORIGINATION_COLUMNS = [
    "Zip Code",
    "City",
    "State",
    "Medicare Total Charges",
    "Medicare Avg Charge/Case",
    "Medicare % of Charges Within Search",
    "Medicare Total # of Cases",
    "Medicare Total Days of Care",
]

MEDICALCLAIMS_DRG_COLUMNS = [
    "DRG Code",
    "DRG Description",
    "Definitive ID",
    "Facility Name",
    "Firm Type",
    "# Actual Claims",
    "% Actual Claims",
    "# Actual Unique Patients",
    "Actual Charges",
    "% Actual Charges",
    "Charge/Claim (Actual)",
]

MEDICALCLAIMS_CPT_COLUMNS = [
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

OUTPATIENT_HOSPITAL_LEAKAGE_COLUMNS = [
    "Hospital Name",
    "HCPCS Category",
    "Total Pmts",
    "Total Charges",
    "Total Claims",
    "Unique Patients",
    "Network",
    "Network Parent",
    "Definitive ID",
]

REFERRALS_FROM_COLUMNS = [
    "Definitive ID",
    "Hospital name",
    "City",
    "State",
    "Medicare pmts",
    "Medicare charges",
    "# of referrals",
    "% of referrals",
    "# of unique beneficiaries",
    "Network name",
    "In-network referrals",
]

REFERRALS_TO_COLUMNS = [
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

OUTPATIENT_PROCEDURE_COLUMNS = [
    "Outpatient",
    "Procedure",
    "HCPCS/CPT Code",
    "# Actual Procedures",
]


class ClassificationTests(unittest.TestCase):
    def test_detected_year_from_filename(self):
        self.assertEqual(detect_year_from_filename("Rush_CPT_2025.csv"), "2025")
        self.assertEqual(detect_year_from_filename("Rush.2024.medicalclaims.csv"), "2024")
        self.assertEqual(detect_year_from_filename("Rush_no_year.csv"), "")

    def test_classifies_inpatient_drg_breakdown(self):
        result = classify_file(INPATIENT_DRG_COLUMNS)
        self.assertEqual(result.detected_file_type, "inpatient_drg_breakdown")

    def test_classifies_inpatient_leakage(self):
        result = classify_file(INPATIENT_LEAKAGE_COLUMNS)
        self.assertEqual(result.detected_file_type, "inpatient_leakage")

    def test_classifies_inpatient_marketshare(self):
        result = classify_file(INPATIENT_MARKETSHARE_COLUMNS)
        self.assertEqual(result.detected_file_type, "inpatient_marketshare")

    def test_classifies_zip_origination(self):
        result = classify_file(ZIP_ORIGINATION_COLUMNS)
        self.assertEqual(result.detected_file_type, "zip_origination")

    def test_classifies_medicalclaims_drg_breakdown(self):
        result = classify_file(MEDICALCLAIMS_DRG_COLUMNS)
        self.assertEqual(result.detected_file_type, "medicalclaims_drg_breakdown")

    def test_classifies_medicalclaims_cpt_breakdown(self):
        result = classify_file(MEDICALCLAIMS_CPT_COLUMNS)
        self.assertEqual(result.detected_file_type, "medicalclaims_cpt_breakdown")

    def test_classifies_outpatient_hospital_leakage(self):
        result = classify_file(OUTPATIENT_HOSPITAL_LEAKAGE_COLUMNS)
        self.assertEqual(result.detected_file_type, "outpatient_hospital_leakage")

    def test_classifies_referrals_from(self):
        result = classify_file(REFERRALS_FROM_COLUMNS)
        self.assertEqual(result.detected_file_type, "referrals_from")

    def test_classifies_referrals_to(self):
        result = classify_file(REFERRALS_TO_COLUMNS)
        self.assertEqual(result.detected_file_type, "referrals_to")

    def test_classifies_outpatient_procedure_breakdown(self):
        result = classify_file(OUTPATIENT_PROCEDURE_COLUMNS)
        self.assertEqual(result.detected_file_type, "outpatient_procedure_breakdown")

    def test_inpatient_leakage_not_medicalclaims_drg_breakdown(self):
        result = classify_file(INPATIENT_LEAKAGE_COLUMNS)
        self.assertNotEqual(result.detected_file_type, "medicalclaims_drg_breakdown")

    def test_inpatient_marketshare_not_medicalclaims_drg_breakdown(self):
        result = classify_file(INPATIENT_MARKETSHARE_COLUMNS)
        self.assertNotEqual(result.detected_file_type, "medicalclaims_drg_breakdown")

    def test_rush_medicalclaims_cpt_breakdown_regression(self):
        result = classify_file(MEDICALCLAIMS_CPT_COLUMNS)
        self.assertEqual(result.detected_file_type, "medicalclaims_cpt_breakdown")

    def test_unknown_file_type(self):
        result = classify_file(["Hospital", "Favorite Color", "Lunch Preference"])
        self.assertEqual(result.detected_file_type, "unknown")


if __name__ == "__main__":
    unittest.main()
