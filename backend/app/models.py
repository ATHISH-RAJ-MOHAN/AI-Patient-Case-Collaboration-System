from sqlalchemy import BigInteger, Text, Boolean, Column, DateTime, ForeignKey, String, func, text
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key= True, autoincrement=True, index = True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable = False, unique=True, index = True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable = False, server_default=text("'doctor'"))
    is_active = Column(Boolean, nullable = False, server_default = text("1"))
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default = func.current_timestamp(), onupdate=func.current_timestamp())

class PatientCase(Base):
    __tablename__ = "patient_cases"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index = True)
    patient_code = Column(String(100), nullable=False, unique=True, index=True)
    case_title = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, server_default=text("'open'"))
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class CaseMember(Base):
    __tablename__ = "case_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    case_id = Column(BigInteger, ForeignKey("patient_cases.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    member_role = Column(String(50), nullable=False)
    joined_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key = True, autoincrement=True)
    case_id = Column(BigInteger, ForeignKey("patient_cases.id"), nullable = False)
    sender_id = Column(BigInteger, ForeignKey("users.id"), nullable = False)
    message_type = Column(String(20), nullable=False, server_default=text("'text'"))
    content = Column(Text, nullable = False)
    reply_to_id = Column(BigInteger, nullable=True)
    sent_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    edited_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False, server_default=text("0"))

