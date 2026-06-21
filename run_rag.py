from src.utils.config import setup_gemini
from src.analytics.rag_engine import get_retrieved_context
import google.generativeai as genai

def load_chunks(path="data/knowledge/insights.md"):
    text = open(path).read()
    parts = text.split("\n## ")
    chunks = []
    for i, p in enumerate(parts):
        chunk = ("## " + p) if i > 0 else p
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks

chunks = load_chunks()

genai = setup_gemini()
model = genai.GenerativeModel('models/gemini-3.5-flash') # fixed model name

user_query = "What is the primary driver of price in the Madrid Airbnb model?"

context = get_retrieved_context(user_query, chunks)

if context is None:
    print("No relevant information found in the knowledge base.")
else:
    print("---- RETRIEVED CONTEXT ----")
    print(context)
    print("----------------------------\n")

    prompt = (
        "Answer the following question using only the context provided. "
        "If it's not in the context, say you don't know.\n\n"
        f"Context: {context}\n\nQuestion: {user_query}"
    )
    response = model.generate_content(prompt)
    print(response.text)