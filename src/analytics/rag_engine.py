import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_retrieved_context(query, knowledge_base_chunks, top_k=4, threshold=0.3):
    query_vec = model.encode([query])
    chunk_vecs = model.encode(knowledge_base_chunks)
    similarities = cosine_similarity(query_vec, chunk_vecs)[0]

    top_idx = similarities.argsort()[::-1][:top_k]
    top_idx = [i for i in top_idx if similarities[i] >= threshold]

    if not top_idx:
        return None  # nothing relevant enough

    return "\n\n".join(knowledge_base_chunks[i] for i in top_idx)