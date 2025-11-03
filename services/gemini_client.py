
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    # Remove any default GOOGLE_API_KEY injected by the base image
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]

    # Ensure we use only our Gemini API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError(" GEMINI_API_KEY not found in environment variables.")

    os.environ["GEMINI_API_KEY"] = api_key
    return genai.Client(api_key=api_key)
