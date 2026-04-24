from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "doctor"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserSearchOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CaseCreate(BaseModel):
    patient_code: str
    case_title: str


class CaseOut(BaseModel):
    id: int
    patient_code: str
    case_title: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class CaseSummaryOut(BaseModel):
    id: int
    patient_code: str
    case_title: str
    status: str
    member_count: int = 0
    document_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_message: str | None = None
    last_message_at: datetime | None = None
    last_message_sender_id: int | None = None
    last_message_type: str | None = None


class CaseMemberCreate(BaseModel):
    user_id: int
    member_role: str = "doctor"


class CaseMemberOut(BaseModel):
    id: int
    case_id: int
    user_id: int
    member_role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseMemberUserOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: str
    member_role: str
    joined_at: datetime


class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    reply_to_id: int | None = None


class MessageOut(BaseModel):
    id: int
    case_id: int
    sender_id: int
    message_type: str
    content: str
    reply_to_id: int | None = None
    sent_at: datetime
    edited_at: datetime | None = None
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(BaseModel):
    id: int
    case_id: int
    uploaded_by: int
    file_name: str
    file_type: str
    file_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIQueryRequest(BaseModel):
    case_id: int
    question: str


class AISource(BaseModel):
    chunk: str
    score: float


class AIQueryResponse(BaseModel):
    answer: str
    sources: List[AISource] = Field(default_factory=list)
