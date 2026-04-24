from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil
from pathlib import Path

from app.db import get_db
from app.models import Document, CaseMember, PatientCase, User
from app.schemas import DocumentOut
from app.security import get_current_user

from app.ai.indexing import UPLOAD_DIR, index_document_for_ai

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_document_for_ai(case_id: int, disk_path: Path) -> None:
    """
    Extract text, chunk it, create embeddings, and store in case-specific FAISS.
    This runs in the background so it does not block the upload response.
    """
    index_document_for_ai(case_id, disk_path)


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
