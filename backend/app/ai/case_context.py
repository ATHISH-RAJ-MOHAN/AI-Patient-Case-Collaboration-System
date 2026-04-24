import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.faiss_store import has_index
from app.ai.indexing import index_case_documents
from app.models import Document


async def ensure_case_index(case_id: int, db: AsyncSession) -> bool:
    """
    Build a searchable AI index for existing case documents when one is missing.
    This keeps older uploads useful even if they were added before indexing worked.
    """
    if has_index(case_id):
        return True

    documents_result = await db.execute(
        select(Document).where(Document.case_id == case_id)
    )
    documents = documents_result.scalars().all()
    if not documents:
        return False

    indexed_chunks = await asyncio.to_thread(
        index_case_documents,
        case_id,
        [document.file_path for document in documents],
    )

    return indexed_chunks > 0
