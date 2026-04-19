from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from app.routers.auth import router as auth_router
from app.routers.cases import router as cases_router 
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.ai import router as ai_router

from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title = "Healthcare Group Chat API")

# Since FrontEnd will call backend we need middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
) 

app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(ai_router)


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR.parent.parent / "uploads"

os.makedirs(UPLOAD_DIR, exist_ok = True)
app.mount("/uploads", StaticFiles(directory = str(UPLOAD_DIR)), name="uploads")

@app.get('/')
async def root():
    return {"message":"Backend is running"}

# create a route
@app.get("/health_check-db") # this is an endpoint to test the database connection
# Inject DB Session
async def health_check_db(db: AsyncSession = Depends(get_db)):

    # run sql -- sqlalchemy uses text() for raw SQL, AsyncSession uses await db.execute()
    result = await db.execute(text("SELECT 1"))

    # return result
    return {"status":"connected", "result": result.scalar()}
