import os
import logging
from django.conf import settings
from .models import Document, Chunk
from .extractors import extract_text_from_file
from .chunker import chunk_document_text
from .ollama_embedding import embed_text
import chromadb

logger = logging.getLogger(__name__)

CHROMA_DIR = str(settings.CHROMA_PERSIST_DIRECTORY)
os.makedirs(CHROMA_DIR, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(name=str(settings.CHROMA_COLLECTION_NAME))


def ingest_document(document_id):

    doc = Document.objects.get(id=document_id)

    text, metadata = extract_text_from_file(doc.file.path)

    doc.extracted_text = text
    doc.metadata = metadata or {}
    doc.save(update_fields=["extracted_text", "metadata"])

    print("Extracted text length:", len(text))
    print("Preview:", text[:300])

    if not text.strip():
        logger.warning("No text extracted from document")
        return 0

    chunks = chunk_document_text(text)

    if not chunks:
        logger.warning("No chunks created")
        return 0

    # ---- 3. Clear old vectors + chunks ----
    existing = collection.get()
    if existing and existing["ids"]:
        collection.delete(ids=existing["ids"])
    Chunk.objects.all().delete()  # wipe old DB chunks

    embeddings = embed_text(chunks)

    if len(embeddings) != len(chunks):
        raise RuntimeError("Embedding count mismatch")

    ids = [f"doc{doc.id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": doc.id, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    Chunk.objects.bulk_create([
        Chunk(document=doc, chunk_index=i, text=chunks[i], chroma_id=ids[i])
        for i in range(len(chunks))
    ])

    logger.info(f"Ingested {len(chunks)} chunks")

    return len(chunks)
