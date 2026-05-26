from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # noqa: F401  — register models so create_all sees them
from .routers import auth as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="风险资产压降填报系统")

app.include_router(auth_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
