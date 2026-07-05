"""
rag_utils.py
------------
Retrieval-Augmented Generation helpers.

Responsibilities:
  • Ingest PDF / TXT knowledge-base documents into a persistent ChromaDB collection.
  • Chunk text, embed with sentence-transformers (all-MiniLM-L6-v2), and store.
  • Retrieve the top-K most relevant chunks for a given query.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional

import pdfplumber

# ── Optional heavy dependencies (RAG stack) ──────────────────────────────────
# These are only required for the Knowledge Base / RAG feature.
# If they are not installed, the app still works — KB routes return a clear error.
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

import agent_instructions as AI

logger = logging.getLogger(__name__)

RAG_UNAVAILABLE_MSG = (
    "RAG packages not installed. Run: "
    "pip install numpy sentence-transformers chromadb --timeout 120"
)

# ── Singleton embedding model (loaded once) ──────────────────────────────────
_embed_model = None

def _get_embed_model():
    global _embed_model
    if not RAG_AVAILABLE:
        raise RuntimeError(RAG_UNAVAILABLE_MSG)
    if _embed_model is None:
        logger.info("Loading embedding model (all-MiniLM-L6-v2)…")
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


# ── ChromaDB client ──────────────────────────────────────────────────────────
_chroma_client = None
_COLLECTION_NAME = "interview_kb"

def _get_chroma_client():
    global _chroma_client
    if not RAG_AVAILABLE:
        raise RuntimeError(RAG_UNAVAILABLE_MSG)
    if _chroma_client is None:
        persist_dir = os.path.join(os.getcwd(), "chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
    return _chroma_client


def _get_collection():
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── Text extraction ───────────────────────────────────────────────────────────
def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from a PDF or TXT file."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ── Chunking ──────────────────────────────────────────────────────────────────
def _chunk_text(text: str, chunk_size: int = AI.RAG_CHUNK_SIZE,
                overlap: int = AI.RAG_CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping fixed-size chunks."""
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks


# ── Ingest ────────────────────────────────────────────────────────────────────
def ingest_document(file_path: str, doc_id: Optional[str] = None) -> int:
    """
    Ingest a document into the ChromaDB knowledge base.
    Returns the number of chunks added.
    Raises RuntimeError if RAG packages are not installed.
    """
    if not RAG_AVAILABLE:
        raise RuntimeError(RAG_UNAVAILABLE_MSG)

    if doc_id is None:
        doc_id = Path(file_path).stem

    text = extract_text_from_file(file_path)
    if not text.strip():
        logger.warning("No text extracted from %s", file_path)
        return 0

    chunks = _chunk_text(text)
    if not chunks:
        return 0

    embed_model = _get_embed_model()
    embeddings = embed_model.encode(chunks).tolist()

    collection = _get_collection()
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": doc_id, "chunk": i} for i in range(len(chunks))]

    # Upsert to avoid duplicates on re-upload
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    logger.info("Ingested %d chunks from '%s'", len(chunks), doc_id)
    return len(chunks)


# ── Retrieve ──────────────────────────────────────────────────────────────────
def retrieve_context(query: str, top_k: int = AI.RAG_TOP_K) -> str:
    """
    Retrieve the most relevant chunks for a query.
    Returns empty string if RAG is unavailable or KB is empty.
    """
    if not RAG_AVAILABLE:
        return ""  # gracefully degrade — prompts just won't have RAG context

    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return ""
    except Exception:
        return ""

    embed_model = _get_embed_model()
    query_embedding = embed_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, count),
        include=["documents", "metadatas"],
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    snippets = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        snippets.append(f"[Source: {source}]\n{doc}")

    return "\n\n".join(snippets)


# ── KB status ─────────────────────────────────────────────────────────────────
def get_kb_stats() -> dict:
    """Return basic stats about the current knowledge base."""
    if not RAG_AVAILABLE:
        return {"total_chunks": 0, "status": "unavailable", "message": RAG_UNAVAILABLE_MSG}
    try:
        collection = _get_collection()
        count = collection.count()
        return {"total_chunks": count, "status": "ready" if count > 0 else "empty"}
    except Exception as exc:
        logger.error("KB stats error: %s", exc)
        return {"total_chunks": 0, "status": "error"}


def clear_knowledge_base() -> None:
    """Drop and recreate the ChromaDB collection (full reset)."""
    client = _get_chroma_client()
    try:
        client.delete_collection(_COLLECTION_NAME)
        logger.info("Knowledge base cleared.")
    except Exception:
        pass
    _get_collection()  # re-create empty collection
