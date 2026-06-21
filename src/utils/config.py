import os
from dotenv import load_dotenv
import google.generativeai as genai

def setup_gemini():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in .env file")
    genai.configure(api_key=api_key)
    return genai