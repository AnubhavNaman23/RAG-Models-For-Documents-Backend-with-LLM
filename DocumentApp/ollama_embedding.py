import ollama
import logging
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "nomic-embed-text"

def _extract_embedding(resp):
    if hasattr(resp, "embedding"):
        return resp.embedding
    if isinstance(resp, dict) and "embedding" in resp:
        return resp["embedding"]
    raise RuntimeError(f"Unexpected embedding response type: {type(resp)}")

def embed_text(texts):
    vectors = []
    for t in texts:
        r = ollama.embeddings(model=EMBEDDING_MODEL, prompt=t)
        vectors.append(_extract_embedding(r))
    return vectors

def embed_query(query):
    r = ollama.embeddings(model=EMBEDDING_MODEL, prompt=query)
    return _extract_embedding(r)
