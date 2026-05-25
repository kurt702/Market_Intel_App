from pathlib import Path
import csv

APP_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_ROOT = APP_ROOT.parent

markdown_dir = WORKFLOWS_ROOT / "ChatGPT_Export" / "markdown"
output_file = WORKFLOWS_ROOT / "Knowledge_Base" / "conversation_index.csv"

rows = []

for file in sorted(markdown_dir.glob("*.md")):
    text = file.read_text(encoding="utf-8", errors="ignore")
    title = text.splitlines()[0].replace("#", "").strip() if text else file.stem

    preview = " ".join(text.split())[:500]
    word_count = len(text.split())

    rows.append({
        "file_name": file.name,
        "title": title,
        "word_count": word_count,
        "category": "",
        "tags": "",
        "summary": "",
        "preview": preview
    })

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["file_name", "title", "word_count", "category", "tags", "summary", "preview"]
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. Indexed {len(rows)} markdown files.")
print(f"Saved to: {output_file}")
