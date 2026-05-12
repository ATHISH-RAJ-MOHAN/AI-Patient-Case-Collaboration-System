from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os

from app.db import get_db
from app.routers.ai import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.cases import router as cases_router
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.frontend import router as frontend_router

load_dotenv()

app = FastAPI(title="Healthcare Group Chat API")

# Since FrontEnd will call backend we need middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(ai_router)
app.include_router(frontend_router)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
BASE_DIR = APP_DIR
UPLOAD_DIR = BASE_DIR.parent.parent / "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "Backend is running",
        "frontend_url": "/app",
    }

@app.get("/.well-known/assetlinks.json")
def assetlinks():
    return FileResponse("app/static/.well-known/assetlinks.json", media_type="application/json")

