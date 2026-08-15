"""FastAPI app factory."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.routers.all_routers import (
    meta_router, proc_router, job_router,
    portfolio_router, rubric_router, evidence_router,
    compare_router, ask_router,
)
import logging, os

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Load corpus on startup (skip if already loaded)
    try:
        from app.db import SessionLocal
        from app.corpus.loader import load_corpus
        from app.config import get_settings
        s = get_settings()
        db = SessionLocal()
        from app.models import Source
        if db.query(Source).count() == 0:
            corpus_dir = os.path.join(os.path.dirname(__file__), "corpus")
            load_corpus(db, corpus_dir, embed=s.embed_corpus)
        db.close()
    except Exception as e:
        logging.warning(f"Corpus load skipped: {e}")
    yield


app = FastAPI(title="Process Intelligence Engine", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router)
app.include_router(proc_router)
app.include_router(job_router)
app.include_router(portfolio_router)
app.include_router(rubric_router)
app.include_router(evidence_router)
app.include_router(compare_router)
app.include_router(ask_router)
