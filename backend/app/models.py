from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, func, text
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key= True, autoincrement=True, index = True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable = False, unique=True, index = True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable = False, server_default=text('"doctor"'))
    is_active = Column(Boolean, nullable = False, server_default = text("1"))
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default = func.current_timestamp(), onupdate=func.current_timestamp())


