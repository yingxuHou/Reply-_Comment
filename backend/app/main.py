from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import create_db_and_tables
from app.modules.kb.router import router as kb_router
from app.modules.leads.router import router as leads_router
from app.modules.monitor.router import router as monitor_router
from app.modules.reply.router import router as reply_router
from app.modules.vector.router import router as vector_router
from app.modules.xhs.router import router as xhs_router


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _on_startup() -> None:
    create_db_and_tables()


@app.get("/healthz")
def healthz():
    return {"ok": True}


app.include_router(kb_router, prefix="/api")
app.include_router(vector_router, prefix="/api")
app.include_router(reply_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(monitor_router, prefix="/api")
app.include_router(xhs_router, prefix="/api")

