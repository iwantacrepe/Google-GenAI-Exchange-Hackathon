from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return genai.Client()
