import logging
from pathlib import Path
from typing import Iterable

from app.ai.chunking import chunk_text
from app.ai.document_processor import extract_text
from app.ai.embeddings import get_embedding_batch
from app.ai.faiss_store import add_embeddings


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "uploads"


def resolve_document_path(file_path: str) -> Path:
    """
    Convert stored public paths like /uploads/report.pdf into local disk paths.
    """
    clean_path = file_path.lstrip("/")
    if clean_path.startswith("uploads/"):
        return PROJECT_ROOT / clean_path
    return UPLOAD_DIR / clean_path


def index_document_for_ai(case_id: int, disk_path: Path) -> int:
    """
    Extract text, chunk it, create embeddings, and store them in case-specific FAISS.
    Returns the number of chunks indexed.
    """
    try:
        text = extract_text(str(disk_path))

        if not text or not text.strip():
            logger.warning("No text extracted from %s", disk_path)
            return 0

        chunks = [chunk.strip() for chunk in chunk_text(text) if chunk.strip()]
        if not chunks:
            logger.warning("No chunks created from %s", disk_path)
            return 0

        embeddings = get_embedding_batch(chunks)
        if not embeddings:
            logger.warning("No embeddings created for %s", disk_path)
            return 0

        valid_chunks = []
        valid_embeddings = []
        for chunk, embedding in zip(chunks, embeddings):
            if embedding:
                valid_chunks.append(chunk)
                valid_embeddings.append(embedding)

        if not valid_embeddings:
            logger.warning("No valid embeddings created for %s", disk_path)
            return 0

        add_embeddings(case_id, valid_embeddings, valid_chunks)
        logger.info("AI indexing complete for %s", disk_path)
        return len(valid_chunks)

    except Exception as exc:
        logger.exception("AI processing failed for %s: %s", disk_path, exc)
        return 0


def index_case_documents(case_id: int, file_paths: Iterable[str]) -> int:
    indexed_chunks = 0
    for file_path in file_paths:
        disk_path = resolve_document_path(file_path)
        if not disk_path.exists():
            logger.warning("Document file does not exist: %s", disk_path)
            continue

        indexed_chunks += index_document_for_ai(case_id, disk_path)

    return indexed_chunks
