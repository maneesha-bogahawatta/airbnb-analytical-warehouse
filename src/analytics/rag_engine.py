import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Load a lightweight local model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_retrieved_context(query, knowledge_base_chunks):
    # 2. Embed the query and the knowledge chunks
    query_vec = model.encode([query])
    chunk_vecs = model.encode(knowledge_base_chunks)
    
    # 3. Calculate similarity (The "Retrieve" step)
    similarities = cosine_similarity(query_vec, chunk_vecs)
    
    # 4. Get the index of the best match
    best_idx = np.argmax(similarities)
    
    return knowledge_base_chunks[best_idx]