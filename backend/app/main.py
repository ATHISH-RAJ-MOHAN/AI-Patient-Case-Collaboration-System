from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.routers.auth import router as auth_router

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
