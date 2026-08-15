# 📚 Process Intelligence Engine (PIE) — API Documentation

> **Version:** 1.0.0  
> **Base URL (Local):** `http://localhost:8000`  
> **Base URL (Production):** `https://pie-backend.onrender.com` *(configurable via `VITE_API_BASE`)*  
> **Interactive OpenAPI Docs:** `GET /docs` (Swagger UI), `GET /redoc` (ReDoc), `GET /openapi.json`  

---

## 🧭 Overview & Core Principles

The Process Intelligence Engine (PIE) exposes a high-performance REST API built on **FastAPI 0.111.0**, validated with **Pydantic v2**, and backed by **PostgreSQL 16 + pgvector**.

All data mutation endpoints strictly follow the design invariant:
- **AI Interprets:** Feature ratings (1–5) and factual claims extracted via bounded JSON schemas.
- **Deterministic Software Decides:** Numerical scoring, factor contributions, band assignments, and ranking percentiles computed via pure Python algorithms.
- **Whitelisted Query Execution:** Natural language querying (`/api/ask`) maps questions to strongly typed `QueryPlan` schemas and pre-compiled SQLAlchemy executors (zero dynamic raw text-to-SQL).

---

## 🗂️ API Catalog Summary

| Category | Method | Endpoint | Purpose |
|---|---|---|---|
| **System** | `GET` | `/health` | Service health & PostgreSQL connectivity verification |
| **Processes** | `GET` | `/api/processes` | Filterable, sortable, paginated process listing |
| **Processes** | `GET` | `/api/processes/{id}` | Deep process analysis (scores, waterfall factors, verified evidence) |
| **Processes** | `POST` | `/api/processes` | Asynchronous Process 101 ingestion & 9-stage pipeline trigger |
| **Processes** | `POST` | `/api/processes/{id}/rescore` | Deterministic rescoring under alternate rubric version |
| **Pipeline Jobs** | `GET` | `/api/jobs/{id}` | Real-time 9-stage execution progress & status polling |
| **Portfolio** | `GET` | `/api/portfolio/summary` | Aggregate portfolio statistics, band distribution & histogram |
| **Rubric** | `GET` | `/api/rubric/{version}` | Mathematical rubric weights, directions, and override rules |
| **Evidence & RAG** | `GET` | `/api/evidence/{claim_id}` | Ground-truth verification provenance & verbatim quote citation |
| **Comparison** | `POST` | `/api/compare` | Side-by-side comparative analysis of two processes |
| **Natural Language** | `POST` | `/api/ask` | Natural language querying via intent classification & QueryPlan |

---

## 📡 Detailed Endpoint Reference

### 1. System Health Check

#### `GET /health`
Verifies backend service availability and PostgreSQL connection.

- **Request Headers:** None
- **Query Parameters:** None
- **Response `200 OK`:**
```json
{
  "status": "ok",
  "db": "connected"
}
```
- **Error Response `200 OK (Degraded)`:**
```json
{
  "status": "error",
  "db": "could not connect to server: Connection refused"
}
```

---

### 2. List Processes

#### `GET /api/processes`
Retrieves a paginated list of completed processes with optional band filtering, department filtering, search, and sorting.

- **Query Parameters:**
  - `band` *(string, optional)*: Filter by decision band (`Automate`, `Augment`, `Human-Led`).
  - `department` *(string, optional)*: Filter by department (e.g., `Maintenance`, `Quality Assurance`, `Supply Chain`).
  - `search` *(string, optional)*: Case-insensitive substring search across process names.
  - `sort_by` *(string, optional, default: `"rank"`)*: Column to sort by (`rank`, `score`, `name`, `created_at`).
  - `sort_dir` *(string, optional, default: `"asc"`)*: Sort direction (`asc`, `desc`).
  - `offset` *(integer, optional, default: `0`)*: Pagination offset.
  - `limit` *(integer, optional, default: `50`, max: `200`)*: Page size.

- **Response `200 OK`:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Vibration-Based Bearing Failure Prediction",
      "department": "Maintenance",
      "industry": "Manufacturing",
      "status": "completed",
      "total_score": 82.5,
      "band": "Automate",
      "rank": 1,
      "percentile": 100.0,
      "created_at": "2026-08-15T06:00:00Z"
    }
  ],
  "total": 100,
  "offset": 0,
  "limit": 50
}
```

---

### 3. Get Process Detail

#### `GET /api/processes/{id}`
Returns full end-to-end intelligence for a single process: raw text, extracted factor ratings with rationales, deterministic score breakdown, signed waterfall contributions, and verified claim-to-evidence trust chains.

- **Path Parameters:**
  - `id` *(integer, required)*: The process database ID.

- **Response `200 OK`:**
```json
{
  "id": 1,
  "name": "Vibration-Based Bearing Failure Prediction",
  "raw_description": "Our CNC machining center spindle bearings are monitored with triaxial accelerometers sampling at 20kHz...",
  "department": "Maintenance",
  "industry": "Manufacturing",
  "status": "completed",
  "created_at": "2026-08-15T06:00:00Z",
  "features": [
    {
      "feature_key": "data_availability",
      "ordinal_value": 5,
      "normalized_value": 1.0,
      "rationale": "High-frequency 20kHz vibration sensor data is continuously streamed and logged to OSIsoft PI historian.",
      "confidence": 0.95
    },
    {
      "feature_key": "regulatory_safety_constraint",
      "ordinal_value": 1,
      "normalized_value": 0.0,
      "rationale": "Standard machine tool bearing monitoring without life-critical safety implications.",
      "confidence": 0.9
    }
  ],
  "score": {
    "id": 1,
    "rubric_version": "v1",
    "total_score": 82.5,
    "band": "Automate",
    "recommendation": "Automate",
    "recommendation_text": "This process is a strong candidate for automation. Score: 82.5/100. Key drivers: Data Availability (18.0pts), Process Repeatability (16.0pts), Volume/Frequency (12.0pts). Constraints: Human Judgment (9.6pts).",
    "computed_at": "2026-08-15T06:01:00Z",
    "factors": [
      {
        "factor_key": "data_availability",
        "feature_value": 5.0,
        "weight": 0.18,
        "contribution": 18.0,
        "direction": "+"
      },
      {
        "factor_key": "human_judgment_dependency",
        "feature_value": 2.0,
        "weight": 0.12,
        "contribution": 9.0,
        "direction": "-"
      }
    ]
  },
  "claims": [
    {
      "id": 101,
      "claim_text": "Vibration analysis at 20kHz enables early detection of bearing outer raceway defect frequencies (BPFO).",
      "claim_type": "factual",
      "supported": true,
      "evidence_items": [
        {
          "id": 501,
          "quote": "High-frequency accelerometer data captures characteristic bearing defect frequencies including ball pass frequency outer race (BPFO) weeks before thermal failure.",
          "verified": true,
          "verification_method": "exact_match",
          "source_chunk_id": 12,
          "chunk_text": "In rotating equipment health monitoring, high-frequency accelerometer data captures characteristic bearing defect frequencies including ball pass frequency outer race (BPFO) weeks before thermal failure...",
          "source_title": "ISO 13373-1: Condition Monitoring and Diagnostics of Machines — Vibration Condition Monitoring",
          "source_publisher": "International Organization for Standardization",
          "source_url": "https://www.iso.org/standard/39735.html",
          "source_year": 2022
        }
      ]
    }
  ],
  "rank": {
    "rank": 1,
    "percentile": 100.0,
    "rubric_version": "v1",
    "computed_at": "2026-08-15T06:02:00Z"
  }
}
```

- **Error `404 Not Found`:**
```json
{
  "detail": "Process not found"
}
```

---

### 4. Ingest New Process (Process 101)

#### `POST /api/processes`
Accepts an unstructured process description, performs SHA-256 deduplication, creates pending tracking entities, and dispatches the asynchronous 9-stage pipeline worker in a background task.

- **Request Body (`ProcessCreate`):**
```json
{
  "name": "Automated Automated Optical Inspection (AOI) for PCB Assembly",
  "raw_description": "Our SMT lines produce 10,000 PCB assemblies daily. High-resolution cameras capture top and bottom component placements after solder reflow. Operators currently inspect defect false-calls manually under microscopes. Inspection logs and historical defect images are cataloged in our MES database with component coordinates.",
  "department": "Quality Assurance",
  "industry": "Electronics Manufacturing",
  "external_key": "QA-AOI-001"
}
```

- **Response `202 Accepted`:**
```json
{
  "job_id": 101,
  "process_id": 101,
  "message": "Pipeline started."
}
```

- **Error `409 Conflict (Duplicate Content)`:**
```json
{
  "detail": {
    "message": "Duplicate process — identical content already exists.",
    "existing_process_id": 4,
    "existing_process_name": "Visual Quality Inspection for Printed Circuit Boards"
  }
}
```

---

### 5. Check Pipeline Job Progress

#### `GET /api/jobs/{job_id}`
Polls the execution state and stage-by-stage progress of an asynchronous pipeline run.

- **Path Parameters:**
  - `job_id` *(integer, required)*: The job tracking ID.

- **Response `200 OK`:**
```json
{
  "id": 101,
  "kind": "ingest",
  "target_process_id": 101,
  "status": "running",
  "stage": "research",
  "progress": 70.0,
  "error": null,
  "created_at": "2026-08-15T06:05:00Z",
  "finished_at": null
}
```
*Stage Progression:* `validate` (5%) → `normalize` (10%) → `extract` (20%) → `features` (40%) → `score` (55%) → `research` (70%) → `persist` (85%) → `portfolio` (95%) → `complete` (100%).

---

### 6. Portfolio Executive Summary

#### `GET /api/portfolio/summary`
Returns aggregate intelligence across all scored processes for the executive dashboard.

- **Query Parameters:**
  - `rubric_version` *(string, optional, default: `"v1"`)*: Rubric version to aggregate.

- **Response `200 OK`:**
```json
{
  "total": 100,
  "band_counts": [
    { "band": "Automate", "count": 42 },
    { "band": "Augment", "count": 38 },
    { "band": "Human-Led", "count": 20 }
  ],
  "top_processes": [
    { "id": 1, "name": "Vibration-Based Bearing Failure Prediction", "total_score": 82.5, "band": "Automate", "rank": 1 }
  ],
  "bottom_processes": [
    { "id": 98, "name": "Executive Root-Cause Disciplinary Review", "total_score": 28.4, "band": "Human-Led", "rank": 100 }
  ],
  "avg_score": 62.4,
  "score_distribution": [
    { "range": "0-10", "count": 0 },
    { "range": "10-20", "count": 2 },
    { "range": "20-30", "count": 7 },
    { "range": "30-40", "count": 11 },
    { "range": "40-50", "count": 18 },
    { "range": "50-60", "count": 20 },
    { "range": "60-70", "count": 22 },
    { "range": "70-80", "count": 14 },
    { "range": "80-90", "count": 6 },
    { "range": "90-100", "count": 0 }
  ]
}
```

---

### 7. Natural Language Querying (Ask PIE)

#### `POST /api/ask`
Answers business questions over the intelligence dataset without raw text-to-SQL risks.

- **Request Body (`AskRequest`):**
```json
{
  "question": "Which top 3 processes in the Maintenance department have the highest potential for automation?"
}
```

- **Response `200 OK`:**
```json
{
  "question": "Which top 3 processes in the Maintenance department have the highest potential for automation?",
  "intent": "rank_top",
  "query_plan": {
    "intent": "rank_top",
    "metric": null,
    "filters": {
      "band": "Automate"
    },
    "sort": "score_desc",
    "limit": 3,
    "target_process_id": null
  },
  "results": [
    {
      "id": 1,
      "name": "Vibration-Based Bearing Failure Prediction",
      "department": "Maintenance",
      "total_score": 82.5,
      "band": "Automate",
      "rank": 1,
      "percentile": 100.0
    },
    {
      "id": 14,
      "name": "Cooling Tower Pump Energy Optimization",
      "department": "Maintenance",
      "total_score": 80.2,
      "band": "Automate",
      "rank": 2,
      "percentile": 98.9
    },
    {
      "id": 6,
      "name": "Hydraulic Oil Contamination Monitoring",
      "department": "Maintenance",
      "total_score": 78.6,
      "band": "Automate",
      "rank": 3,
      "percentile": 97.9
    }
  ],
  "prose_explanation": "Based on our deterministic evaluation, the top 3 automation candidates in Maintenance are Vibration-Based Bearing Failure Prediction (82.5/100), Cooling Tower Pump Energy Optimization (80.2/100), and Hydraulic Oil Contamination Monitoring (78.6/100). All three exhibit rich data streams and standardized operational logic.",
  "unmappable": false
}
```

---

### 8. Compare Two Processes

#### `POST /api/compare`
Performs a factor-by-factor delta comparison between two scored processes.

- **Request Body:**
```json
{
  "process_ids": [1, 15]
}
```

- **Response `200 OK`:**
```json
{
  "processes": [
    { "id": 1, "name": "Vibration-Based Bearing Failure Prediction", "total_score": 82.5, "band": "Automate" },
    { "id": 15, "name": "Manual Heat Treatment Recipe Calibration", "total_score": 48.0, "band": "Augment" }
  ],
  "factor_comparisons": [
    {
      "factor_key": "data_availability",
      "direction": "+",
      "weight": 0.18,
      "values": { "1": 5.0, "15": 3.0 },
      "contributions": { "1": 18.0, "15": 9.0 }
    },
    {
      "factor_key": "human_judgment_dependency",
      "direction": "-",
      "weight": 0.12,
      "values": { "1": 2.0, "15": 4.0 },
      "contributions": { "1": 9.0, "15": 3.0 }
    }
  ],
  "score_delta": 34.5
}
```

---

### 9. Get Rubric Specification

#### `GET /api/rubric/{version}`
Returns the active rubric configuration loaded directly from YAML.

- **Path Parameters:**
  - `version` *(string, required, default: `"v1"`)*: Rubric version.

- **Response `200 OK`:**
```json
{
  "version": "v1",
  "factors": {
    "data_availability": { "direction": "+", "weight": 0.18, "description": "Availability of structured, machine-readable data" },
    "process_repeatability": { "direction": "+", "weight": 0.16, "description": "Degree of consistent repeatable pattern" },
    "rule_clarity": { "direction": "+", "weight": 0.14, "description": "Clarity of decision logic" },
    "volume_frequency": { "direction": "+", "weight": 0.12, "description": "Execution volume and cadence" },
    "digital_maturity": { "direction": "+", "weight": 0.10, "description": "Tooling and digital capture" },
    "error_cost_tolerance": { "direction": "+", "weight": 0.10, "description": "Cost of error tolerance" },
    "human_judgment_dependency": { "direction": "-", "weight": 0.12, "description": "Nuanced human expertise requirement" },
    "regulatory_safety_constraint": { "direction": "-", "weight": 0.08, "description": "Regulatory oversight & safety criticality" }
  },
  "bands": {
    "automate_threshold": 70,
    "augment_threshold": 45
  },
  "override": {
    "description": "If regulatory_safety_constraint==5 AND human_judgment_dependency>=4, cap band at Augment",
    "regulatory_safety_constraint_eq": 5,
    "human_judgment_dependency_gte": 4,
    "cap_band": "Augment"
  }
}
```

---

### 10. Get Claim Evidence

#### `GET /api/evidence/{claim_id}`
Returns all cited evidence records, matched chunks, and verbatim quotes supporting an extracted claim.

- **Path Parameters:**
  - `claim_id` *(integer, required)*: Database ID of the claim.

- **Response `200 OK`:**
```json
{
  "claim_id": 101,
  "claim_text": "Vibration analysis at 20kHz enables early detection of bearing outer raceway defect frequencies (BPFO).",
  "supported": true,
  "evidence": [
    {
      "id": 501,
      "quote": "High-frequency accelerometer data captures characteristic bearing defect frequencies...",
      "verified": true,
      "verification_method": "exact_match",
      "chunk_text": "In rotating equipment health monitoring, high-frequency accelerometer data...",
      "source": {
        "title": "ISO 13373-1: Condition Monitoring and Diagnostics of Machines",
        "publisher": "International Organization for Standardization",
        "url": "https://www.iso.org/standard/39735.html",
        "year": 2022
      }
    }
  ]
}
```

---

### 11. Rescore Process

#### `POST /api/processes/{id}/rescore`
Triggers deterministic rescoring of an existing process against an updated or alternate rubric version without re-running LLM extraction.

- **Path Parameters:**
  - `id` *(integer, required)*: Process database ID.
- **Query Parameters:**
  - `rubric_version` *(string, optional, default: `"v1"`)*: Target rubric version.

- **Response `200 OK`:**
```json
{
  "message": "Rescored under v1"
}
```

---

## 🔒 Error Handling & Status Codes

| HTTP Status | Meaning | Typical Trigger |
|---|---|---|
| `200 OK` | Request succeeded | Standard reads & synchronous queries |
| `202 Accepted` | Background processing initiated | Process 101 ingestion (`POST /api/processes`) |
| `400 Bad Request` | Invalid payload or constraints | Compare request with fewer/more than 2 IDs |
| `404 Not Found` | Entity does not exist | Invalid `process_id`, `job_id`, or `claim_id` |
| `409 Conflict` | Deduplication duplicate | Submitting process text with an existing SHA-256 hash |
| `422 Unprocessable Entity` | Pydantic schema validation error | Empty process name, description < 20 chars |
| `500 Internal Error` | Unhandled backend exception | Database connection drop or external API error |
