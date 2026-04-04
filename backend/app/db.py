import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# LOAD database url
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL does not exists")

# ESTABLISH CONNECTION with the database
engine = create_async_engine(DATABASE_URL, echo = True, pool_pre_ping = True)

# database session for each request
SessionLocal = async_sessionmaker(bind = engine, class_= AsyncSession, expire_on_commit=False)

# Base class for sql alchemy models 
Base = declarative_base()

# Each request must open a session and close it automatically, Since FastAPI uses dependency injection, use a generator function with yield
async def get_db():
    async with SessionLocal() as session:
        yield session 