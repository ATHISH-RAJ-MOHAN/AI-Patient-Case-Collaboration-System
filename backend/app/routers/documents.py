from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import shutil
import logging

from app.db import get_db
from app.models import Document, CaseMember, PatientCase, User
from app.schemas import DocumentOut
from app.security import get_current_user

from app.ai.document_processor import extract_text
from app.ai.chunking import chunk_text
from app.ai.embeddings import get_embedding_batch
from app.ai.faiss_store import add_embeddings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

# project_root/uploads
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_document_for_ai(case_id: int, disk_path: Path) -> None:
    """
    Extract text, chunk it, create embeddings, and store in case-specific FAISS.
    This runs in the background so it does not block the upload response.
    """
    try:
        text = extract_text(str(disk_path))

        if not text or not text.strip():
            logger.warning("No text extracted from %s", disk_path)
            return

        chunks = [chunk.strip() for chunk in chunk_text(text) if chunk.strip()]
        if not chunks:
            logger.warning("No chunks created from %s", disk_path)
            return

        embeddings = get_embedding_batch(chunks)
        if not embeddings:
            logger.warning("No embeddings created for %s", disk_path)
            return

        valid_chunks = []
        valid_embeddings = []
        for chunk, emb in zip(chunks, embeddings):
            if emb:
                valid_chunks.append(chunk)
                valid_embeddings.append(emb)

        if valid_embeddings:
            add_embeddings(case_id, valid_embeddings, valid_chunks)
            logger.info("AI indexing complete for %s", disk_path)

    except Exception as e:
        logger.exception("AI processing failed for %s: %s", disk_path, e)


@router.post("/upload/{case_id}", response_model=DocumentOut)
async def upload_document(
    case_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case_result = await db.execute(
        select(PatientCase).where(PatientCase.id == case_id)
    )
    case = case_result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == current_user.id,
        )
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not allowed in this case")

    original_name = Path(file.filename).name if file.filename else "upload.bin"
    suffix = Path(original_name).suffix.lower()
    stem = Path(original_name).stem
    unique_name = f"{stem}_{case_id}_{current_user.id}{suffix}"

    disk_path = UPLOAD_DIR / unique_name
    public_path = f"/uploads/{unique_name}"

    with open(disk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(
        case_id=case_id,
        uploaded_by=current_user.id,
        file_name=original_name,
        file_type=file.content_type or "application/octet-stream",
        file_path=public_path,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    background_tasks.add_task(process_document_for_ai, case_id, disk_path)

    return document


@router.get("/case/{case_id}", response_model=list[DocumentOut])
async def get_case_documents(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == current_user.id,
        )
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not allowed")

    result = await db.execute(
        select(Document).where(Document.case_id == case_id)
    )

    return result.scalars().all()