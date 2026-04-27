import os
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import CaseMember, User
from app.security import get_current_user
from app.schemas import AIQueryRequest, AIQueryResponse, AISource
from app.ai.embeddings import get_embedding
from app.ai.faiss_store import search
from app.ai.case_context import ensure_case_index
from app.ai.openai_client import create_openai_client

router = APIRouter(prefix="/ai", tags=["AI"])


def should_ai_respond(message: str) -> bool:
    if not message:
        return False
    msg = message.strip().lower()
    return msg.startswith("@ai") or msg.startswith("/ai") or msg.startswith("ai:")


def strip_ai_prefix(content: str) -> str:
    msg = content.strip()
    lowered = msg.lower()

    if lowered.startswith("@ai"):
        return msg[3:].strip()
    if lowered.startswith("/ai"):
        return msg[3:].strip()
    if lowered.startswith("ai:"):
        return msg[3:].strip()

    return msg


def generate_case_ai_reply_sync(case_id: int, question: str) -> tuple[str, list[dict]]:
    """
    Returns:
        (answer, sources)
    """
    query_embedding = get_embedding(question)
    if not query_embedding:
        return "I could not process the question right now.", []

    results = search(case_id, query_embedding, top_k=5)
    if not results:
        return "I could not find any relevant information in this case yet.", []

    context = "\n".join([f"- {chunk}" for chunk, _score in results])

    client = create_openai_client()

    prompt = f"""
You are an AI assistant inside a patient case group chat.

Rules:
- Answer only using the case-specific context below.
- Do not use outside knowledge if the answer is not in the context.
- If the answer is not present, say you could not find it in the uploaded case documents.
- Keep the answer short and clear.

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You answer only from case-specific context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content or "I could not generate an answer."
    sources = [{"chunk": chunk, "score": score} for chunk, score in results]
    return answer, sources


@router.post("/query", response_model=AIQueryResponse)
async def ai_query(
    payload: AIQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == payload.case_id,
            CaseMember.user_id == current_user.id,
        )
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not allowed in this case")

    await ensure_case_index(payload.case_id, db)

    try:
        answer, sources_raw = await asyncio.to_thread(
            generate_case_ai_reply_sync,
            payload.case_id,
            payload.question,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI request failed or timed out. Please try again.",
        ) from exc

    sources = [AISource(chunk=item["chunk"], score=item["score"]) for item in sources_raw]

    return AIQueryResponse(answer=answer, sources=sources)
