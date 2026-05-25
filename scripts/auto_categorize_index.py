import csv
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_ROOT = APP_ROOT.parent

input_file = WORKFLOWS_ROOT / "Knowledge_Base" / "conversation_index.csv"
output_file = WORKFLOWS_ROOT / "Knowledge_Base" / "conversation_index_categorized.csv"

categories = {
    "Philips_Strategy": ["philips", "lead management", "ciied", "extraction", "epic", "power bi", "definitive", "hospital", "cfo", "cvsl"],
    "Market_Intel": ["heat map", "leakage", "referral", "market", "claims", "drg", "cpt", "hcpcs", "zipcode", "facility"],
    "NW_Neuro": ["nw neuro", "neuro", "driving", "stisim", "occupational therapy", "ot", "vestibular", "low vision"],
    "Business_Ideas": ["business", "llc", "side hustle", "consulting", "website", "service", "offer", "product"],
    "Finance": ["401k", "roth", "vanguard", "investment", "savings", "cash flow", "net worth", "mortgage", "credit card"],
    "Career": ["career", "job", "interview", "director", "promotion", "resume", "linkedin", "leadership"],
    "Relationships": ["relationship", "dating", "text", "reply", "nora", "romantic"],
    "Psychology": ["anxiety", "guilt", "ego", "shame", "fear", "confidence", "grounded", "embodied"],
    "Clinical_OT": ["soap", "objective note", "assessment note", "patient", "functional mobility", "transfer", "adl"],
    "AI_and_Tech": ["ai", "llm", "gpu", "5080", "5090", "ollama", "lm studio", "python", "local model"],
    "Writing": ["rewrite", "draft", "email", "tone", "summary", "polish", "wording"]
}

def classify(text):
    text = text.lower()
    scores = {}

    for category, keywords in categories.items():
        score = sum(text.count(keyword) for keyword in keywords)
        if score > 0:
            scores[category] = score

    if not scores:
        return "Random"

    return max(scores, key=scores.get)

with open(input_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for row in rows:
    combined_text = f"{row.get('title','')} {row.get('preview','')}"
    row["category"] = classify(combined_text)

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. Categorized {len(rows)} conversations.")
print(f"Saved to: {output_file}")
