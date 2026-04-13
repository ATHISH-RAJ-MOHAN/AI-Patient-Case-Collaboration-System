from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db import get_db
from app.models import CaseMember, Message, PatientCase, User
from app.schemas import MessageCreate, MessageOut
from app.security import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(prefix = "/cases", tags=["Messages"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, case_id: int, websocket: WebSocket):
        await websocket.accept()

        if case_id not in self.active_connections:
            self.active_connections[case_id] = []
        self.active_connections[case_id].append(websocket)
    
    def disconnect(self, case_id: int, websocket:WebSocket):
        if case_id in self.active_connections:
            if websocket in self.active_connections[case_id]:
                self.active_connections[case_id].remove(websocket)
            if not self.active_connections[case_id]:
                del self.active_connections[case_id]
    
    async def broadcast(self, case_id: int, message:dict):
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

async def get_user_from_token(token: str, db:AsyncSession):
    credentials_exc = HTTPException(status_code=401, detail = "Could not validate credentials")

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


async def _ensure_case_member(case_id:int, user_id:int, db:AsyncSession):
    result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == user_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code = 403, detail = "You are not a member of this case")

@router.post("/{case_id}/messages", response_model = MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    case_id:int,
    payload:MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
    case_obj = case_result.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(status_code = 404, detail = "Case not found")
    
    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == current_user.id
        )
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail = "You are not a member of this case")
    
    new_message = Message(
        case_id = case_id,
        sender_id = current_user.id,
        message_type = payload.message_type,
        content = payload.content,
        reply_to_id = payload.reply_to_id,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

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
        raise HTTPException(status_code = 404, detail = "Case not found")
    
    member_result = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == current_user.id,
        )
    )

    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail = "You are not a member of this case")

    result = await db.execute(
        select(Message)
        .where(Message.case_id == case_id)
        .order_by(Message.sent_at.asc())
    )

    messages = result.scalars().all()
    return messages

# Web Socket_end_point
@router.websocket("/ws/cases/{case_id}")
async def websocket_case_chat(websocket: WebSocket, case_id:int):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    async for db in get_db():
        current_user = await get_user_from_token(token, db)

        case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
        case_obj = case_result.scalar_one_or_none()

        if not case_obj:
            await websocket.close(code = 1008)
            return
        
        member_result = await db.execute(
            select(CaseMember).where(CaseMember.case_id == case_id, CaseMember.user_id == current_user.id),
        )
        if not member_result.scalar_one_or_none():
            await websocket.close(code = 1008)
            return
        
        await manager.connect(case_id, websocket)

        try:
            while True:
                data = await websocket.receive_json()

                content = data.get("content")
                if not content:
                    await websocket.send_json({"error":"content is required"})
                    continue
                    
                message_type = data.get("message_type", "text")
                reply_to_id = data.get("reply_to_id")

                new_message = Message(
                    case_id = case_id,
                    sender_id = current_user.id,
                    message_type = message_type,
                    content = content,
                    reply_to_id = reply_to_id
                )

                db.add(new_message)
                await db.commit()
                await db.refresh(new_message)

                message_data = MessageOut.model_validate(new_message).model_dump(mode = "json")

                await manager.broadcast(
                    case_id,
                    {
                        "type" : "new_message",
                        "data": message_data
                    },
                )

        except WebSocketDisconnect:
            manager.disconnect(case_id, websocket)
        
