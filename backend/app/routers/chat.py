from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from openai import OpenAI
import os
import asyncio

from app.db import get_db
from app.models import CaseMember, Message, PatientCase, User
from app.schemas import MessageCreate, MessageOut
from app.security import get_current_user, SECRET_KEY, ALGORITHM
from app.ai.embeddings import get_embedding
from app.ai.faiss_store import search

router = APIRouter(prefix="/cases", tags=["Messages"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, case_id: int, websocket: WebSocket):
        await websocket.accept()

        if case_id not in self.active_connections:
            self.active_connections[case_id] = []
        self.active_connections[case_id].append(websocket)

    def disconnect(self, case_id: int, websocket: WebSocket):
        if case_id in self.active_connections:
            if websocket in self.active_connections[case_id]:
                self.active_connections[case_id].remove(websocket)
            if not self.active_connections[case_id]:
                del self.active_connections[case_id]

    async def broadcast(self, case_id: int, message: dict):
        if case_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[case_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)

            for connection in dead_connections:
                self.disconnect(case_id, connection)


manager = ConnectionManager()


async def get_user_from_token(token: str, db: AsyncSession):
    credentials_exc = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exc

    return user


async def _ensure_case_member(case_id: int, user_id: int, db: AsyncSession):
    result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == user_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this case")


def should_ai_respond(content: str) -> bool:
    if not content:
        return False
    msg = content.strip().lower()
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


def generate_case_ai_reply_sync(case_id: int, question: str) -> str:
    """
    Synchronous helper so the OpenAI call does not block the event loop.
    """
    query_embedding = get_embedding(question)
    if not query_embedding:
        return "I could not process the question right now."

    results = search(case_id, query_embedding, top_k=5)
    if not results:
        return "I could not find any relevant information in this case yet."

    context = "\n".join([f"- {chunk}" for chunk, _score in results])

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    return response.choices[0].message.content or "I could not generate an answer."


async def generate_case_ai_reply(case_id: int, question: str) -> str:
    return await asyncio.to_thread(generate_case_ai_reply_sync, case_id, question)


async def save_message(
    db: AsyncSession,
    case_id: int,
    sender_id: int,
    message_type: str,
    content: str,
    reply_to_id: int | None = None,
) -> Message:
    new_message = Message(
        case_id=case_id,
        sender_id=sender_id,
        message_type=message_type,
        content=content,
        reply_to_id=reply_to_id,
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message


@router.post("/{case_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    case_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
    case_obj = case_result.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")

    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == current_user.id,
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this case")

    new_message = await save_message(
        db=db,
        case_id=case_id,
        sender_id=current_user.id,
        message_type=payload.message_type,
        content=payload.content,
        reply_to_id=payload.reply_to_id,
    )

    await manager.broadcast(
        case_id,
        {
            "type": "new_message",
            "data": MessageOut.model_validate(new_message).model_dump(mode="json"),
        },
    )

    try:
        if should_ai_respond(payload.content):
            question = strip_ai_prefix(payload.content)
            ai_text = await generate_case_ai_reply(case_id, question)

            ai_reply = await save_message(
                db=db,
                case_id=case_id,
                sender_id=current_user.id,
                message_type="ai",
                content=ai_text,
                reply_to_id=new_message.id,
            )

            await manager.broadcast(
                case_id,
                {
                    "type": "new_message",
                    "data": MessageOut.model_validate(ai_reply).model_dump(mode="json"),
                },
            )
    except Exception as e:
        print(f"[AI ERROR] {e}")

    return new_message


@router.get("/{case_id}/messages", response_model=list[MessageOut])
async def get_case_messages(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
    case_obj = case_result.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")

    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == current_user.id,
        )
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this case")

    result = await db.execute(
        select(Message)
        .where(Message.case_id == case_id)
        .order_by(Message.sent_at.asc())
    )

    return result.scalars().all()


@router.websocket("/ws/cases/{case_id}")
async def websocket_case_chat(websocket: WebSocket, case_id: int):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    async for db in get_db():
        current_user = await get_user_from_token(token, db)

        case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
        case_obj = case_result.scalar_one_or_none()

        if not case_obj:
            await websocket.close(code=1008)
            return

        member_result = await db.execute(
            select(CaseMember).where(
                CaseMember.case_id == case_id,
                CaseMember.user_id == current_user.id,
            )
        )
        if not member_result.scalar_one_or_none():
            await websocket.close(code=1008)
            return

        await manager.connect(case_id, websocket)

        try:
            while True:
                try:
                    data = await websocket.receive_json()

                    content = data.get("content")
                    if not content:
                        await websocket.send_json({"error": "content is required"})
                        continue

                    message_type = data.get("message_type", "text")
                    reply_to_id = data.get("reply_to_id")

                    user_message = await save_message(
                        db=db,
                        case_id=case_id,
                        sender_id=current_user.id,
                        message_type=message_type,
                        content=content,
                        reply_to_id=reply_to_id,
                    )

                    await manager.broadcast(
                        case_id,
                        {
                            "type": "new_message",
                            "data": MessageOut.model_validate(user_message).model_dump(mode="json"),
                        },
                    )

                    try:
                        if should_ai_respond(content):
                            question = strip_ai_prefix(content)
                            ai_text = await generate_case_ai_reply(case_id, question)

                            ai_message = await save_message(
                                db=db,
                                case_id=case_id,
                                sender_id=current_user.id,
                                message_type="ai",
                                content=ai_text,
                                reply_to_id=user_message.id,
                            )

                            await manager.broadcast(
                                case_id,
                                {
                                    "type": "new_message",
                                    "data": MessageOut.model_validate(ai_message).model_dump(mode="json"),
                                },
                            )
                    except Exception as e:
                        print(f"[AI ERROR] {e}")
                        try:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": "AI reply failed",
                                }
                            )
                        except Exception:
                            pass

                except Exception as e:
                    print(f"[WEBSOCKET LOOP ERROR] {e}")
                    try:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": "Message processing failed",
                            }
                        )
                    except Exception:
                        pass

        except WebSocketDisconnect:
            manager.disconnect(case_id, websocket)
            break