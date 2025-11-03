import json, mimetypes, re
from services.gemini_client import get_gemini_client
import os

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
    safe_path = os.path.join("/tmp", os.path.basename(file_path))
    if not os.path.exists(safe_path):
        try:
            with open(file_path, "rb") as src, open(safe_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            print(f"⚠️ File copy failed: {e}", flush=True)
            safe_path = file_path

    # Guess mime type
    mime_type, _ = mimetypes.guess_type(safe_path)
    mime_type = mime_type or "application/octet-stream"

    # Upload to Gemini
    try:
        uploaded_file = client.files.upload(file=safe_path)
    except Exception as e:
        print(f"❌ Gemini file upload failed: {e}", flush=True)
        uploaded_file = None

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

    try:
        # Stream response for faster first tokens
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=[system_prompt, uploaded_file] if uploaded_file else [system_prompt]
        )
        text = "".join(chunk.text for chunk in response_stream if chunk.text)
    except Exception as e:
        print(f"❌ Gemini generation failed: {e}", flush=True)
        text = ""

    text = text.replace("```json", "").replace("```", "").strip()
    print("🧩 Gemini timeline raw output (first 200 chars):", text[:200], flush=True)

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
    print(" Gemini timeline raw output:", text[:300])
    # ✅ Always return valid JSON array
    return json.dumps(timeline, indent=2)