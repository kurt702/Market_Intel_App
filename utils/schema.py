def detect_fields(df):
    return {
        "Hospital": [c for c in df.columns if any(x in c.lower() for x in ["hospital", "facility", "account", "site"])],
        "Physician": [c for c in df.columns if any(x in c.lower() for x in ["physician", "provider", "doctor", "md"])],
        "Procedure": [c for c in df.columns if any(x in c.lower() for x in ["procedure", "proc", "description"])],
        "Charges": [c for c in df.columns if any(x in c.lower() for x in ["charge", "charges", "revenue", "payment", "cost", "dollars", "amount"])],
        "ZIP": [c for c in df.columns if any(x in c.lower() for x in ["zip", "zipcode", "postal"])],
        "DRG": [c for c in df.columns if "drg" in c.lower()],
        "CPT": [c for c in df.columns if "cpt" in c.lower()],
        "HCPCS": [c for c in df.columns if "hcpcs" in c.lower()],
        "ICD": [c for c in df.columns if "icd" in c.lower()],
        "Volume": [c for c in df.columns if any(x in c.lower() for x in ["volume", "cases", "count", "patients", "# of procedures", "procedures"])],
        "Referral": [c for c in df.columns if any(x in c.lower() for x in ["referral", "leakage", "transfer"])],
        "Leakage": [c for c in df.columns if any(x in c.lower() for x in ["leakage", "leaked", "external", "outmigration", "out-migration", "lost"])],
        "Destination": [c for c in df.columns if any(x in c.lower() for x in ["destination", "to hospital", "to facility", "receiving", "competitor", "external facility", "leakage facility", "hospital name", "facility name"])],
        "Origin": [c for c in df.columns if any(x in c.lower() for x in ["origin", "from hospital", "from facility", "source", "referring"])],
        "Geography": [c for c in df.columns if any(x in c.lower() for x in ["city", "state", "county", "market", "region"])],
        "Quality": [c for c in df.columns if any(x in c.lower() for x in ["mortality", "readmission", "los", "length"])],
        "Device": [c for c in df.columns if any(x in c.lower() for x in ["device", "cied", "icd", "pacemaker", "lead"])]
    }


def detect_dataset_type(fields):
    if (fields["Referral"]
        or (fields["Origin"] and fields["Destination"])):
        return "Referral Analysis"
    if fields["Leakage"] or (fields["Destination"] and fields["Charges"]):
        return "Leakage Analysis"
    if fields["DRG"]:
        return "Inpatient DRG Leakage"
    if fields["HCPCS"]:
        return "Outpatient HCPCS Leakage"
    if fields["CPT"]:
        return "Procedure / CPT Analytics"
    if fields["ZIP"]:
        return "ZIP Geography"
    if fields["Hospital"] and fields["Volume"]:
        return "Hospital Procedure Volume"
    if fields["ICD"] and fields["Volume"]:
        return "ICD Procedure Volume"
    return "Unknown"