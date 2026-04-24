from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.db import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut, UserSearchOut
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    bearer_scheme,
    SECRET_KEY,
    ALGORITHM,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# Signup
@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)):

    # Check if user already exists
    stmt = select(User).where(User.email == payload.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    new_user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


# Login
@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {"access_token": token, "token_type": "bearer"}


# Logout
@router.post("/logout")
async def logout():
    return {"messages":"Logged out successfully"}


@router.get("/users/search", response_model=list[UserSearchOut])
async def search_users(
    q: str = Query("", description="Search by user name or email"),
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    search_term = q.strip().lower()
    if len(search_term) < 2:
        return []

    pattern = f"%{search_term}%"
    result = await db.execute(
        select(User)
        .where(
            User.is_active.is_(True),
            User.id != current_user.id,
            or_(
                func.lower(User.full_name).like(pattern),
                func.lower(User.email).like(pattern),
            ),
        )
        .order_by(User.full_name.asc())
        .limit(limit)
    )

    return result.scalars().all()


# Current User
@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
