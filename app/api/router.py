from fastapi import APIRouter

from app.api.routes import chat, documents, health


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/files", tags=["documents"])
api_router.include_router(chat.router, tags=["chat"])
