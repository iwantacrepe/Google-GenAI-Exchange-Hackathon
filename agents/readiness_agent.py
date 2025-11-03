import mimetypes
from services.gemini_client import get_gemini_client

def prepare_hearing_readiness(file_path: str, language: str = "English") -> str:
    """
    Generates a structured readiness checklist, strategy notes, and argument focus areas 
    for an upcoming court hearing, based on the case document.
    """
    client = get_gemini_client()
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    uploaded_file = client.files.upload(file=file_path)

    system_prompt = (
        f"You are 'Nyay-Strategist', a multilingual Legal Readiness & Strategy Agent.\n"
        f"Always respond in {language}.\n\n"
        "You will receive a legal case document. The hearing is scheduled for **tomorrow**.\n"
        "Your task is to prepare a **comprehensive readiness brief** to ensure the lawyer or petitioner "
        "is fully prepared for the hearing.\n\n"
        "### Instructions:\n"
        "- Analyze the entire case context.\n"
        "- Identify **critical arguments, weak points, and supporting evidence**.\n"
        "- Suggest **possible counterarguments** the opposing party might raise.\n"
        "- Create a **checklist of readiness tasks** (documents, witnesses, laws to cite, etc.).\n"
        "- Mention **important sections of law**, landmark judgments, and procedural deadlines.\n\n"
        "### Output strictly in Markdown format as below:\n"
        "## 1. Case Snapshot\n"
        "- One short paragraph summarizing the case posture before tomorrow’s hearing.\n\n"
        "## 2. Critical Points & Arguments\n"
        "- Bullet list of your strongest arguments.\n"
        "- Highlight legal sections or evidence that back them.\n\n"
        "## 3. Opponent’s Expected Counterarguments\n"
        "- List likely counterpoints and how to preempt or defend against them.\n\n"
        "## 4. Readiness Checklist\n"
        "- List things to verify before hearing (documents, affidavits, witness confirmations, etc.).\n"
        "- Mention deadlines or procedural filings.\n\n"
        "## 5. Suggested Citations / Case Laws\n"
        "- Include 2–5 landmark or recent cases relevant to this issue.\n\n"
        "## 6. Hearing Day Strategy Summary\n"
        "- A 5-line practical brief of what to focus on in tomorrow’s hearing.\n\n"
        "Rules:\n"
        "- Always use Markdown (no HTML).\n"
        "- Stay practical — assume this is for real preparation.\n"
        "- Do not repeat full case text — summarize insightfully."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[system_prompt, uploaded_file],
    )

    return response.text or "⚠️ Unable to generate hearing readiness brief."
