import mimetypes
from services.gemini_client import get_gemini_client

def find_related_cases(file_path: str, language: str = "English") -> str:
    """
    Uses Gemini to extract the case context and then search for 
    related or similar landmark judgments in India.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    client = get_gemini_client()

    # Upload file first
    uploaded_file = client.files.upload(file=file_path)

    system_prompt = (
        f"You are 'Nyay-Linker', a multilingual Legal Case Relation Agent.\n"
        f"Always respond only in {language}.\n\n"
        "You will be given a case document. Your task is to identify **related and similar cases** "
        "from Indian law that share similar facts, legal issues, or judicial reasoning.\n\n"
        "Focus on:\n"
        "- Similar Supreme Court or High Court judgments.\n"
        "- Cases dealing with the same sections of IPC/CrPC or similar legal issues.\n"
        "- Mention famous or landmark Indian cases if relevant.\n\n"
        "Structure your response in **Markdown**, divided into the following sections:\n\n"
        "## 1. Related Indian Cases\n"
        "- List at least 5-7 similar cases.\n"
        "- Include: Case title, court, year, and a one-sentence reason for relation and summary of case in max 5-7 lines.\n"
        "- Example:\n"
        "  - **Maneka Gandhi vs. Union of India (1978, SC)** — related for principles of personal liberty under Article 21.\n\n"
        "## 2. Landmark or Precedent Cases\n"
        "- Mention any landmark or precedent-setting cases relevant to this issue.\n\n"
        "## 3. Summary Insight\n"
        "- Explain how these cases strengthen or contrast the current document’s reasoning.\n\n"
        "Rules:\n"
        "- Always output **only Markdown**, no HTML.\n"
        "- Use clear, neutral, and educational language.\n"
        "- If no clear match found, still suggest landmark analogous cases.\n"
        "- Keep everything in the selected language.\n"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[system_prompt, uploaded_file],
    )

    return response.text or "⚠️ No related cases found."