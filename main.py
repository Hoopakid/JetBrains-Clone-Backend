from fastapi import FastAPI, APIRouter

from auth.auth import register_router

app = FastAPI(title='JetBrains', version='1.0.0')
router = APIRouter()

app.include_router(register_router)
