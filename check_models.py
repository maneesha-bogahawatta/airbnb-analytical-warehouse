import google.generativeai as genai
from src.utils.config import setup_gemini

setup_gemini()

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)