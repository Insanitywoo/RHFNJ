from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil

from app.core.config import settings
from app.api import chat
from app.services.pdf_processor import index_pdf, get_vector_db


PAPERS_DIR = "data/papers"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("RHFNJ is starting...")

    os.makedirs(PAPERS_DIR, exist_ok=True)
    print(f"Created {PAPERS_DIR} directory")

    yield
    print("RHFNJ is shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/files/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_path = os.path.join(PAPERS_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        vector_db = get_vector_db()
        existing = vector_db.similarity_search("dummy", k=1)

        index_pdf(file_path)

        return JSONResponse(
            {
                "status": "success",
                "filename": file.filename,
                "message": "File uploaded and indexed successfully",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index file: {str(e)}")
