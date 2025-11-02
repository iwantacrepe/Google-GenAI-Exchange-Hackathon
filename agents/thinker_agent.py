# agents/thinker_agent.py
from typing import List, Dict, Optional
import mimetypes
from services.gemini_client import get_gemini_client

def chat_with_thinker(history: List[Dict[str, str]], language: str = "English", files: Optional[List[str]] = None) -> str:
    """
    Thinker Agent — A conversational legal advisor that:
       remembers past chat context,
       uses uploaded documents as reference,
       replies in the chosen language,
       outputs rich Markdown answers.
    """
    client = get_gemini_client()

    # Upload attached files (only once per session ideally)
    uploaded_refs = []
    if files:
        for file_path in files:
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            try:
                uploaded_file = client.files.upload(file=file_path)
                uploaded_refs.append(uploaded_file)
            except Exception as e:
                print("File upload failed:", e)

    system_prompt = (
    f"You are 'Nyay-Sahayak', a multilingual legal and strategic reasoning assistant.\n"
    f"Always respond in {language}.\n\n"
    "You have access to the user's uploaded legal documents and prior conversation.\n"
    "Treat those documents as *primary evidence* for your reasoning.\n"
    "When you quote or rely on the text, clearly cite it — e.g.:\n"
    "‘(Source: Page 3)’ or ‘(Ref: Para 2, Page 5)’.\n\n"
    "Organize every answer in this format:\n"
    "1. **Context** – Restate what the user is asking and summarize any relevant facts.\n"
    "2. **Reasoning** – Explain the logical and legal interpretation.\n"
    "3. **Evidence** – Quote or reference document excerpts that support your reasoning.\n"
    "4. **Implication** – Clarify what this means for the user, neutrally.\n\n"
    " Guidelines:\n"
    "- Never invent or fabricate citations; quote only from provided material.\n"
    "- If evidence is insufficient, ask clarifying questions.\n"
    "- Be empathetic and concise; use Markdown for formatting (headings, bullet points, emphasis).\n"
    "- Do **not** provide binding legal advice — remain educational and analytical."
)


    # Combine into structured Gemini chat content
    contents = []
    
    # Add system instruction as first user message
    contents.append(system_prompt)
    
    # Add chat history
    for msg in history:
        contents.append(msg.get("content", ""))
    
    # Add uploaded files as part of the content
    if uploaded_refs:
        contents.extend(uploaded_refs)

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=contents,
    )

    return response.text or "⚠️ No response generated."
