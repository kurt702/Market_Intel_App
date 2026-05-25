import csv
import json
import requests
from pathlib import Path

MODEL = "qwen3:14b"
BATCH_LIMIT = 10

APP_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_ROOT = APP_ROOT.parent

index_file = WORKFLOWS_ROOT / "Knowledge_Base" / "high_value_conversations.csv"
markdown_dir = WORKFLOWS_ROOT / "ChatGPT_Export" / "markdown"
output_file = WORKFLOWS_ROOT / "Knowledge_Base" / "high_value_conversations_summarized.csv"

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    return response.json()["response"].strip()

with open(index_file, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

processed = []

for row in rows[:BATCH_LIMIT]:
    file_path = markdown_dir / row["file_name"]

    if not file_path.exists():
        row["summary"] = "ERROR: markdown file not found"
        processed.append(row)
        continue

    text = file_path.read_text(encoding="utf-8", errors="ignore")[:12000]

    prompt = f"""
Summarize this ChatGPT conversation for a personal knowledge base.

Return ONLY valid JSON with these keys:
summary
category
tags
business_value
action_items

Conversation:
{text}
"""

    print(f"Summarizing: {row['file_name']}")

    try:
        result = ask_ollama(prompt)
        data = json.loads(result)

        row["summary"] = data.get("summary", "")
        row["category"] = data.get("category", row.get("category", ""))
        row["tags"] = ", ".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags", "")
        row["business_value"] = data.get("business_value", "")
        row["action_items"] = data.get("action_items", "")

    except Exception as e:
        row["summary"] = f"ERROR: {e}"

    processed.append(row)

fieldnames = list(processed[0].keys())

for extra in ["business_value", "action_items"]:
    if extra not in fieldnames:
        fieldnames.append(extra)

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(processed)

print(f"\nDone. Summarized {len(processed)} conversations.")
print(f"Saved to: {output_file}")
