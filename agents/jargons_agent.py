import mimetypes
from services.gemini_client import get_gemini_client

def explain_jargons(file_path: str, language: str = "English") -> str:
    """
    Detects and explains complex legal or Latin terms,
    as well as short legal phrases, from the uploaded document.
    """
    client = get_gemini_client()

    # Upload file to Gemini
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    uploaded_file = client.files.upload(file=file_path)

    system_prompt = (
        f"You are 'Lexis-Terms', a multilingual legal term explainer.\n"
        f"Always respond in {language}.\n\n"
        "Analyze the uploaded legal document carefully.\n"
        "Detect **complex legal or Latin words, maxims, short phrases, and procedural expressions** "
        "that might confuse a layperson.\n\n"
        "For each, give a short, plain-English explanation (2–4 sentences) "
        "and, if relevant, a simple real-world example.\n\n"
        "Return a Markdown table only (no extra text before/after the table):\n\n"
        "| Term or Phrase | Meaning in Plain language | Example (if any) |\n"
        "|----------------|--------------------------|------------------|\n"
        "| *Habeas Corpus* | A legal writ to bring a detained person before court. | Example: Used when someone is unlawfully imprisoned. |\n\n"
        "Include both single words (e.g., *estoppel*, *jurisprudence*) and short phrases "
        "(e.g., *beyond reasonable doubt*, *res judicata*). "
        "Avoid common English words, focus on domain-specific terms. "
        "Give answer always in markdown."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[system_prompt, uploaded_file],
    )
    
    text = (response.text or "{}").strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return response.text or "⚠️ No jargons detected or explanation generated."
