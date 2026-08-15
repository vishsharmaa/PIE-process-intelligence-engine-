# Process Intelligence Engine (PIE)

> **Enterprise AI Build Challenge — Process Intelligence Engine**  
> *Converts unstructured business process descriptions into structured, evidence-backed transformation intelligence.*

---

## 🏛️ Architectural Core Principle

> **"AI interprets. Deterministic software decides."**

The Process Intelligence Engine strictly separates non-deterministic AI interpretation from deterministic decision-making:

- **LLM (Groq / Llama 3):** Extracts bounded ordinal feature ratings (1–5), factual claims, and classifies natural language query intents. It **never** computes final scores or determines rankings.
- **Deterministic Python Engine:** Computes normalized feature values, signed contributions, total scores, decision bands, override rules, verbatim quote verifications, and executes whitelisted parameterized SQL.

---

## 📦 Stage 2 Submission Pack

All Stage 2 evaluation artifacts are organized in the [`submission/`](submission/) directory:

- **Architecture Diagrams:**
  - [System Architecture Diagram (PDF)](submission/architecture/system-architecture.pdf) | [PNG](submission/architecture/system-architecture.png)
  - [AI Architecture Diagram (PDF)](submission/architecture/ai-architecture.pdf) | [PNG](submission/architecture/ai-architecture.png)
  - [Database ER Diagram (PDF)](submission/architecture/database-er-diagram.pdf) | [PNG](submission/architecture/database-er-diagram.png)
- **Technical & API Documentation:**
  - [Technical Architecture Document (PDF)](submission/documentation/technical-documentation.pdf) | [Markdown](submission/documentation/technical-documentation.md)
  - [API Documentation](submission/documentation/api-documentation.md)
- **Form Answers & Verification:**
  - [Stage 2 Form Answers (Q16–Q56)](submission/form/stage2-answers.md) | [Plain Text](submission/form/stage2-answers.txt)
  - [Production Verification Report](submission/deployment/production-verification.md)
  - [Production Deployment Guide](submission/deployment/deployment-guide.md)
  - [Video Presentation & Demo Script](submission/video/demo-script.md)
  - [Submission Checklist](submission/SUBMISSION_CHECKLIST.md)
  - [Final Submission Report](submission/FINAL_SUBMISSION_REPORT.md)


---

## 🏗️ Tech Stack & Constraints

- **Backend:** Python 3.9+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Database:** PostgreSQL 16 with `pgvector` extension (single database architecture)
- **AI / LLM:** Groq API (`llama3-8b-8192`) — free tier compliant
- **Embeddings:** Local `sentence-transformers/all-mpnet-base-v2` (768-dimensional, zero API cost)
- **Frontend:** React 18, TypeScript, Vite, TanStack Query, Recharts, Vanilla CSS Design System

---

## 🚀 Quickstart

### 1. Prerequisites

Ensure you have Docker and Python 3.9+ installed:
```bash
docker --version
python3 --version
```

### 2. Start PostgreSQL with pgvector

```bash
cd backend
docker compose up -d
```

### 3. Setup Python Virtual Environment & Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy `.env.example` to `.env` and fill in your Groq API key:
```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run Database Migrations

```bash
python3 scripts/migrate.py
```
*(Or if alembic is on your PATH: `alembic upgrade head`)*

### 6. Seed 100 Process Descriptions & Run Pipeline

```bash
python scripts/seed.py
```
*Note: To test without database writes or LLM calls, run `python scripts/seed.py --dry-run`.*

### 7. Run Backend API Server

```bash
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 8. Run Frontend App

In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## ⚙️ The 9-Stage Ingestion & Intelligence Pipeline

Every process description flows sequentially through `app/pipeline/runner.py`:

```
┌────────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌────────────┐
│ 1.Validate │──>│2.Normalize│──>│ 3. Dedup  │──>│4. Extract │──>│ 5. Feature │
└────────────┘   └───────────┘   └───────────┘   └───────────┘   └────────────┘
                                                                        │
┌────────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐          │
│9.Portfolio │<──│ 8.Persist │<──│  7.Score  │<──│6. Research│<─────────┘
└────────────┘   └───────────┘   └───────────┘   └───────────┘
```

1. **Validate:** Ensures non-empty name and minimum description length.
2. **Normalize:** Lowercases text, collapses whitespace, strips non-printable characters.
3. **Dedup:** Computes SHA-256 hash of normalized text. Skips processing if content hash already exists.
4. **Extract (LLM):** Invokes Groq with structured JSON schema (`ExtractionResult`) to rate 8 factors (1–5) and extract 3–5 verifiable claims.
5. **Feature:** Normalizes ordinal ratings `(1–5)` to `(0.0–1.0)` and persists `ProcessFeature` records.
6. **Research (RAG):** For each claim, embeds claim text, searches corpus chunks using vector similarity, extracts verbatim quotes, and verifies substring existence.
7. **Score (Deterministic):** Evaluates `rubric_v1.yaml` using `compute_score()`. Calculates signed factor contributions and total score.
8. **Persist:** Updates process status to `completed` and links all generated child entities.
9. **Portfolio:** Recomputes overall portfolio rankings and percentiles across all scored processes.

---

## 📐 Deterministic Scoring Engine Mechanics

Driven by `app/scoring/rubric_v1.yaml` and `app/scoring/engine.py`:

### Invariant Equation
$$\text{Total Score} = \sum_{f \in \text{Factors}} \text{Contribution}_f$$

- Each factor has a weight $w_f \in [0, 1]$ where $\sum w_f = 1.0$.
- Normalized value $v_f = \frac{\text{ordinal} - 1}{4} \in [0, 1]$.
- **Driver factors (+):** $\text{Contribution} = v_f \times w_f \times 100$.
- **Constraint factors (-):** $\text{Contribution} = -(1 - v_f) \times w_f \times 100$.

### Decision Bands
- **Automate:** Total Score $\ge 70.0$
- **Augment:** Total Score $\ge 45.0$ and $< 70.0$
- **Human-Led:** Total Score $< 45.0$

### Safety Override Rule
If `regulatory_safety_constraint == 5` AND `human_judgment_dependency >= 4`, the decision band is automatically capped at **Augment**, regardless of how high the numerical score is.

---

## 💬 Natural Language Querying (Ask PIE)

Natural language questions (`POST /api/ask`) do **not** use risky text-to-SQL generation. Instead:

1. **Intent Classification:** Groq classifies the question into one of 5 whitelisted intents:
   - `top_n_candidates`
   - `band_filter`
   - `explain_score`
   - `portfolio_stats`
   - `unmappable`
2. **Query Plan Building:** A strongly typed `QueryPlan` Pydantic object is instantiated with validated parameters.
3. **Whitelisted Execution:** `app/query/executors.py` maps the `QueryPlan` to explicit, parameterized SQLAlchemy queries.

---

## 🧪 Automated Testing

Run all 45 automated unit and integration tests:

```bash
cd backend
python3 -m pytest tests/ -v
```

Tests cover:
- Deterministic scoring invariants & override rules
- Whitespace/punctuation normalization & SHA-256 deduplication
- Verbatim quote substring verification & edge cases
- Strongly typed `QueryPlan` parameter bounds
- Seed YAML 100-process integrity & unique content hashes
- Input validation & Pydantic schema constraints

---

## 🖥️ Frontend Overview

Built with Vite, React, TypeScript, TanStack Query, and a dark enterprise CSS design system:

- `/#/dashboard` — High-level portfolio statistics, band distribution pie chart, score histogram, top/bottom processes.
- `/#/processes` — Filterable/sortable table with search, band chips, and pagination.
- `/#/process/:id` — Score waterfall chart, feature rationale table, claim-to-source evidence verification chain.
- `/#/portfolio` — Complete ranked list with percentiles and score comparisons.
- `/#/ingest` — **Process 101** dynamic ingestion form with real-time 9-stage pipeline progress polling.
- `/#/ask` — Natural language query interface showing structured response and debug QueryPlan.
- `/#/methodology` — Interactive documentation of rubric weights, bands, override rules, and AI vs. deterministic roles.

---

## 📄 License

MIT License — MODUS Enterprise AI Build Challenge.
