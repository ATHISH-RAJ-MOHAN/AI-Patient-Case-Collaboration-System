from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "doctor"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id:int
    full_name:str
    email:EmailStr
    role:str
    is_active:bool
    created_at:datetime
    updated_at:datetime | None = None 

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CaseCreate(BaseModel):
    patient_code: str
    case_title: str

class CaseOut(BaseModel):
    id:int
    patient_code:str
    case_title:str
    status:str

    model_config = ConfigDict(from_attributes=True)

class CaseMemberCreate(BaseModel):
    user_id:int
    member_role: str = "doctor"

class CaseMemberOut(BaseModel):
    id:int
    case_id:int
    user_id:int
    member_role:str
    joined_at:datetime

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes = True)