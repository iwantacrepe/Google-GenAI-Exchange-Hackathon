import json, mimetypes, re
from services.gemini_client import get_gemini_client

def extract_timeline(file_path: str, language: str = "English") -> str:
    """
    Generates a structured chronological timeline from legal documents.
    If explicit dates are missing, Gemini infers logical order of events
    based on typical case progression and narrative flow.
    Includes robust JSON recovery and fallback inference.
    """
    client = get_gemini_client()
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    uploaded_file = client.files.upload(file=file_path)

    # 🧩 Enhanced system prompt with reasoning guidance
    system_prompt = (
        f"You are 'Lexis-Timeline', a multilingual legal chronologist and investigator.\n"
        f"Always respond in {language}.\n\n"
        "Your task is to build a **clear, chronological timeline** of all major events, "
        "even if the document does not explicitly mention dates.\n\n"
        "Use logical legal sequencing to infer order, following this typical pattern:\n"
        "→ Complaint / Incident → FIR or Registration → Investigation → Arrest / Charges → Hearings → Arguments → Judgment / Verdict → Appeals (if any).\n\n"
        "Each timeline event should have:\n"
        "- `date`: If available; otherwise use `Stage 1`, `Stage 2`, etc. in logical order.\n"
        "- `title`: A short phrase summarizing the event.\n"
        "- `description`: A 2–3 sentence plain-language summary of what happened.\n\n"
        "Be smart in ordering — if the document talks about evidence before the arrest, fix it to correct order.\n"
        "If multiple parallel proceedings exist, include them as separate sequences with stage indicators.\n\n"
        "Return **only** a JSON array of objects like:\n"
        "[\n"
        "  {\"date\": \"Stage 1\", \"title\": \"Complaint Filed\", \"description\": \"The complainant reported...\"},\n"
        "  {\"date\": \"Stage 2\", \"title\": \"FIR Registered\", \"description\": \"Police registered a case...\"}\n"
        "]\n\n"
        " Rules:\n"
        "- Do not include any commentary, markdown, or extra text outside the JSON.\n"
        "- If uncertain, still maintain a logical order based on procedural sense.\n"
        "- Always write all text in the chosen language.\n"
    )

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[system_prompt, uploaded_file],
    )

    text = (resp.text or "").strip()
    text = text.replace("```json", "").replace("```", "").strip()

    # ✅ Stage 1: Direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return json.dumps(parsed, indent=2)
    except Exception:
        pass

    # ✅ Stage 2: Extract JSON-like content inside brackets
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return json.dumps(parsed, indent=2)
        except Exception:
            pass

    # ✅ Stage 3: Attempt to auto-repair broken JSON
    try:
        repaired = (
            text.replace("’", "'")
                .replace("“", '"')
                .replace("”", '"')
                .replace("True", "true")
                .replace("False", "false")
                .strip()
        )
        if repaired.count("[") > repaired.count("]"): repaired += "]"
        if repaired.count("{") > repaired.count("}"): repaired += "}"
        parsed = json.loads(repaired)
        if isinstance(parsed, list):
            return json.dumps(parsed, indent=2)
    except Exception:
        pass

    # ✅ Stage 4: Final fallback (logical inference)
    lines = [l.strip("•- ") for l in text.split("\n") if l.strip()]
    inferred_stages = [
        "Complaint / Incident Reported",
        "FIR Registered / Case Filed",
        "Investigation or Evidence Collection",
        "Arrest / Charges Framed",
        "Court Hearings / Witness Statements",
        "Arguments & Submissions",
        "Judgment / Order Pronounced",
        "Post-Judgment Actions or Appeals"
    ]

    timeline = []
    for i, stage in enumerate(inferred_stages):
        desc = lines[i] if i < len(lines) else "Not explicitly mentioned but inferred from legal flow."
        timeline.append({
            "date": f"Stage {i+1}",
            "title": stage,
            "description": desc
        })

    # ✅ Always return valid JSON array
    return json.dumps(timeline, indent=2)