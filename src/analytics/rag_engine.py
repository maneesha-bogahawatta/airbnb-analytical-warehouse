import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')


def load_chunks(path="data/knowledge/insights.md"):
    """Load and chunk the knowledge base by markdown heading, so each chunk
    is a self-contained, retrievable section rather than split mid-thought."""
    text = open(path, encoding="utf-8").read()
    parts = text.split("\n## ")
    chunks = []
    for i, p in enumerate(parts):
        chunk = ("## " + p) if i > 0 else p
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


def _chunk_title(chunk: str) -> str:
    """First heading line of a chunk, used as a human-readable source label."""
    first_line = chunk.strip().split("\n", 1)[0]
    return first_line.lstrip("#").strip() or "Untitled section"


def get_retrieved_context(query, knowledge_base_chunks, top_k=4, threshold=0.3):
    """Original interface, unchanged -- used by run_rag.py and anything else
    that only needs the joined context text."""
    query_vec = model.encode([query])
    chunk_vecs = model.encode(knowledge_base_chunks)
    similarities = cosine_similarity(query_vec, chunk_vecs)[0]
    top_idx = similarities.argsort()[::-1][:top_k]
    top_idx = [i for i in top_idx if similarities[i] >= threshold]
    if not top_idx:
        return None  # nothing relevant enough
    return "\n\n".join(knowledge_base_chunks[i] for i in top_idx)


def get_retrieved_context_with_sources(query, knowledge_base_chunks, top_k=4, threshold=0.3):
    """Same retrieval logic as get_retrieved_context, but also returns which
    chunks were used and their similarity scores -- so a caller (e.g. the
    dashboard) can show the user exactly what grounded the answer, instead
    of treating the RAG as an opaque black box.

    Returns:
        (context_text, sources) where sources is a list of
        {"title": str, "score": float, "text": str} dicts, ordered by
        relevance (highest first). Returns (None, []) if nothing clears
        the similarity threshold.
    """
    query_vec = model.encode([query])
    chunk_vecs = model.encode(knowledge_base_chunks)
    similarities = cosine_similarity(query_vec, chunk_vecs)[0]
    top_idx = similarities.argsort()[::-1][:top_k]
    top_idx = [i for i in top_idx if similarities[i] >= threshold]

    if not top_idx:
        return None, []

    context_text = "\n\n".join(knowledge_base_chunks[i] for i in top_idx)
    sources = [
        {
            "title": _chunk_title(knowledge_base_chunks[i]),
            "score": float(similarities[i]),
            "text": knowledge_base_chunks[i],
        }
        for i in top_idx
    ]
    return context_text, sources