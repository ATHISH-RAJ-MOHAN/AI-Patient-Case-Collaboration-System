import os
import uuid

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User


# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))  # 30 days


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    to_encode = data.copy()
    to_encode["jti"] = str(uuid.uuid4()) # unique token Id - needed for logging out
    
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# HTTP Bearer Auth 
bearer_scheme = HTTPBearer()

# Current User Dependency
async def get_current_user(
    token=Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    # Extract raw JWT string
    token = token.credentials

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        jti = payload.get("jti")

        if user_id is None or jti is None:
            raise credentials_exc

    except JWTError:
        raise credentials_exc
    
    '''
    # Check blacklist
    result = await db.execute(
        select(TokenBlackList).where(TokenBlackList.jti == jti)

    )

    blacklisted = result.scalar_one_or_none()

    if blacklisted:
        raise credentials_exc
    '''
    
    # Load user from DB
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exc

    return user