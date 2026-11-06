from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .vqa.router import router as vqa_router

app = FastAPI(title="EyeAssist API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(vqa_router)
