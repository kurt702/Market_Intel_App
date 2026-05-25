from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_ROOT = APP_ROOT.parent

base_path = WORKFLOWS_ROOT / "Knowledge_Base"

folders = [
    "Philips_Strategy",
    "Market_Intel",
    "NW_Neuro",
    "Business_Ideas",
    "Finance",
    "Career",
    "Relationships",
    "Psychology",
    "Clinical_OT",
    "AI_and_Tech",
    "Writing",
    "Random",
    "Archive"
]

for folder in folders:
    folder_path = base_path / folder
    folder_path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {folder_path}")

print("\nKnowledge base folder structure created successfully.")
