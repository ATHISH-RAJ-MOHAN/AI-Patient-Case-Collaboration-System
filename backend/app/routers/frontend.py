import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(include_in_schema=False)

APP_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
ASSET_VERSION = "20260420a"


def build_template_context(request: Request, title: str, page: str, auth_mode: str | None = None) -> dict:
    return {
        "request": request,
        "title": title,
        "page": page,
        "auth_mode": auth_mode,
        "asset_version": ASSET_VERSION,
        "frontend_api_base_url": os.getenv("FRONTEND_API_BASE_URL", "").rstrip("/"),
    }


@router.get("/app", response_class=HTMLResponse)
async def app_shell(request: Request):
    return templates.TemplateResponse(
        request,
        "app.html",
        build_template_context(request, "CareCollab Workspace", "app"),
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        build_template_context(request, "Sign In | CareCollab", "auth", auth_mode="login"),
    )


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        request,
        "signup.html",
        build_template_context(request, "Create Account | CareCollab", "auth", auth_mode="signup"),
    )
