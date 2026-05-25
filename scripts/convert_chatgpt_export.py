import json
import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_ROOT = APP_ROOT.parent

input_dir = WORKFLOWS_ROOT / "ChatGPT_Export" / "Raw"
output_dir = WORKFLOWS_ROOT / "ChatGPT_Export" / "markdown"

output_dir.mkdir(parents=True, exist_ok=True)

def clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:100].strip() or "Untitled"

# Find all conversation JSON files
json_files = sorted(input_dir.glob("conversations-*.json"))

conversation_count = 0

for json_file in json_files:
    print(f"Processing {json_file.name}...")

    with open(json_file, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    for i, convo in enumerate(conversations, start=1):
        title = clean_filename(convo.get("title", f"Conversation_{conversation_count+i}"))
        mapping = convo.get("mapping", {})

        lines = [f"# {title}\n"]

        for node in mapping.values():
            message = node.get("message")

            if not message:
                continue

            role = message.get("author", {}).get("role", "unknown")
            parts = message.get("content", {}).get("parts", [])

            text_parts = []

            for part in parts:
                if isinstance(part, str):
                    text_parts.append(part)
                else:
                    text_parts.append(str(part))

            text = "\n".join(text_parts).strip()

            if text:
                lines.append(f"\n## {role.upper()}\n")
                lines.append(text)
                lines.append("\n")

        output_file = output_dir / f"{conversation_count+i:05d}_{title}.md"

        with open(output_file, "w", encoding="utf-8") as out:
            out.write("\n".join(lines))

    conversation_count += len(conversations)

print(f"\nDone. Converted {conversation_count} conversations.")
print(f"Markdown files saved to:\n{output_dir}")
