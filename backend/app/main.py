from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # noqa: F401  — register models so create_all sees them
from .routers import auth as auth_router
from .routers import admin as admin_router
from .routers import fill as fill_router
from .routers import approve as approve_router
from .routers import data as data_router
from .routers import export as export_router
from .routers import wework as wework_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="风险资产压降填报系统")

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(fill_router.router)
app.include_router(approve_router.router)
app.include_router(data_router.router)
app.include_router(export_router.router)
app.include_router(wework_router.router)

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
