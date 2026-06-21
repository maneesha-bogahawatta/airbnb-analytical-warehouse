# run_rag.py
from src.utils.config import setup_gemini
from src.analytics.rag_engine import get_retrieved_context
import google.generativeai as genai

# NEW: Read your insights file
with open("data/knowledge/insights.md", "r") as f:
    # Splitting by double newline to create chunks
    chunks = f.read().split("\n\n")

# Setup
genai = setup_gemini()
model = genai.GenerativeModel('models/gemini-3.5-flash')

# 1. Your question
user_query = "What is the primary driver of price in the Madrid Airbnb model?"

# 2. Retrieve 
context = get_retrieved_context(user_query, chunks)

# 3. Generate 
prompt = f"Answer the following question using only the context provided. If it's not in the context, say you don't know. Context: {context}. Question: {user_query}"
response = model.generate_content(prompt)

print(response.text)