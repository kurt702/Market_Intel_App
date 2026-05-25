import csv
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_ROOT = APP_ROOT.parent

input_file = WORKFLOWS_ROOT / "Knowledge_Base" / "conversation_index_categorized.csv"
output_file = WORKFLOWS_ROOT / "Knowledge_Base" / "high_value_conversations.csv"

high_value_categories = {
    "Philips_Strategy",
    "Market_Intel",
    "NW_Neuro",
    "Business_Ideas",
    "Finance",
    "Career",
    "Clinical_OT",
    "AI_and_Tech",
    "Writing"
}

with open(input_file, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

filtered = [
    row for row in rows
    if row.get("category") in high_value_categories
    and int(row.get("word_count", 0)) > 300
]

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(filtered)

print(f"Done. Kept {len(filtered)} high-value conversations.")
print(f"Saved to: {output_file}")
