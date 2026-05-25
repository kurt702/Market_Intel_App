from utils.schema import detect_fields, detect_dataset_type


def build_file_profiles(dataframes):
    file_profiles = {}

    for file_name, file_df in dataframes.items():
        file_fields = detect_fields(file_df)
        file_type = detect_dataset_type(file_fields)

        file_profiles[file_name] = {
            "fields": file_fields,
            "dataset_type": file_type
        }

    return file_profiles


def get_module_candidate_files(selected_module, file_profiles):
    candidates = []

    if selected_module == "Executive Packet":
        return list(file_profiles.keys())

    for file_name, profile in file_profiles.items():
        dataset_type = profile["dataset_type"]
        fields = profile["fields"]

        if selected_module == "ZIP Geography":
            if (
                dataset_type == "ZIP Geography"
                or len(fields.get("ZIP", [])) > 0
            ):
                candidates.append(file_name)

        elif selected_module == "Leakage":
            if dataset_type in [
                "Leakage Analysis",
                "Inpatient DRG Leakage",
                "Outpatient HCPCS Leakage"
            ]:
                candidates.append(file_name)

        elif selected_module == "Hospital Volume":
            if dataset_type == "Hospital Procedure Volume":
                candidates.append(file_name)

        elif selected_module == "ICD Analysis":
            if dataset_type == "ICD Procedure Volume":
                candidates.append(file_name)

        elif selected_module == "Referral Analysis":

            if (
                "referral" in dataset_type.lower()
                or len(fields.get("Referral", [])) > 0
                or len(fields.get("Origin", [])) > 0
                or len(fields.get("Destination", [])) > 0
            ):
                candidates.append(file_name)

    return candidates
