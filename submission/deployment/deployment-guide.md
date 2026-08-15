# 🚀 Process Intelligence Engine (PIE) — Deployment Guide

> **Target Architecture:**  
> • **Frontend:** Vercel (SPA / Static Hosting)  
> • **Backend:** Render / Railway / AWS ECS (FastAPI Container or Web Service)  
> • **Database:** Neon / Supabase / AWS RDS (Managed PostgreSQL 16 with `pgvector`)  
> • **LLM Provider:** Groq Cloud API (`llama-3.1-8b-instant`)  

---

## 🏗️ Deployment Architecture Topology

```
┌──────────────────────────────────────┐
│  Vercel (React 18 + Vite SPA)        │
│  https://pie-frontend.vercel.app     │
└──────────────────────────────────────┘
                   │
                   │ HTTPS API Requests (VITE_API_BASE)
                   ▼
┌──────────────────────────────────────┐
│  Render / Web Service (FastAPI)      │
│  https://pie-backend.onrender.com    │
└──────────────────────────────────────┘
         │                   │
         │ SQL (pgvector)    │ HTTPS JSON (API Key)
         ▼                   ▼
┌────────────────────┐  ┌───────────────────────────┐
│ Managed PostgreSQL │  │ Groq Cloud API            │
│ Neon / Supabase    │  │ (llama-3.1-8b-instant)    │
│ (pgvector ext)     │  └───────────────────────────┘
└────────────────────┘
```

---

## 📋 Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Description | Example / Default | Required |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URI with `postgresql+psycopg2://` driver | `postgresql+psycopg2://pie:pie@db.neon.tech:5432/pie?sslmode=require` | **Yes** |
| `GROQ_API_KEY` | Groq Cloud API Key for LLM feature extraction & intent routing | `gsk_xxxxxxxxxxxxxxxxxxxxxxxx` | **Yes** |
| `GROQ_MODEL` | Groq LLM model name | `llama-3.1-8b-instant` | No (defaults to `llama-3.1-8b-instant`) |
| `EMBEDDING_MODEL` | Local sentence-transformers model | `all-mpnet-base-v2` | No (defaults to `all-mpnet-base-v2`) |
| `EXTRACTION_CACHE_DIR` | Directory for on-disk extraction cache | `.cache/extractions` | No |
| `CORPUS_DIR` | Directory containing ground-truth markdown reference docs | `app/corpus` | No |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | No |

### Frontend (`frontend/.env.production`)

| Variable | Description | Example | Required |
|---|---|---|---|
| `VITE_API_BASE` | Public URL of the deployed FastAPI backend | `https://pie-backend.onrender.com` | **Yes** |

---

## 🛠️ Step-by-Step Deployment Procedure

### Step 1: Provision Managed PostgreSQL with `pgvector`

1. **Option A: Neon Serverless PostgreSQL (Recommended)**
   - Go to [Neon.tech](https://neon.tech) and create a new project `pie-db`.
   - In the SQL Editor, verify or enable pgvector:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
   - Copy the Connection String (use `Pooled connection` string with `sslmode=require`).
   - Format for SQLAlchemy:  
     `postgresql+psycopg2://<user>:<password>@<host>/<database>?sslmode=require`

2. **Option B: Supabase**
   - Create a project on [Supabase.com](https://supabase.com).
   - Go to **Database > Extensions** and search for `vector`. Toggle it **ON**.
   - Copy the direct connection string (URI mode, port 5432 or 6543 pooler).

---

### Step 2: Deploy Backend to Render

1. Create an account on [Render.com](https://render.com).
2. Click **New + > Web Service** and connect your GitHub repository: `https://github.com/vishsharmaa/PIE-process-intelligence-engine-`.
3. Configure the service settings:
   - **Name:** `pie-backend`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Region:** `Oregon (US West)` or `Frankfurt (EU Central)`
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python scripts/migrate.py
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
4. Under **Advanced > Environment Variables**, add:
   - `DATABASE_URL`: *(Your Neon/Supabase PostgreSQL connection URI)*
   - `GROQ_API_KEY`: *(Your Groq API key `gsk_...`)*
   - `PYTHON_VERSION`: `3.10.12`
   - `LOG_LEVEL`: `INFO`
5. Click **Deploy Web Service**.
6. Once deployed, verify the health endpoint in your browser:
   `https://pie-backend.onrender.com/health` $\rightarrow$ `{"status": "ok", "db": "connected"}`

---

### Step 3: Run Database Migrations & Initial Corpus Load

When `python scripts/migrate.py` executes, it applies Alembic revision `001_initial`:
- Creates `vector` extension.
- Creates all 11 tables: `process`, `extraction_run`, `process_feature`, `score`, `score_factor`, `claim`, `evidence`, `source`, `source_chunk`, `process_rank`, `job`, `query_log`, `rubric_version`.
- On server startup (`app/main.py`), the `lifespan` handler checks if `source` is empty and automatically chunks, embeds, and indexes all 25 industrial corpus documents.

---

### Step 4: Seed the 100 Process Portfolio Dataset

To populate the database with the pre-extracted, scored, and verified 100-process dataset:

1. **Option A: Run from your local terminal targeting the production DB:**
   ```bash
   cd backend
   DATABASE_URL="postgresql+psycopg2://<user>:<password>@<host>/<database>?sslmode=require" \
   GROQ_API_KEY="gsk_..." \
   python scripts/seed.py --delay 1.0
   ```
2. **Option B: Run inside Render SSH Shell:**
   ```bash
   python scripts/seed.py --delay 1.0
   ```
3. Verify portfolio summary via API:
   `GET https://pie-backend.onrender.com/api/portfolio/summary`
   Confirm `total: 100`, `band_counts`, and non-empty `top_processes`.

---

### Step 5: Deploy Frontend to Vercel

1. Create an account on [Vercel.com](https://vercel.com).
2. Click **Add New... > Project** and import the GitHub repository.
3. In the project configuration:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE`: `https://pie-backend.onrender.com`
5. Click **Deploy**.
6. Test the live production URL (e.g., `https://pie-frontend.vercel.app`).

---

## 🔍 Verification & Smoke Test Checklist

After deployment, execute the following smoke tests:

- [ ] **Health Check:** Open `https://pie-backend.onrender.com/health` $\rightarrow$ returns `{"status":"ok","db":"connected"}`.
- [ ] **OpenAPI Documentation:** Open `https://pie-backend.onrender.com/docs` $\rightarrow$ Swagger UI renders all 11 endpoints.
- [ ] **Dashboard:** Open Vercel URL $\rightarrow$ Portfolio KPIs (100 processes, average score, band pie chart) render immediately.
- [ ] **Process List:** Navigate to `/processes` $\rightarrow$ Table displays 100 sorted processes with search and band filters.
- [ ] **Process Detail & Waterfall:** Click into Process #1 $\rightarrow$ Score waterfall chart and verified quote trust chains display.
- [ ] **Natural Language Query (Ask PIE):** Navigate to `/ask`, query `"Show top 5 automation candidates"` $\rightarrow$ Returns structured table, QueryPlan debug, and prose explanation.
- [ ] **Process 101 Ingestion:** Navigate to `/ingest`, submit a new process $\rightarrow$ Progress bar transitions 5% to 100%, and new process joins the portfolio.
