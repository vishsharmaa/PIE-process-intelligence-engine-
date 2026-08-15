# 🎬 Process Intelligence Engine (PIE) — Video Presentation & Demo Script

> **Target Duration:** 10–13 minutes  
> **Format:** Screen Recording + Voiceover Walkthrough  
> **Stage:** Stage 2 AI Application Submission — MODUS Enterprise AI Build Challenge  

---

## ⏱️ Video Structure & Timing Outline

| Segment | Duration | Title | Key Visual Focus |
|---|---|---|---|
| **0:00–1:00** | 1:00 min | **Problem & Solution** | Executive Dashboard / Problem Statement Slide |
| **1:00–2:30** | 1:30 min | **System & AI Architecture** | Methodology Page & System Architecture Diagram |
| **2:30–4:30** | 2:00 min | **Portfolio Explorer & Scoring Waterfall** | Portfolio Table & Deep Process Waterfall View |
| **4:30–6:30** | 2:00 min | **RAG Evidence & Trust Chain** | Claim-to-Evidence Provenance & Verbatim Citations |
| **6:30–8:00** | 1:30 min | **Ask PIE (Natural Language Interface)** | Intent Routing, QueryPlan Debug, Parameterized Execution |
| **8:00–10:00** | 2:00 min | **Process 101 Ingestion** | Live Ingestion Form & 9-Stage Progress Polling |
| **10:00–11:30** | 1:30 min | **Engineering Quality & Invariants** | Pytest Test Suite, Code Quality, Invariant Equations |
| **11:30–12:30** | 1:00 min | **Core AI Philosophy & Closing** | Closing Slide: "AI interprets. Software decides." |

---

## 🎙️ Detailed Voiceover & Screen Direction Script

### 1. Problem & Solution (0:00–1:00)

**[Screen: Executive Dashboard — `/#/dashboard` showing 100 processes, band breakdown, and KPIs]**

> **Speaker:**  
> "Welcome to the Process Intelligence Engine—or **PIE**—built for the MODUS Enterprise AI Build Challenge.
>
> In every enterprise, digital transformation and automation initiatives face a fundamental bottleneck: **subjective decision-making**. When companies prioritize which operational processes to automate, augment with AI, or keep human-led, they typically rely on expensive, months-long consulting surveys or subjective executive intuition.
>
> Generic LLM chatbots don't solve this problem—in fact, they make it worse by hallucinating arbitrary scores, ignoring hard regulatory constraints, and providing zero auditability.
>
> PIE solves this by converting unstructured, natural-language process descriptions into **structured, evidence-backed transformation intelligence**.
>
> Most importantly, PIE is not a thin LLM wrapper. It is built on a foundational engineering principle:  
> **'AI interprets unstructured text. Deterministic software makes business decisions.'** Let's look under the hood."

---

### 2. Architecture & Pipeline Overview (1:00–2:30)

**[Screen: Navigate to `/#/methodology` — Scroll down to the 9-stage flow diagram and architecture overview]**

> **Speaker:**  
> "PIE is built on a modern, decoupled enterprise stack:
> - On the frontend, **React 18, TypeScript, Vite, and TanStack Query** deliver a responsive, zero-latency user experience.
> - The backend is powered by **FastAPI and Pydantic v2**, orchestrating asynchronous background pipelines.
> - For storage, we use a single unified **PostgreSQL 16** database with the **pgvector** extension for semantic indexing.
> - For AI, we leverage **Groq's Llama-3.1-8B** for bounded extraction and intent classification, alongside local **sentence-transformers** for 768-dimensional embeddings.
>
> Every process submitted to PIE flows through a strict **9-stage pipeline**:
> 1. Validation $\rightarrow$ 2. Text Normalization $\rightarrow$ 3. SHA-256 Deduplication $\rightarrow$ 4. Groq LLM Feature Extraction $\rightarrow$ 5. Feature Normalization $\rightarrow$ 6. Dual-Engine RAG Research $\rightarrow$ 7. Deterministic Rubric Scoring $\rightarrow$ 8. Persistence $\rightarrow$ and 9. Dynamic Portfolio Re-ranking.
>
> Crucially, the LLM has zero arithmetic authority. It rates qualitative factors on an ordinal scale of 1 to 5 and extracts factual claims. Our Python engine handles all math, scoring, and ranking."

---

### 3. Portfolio Explorer & Scoring Waterfall (2:30–4:30)

**[Screen: Navigate to `/#/portfolio`, then click on Process #1: 'Vibration-Based Bearing Failure Prediction']**

> **Speaker:**  
> "Let's examine the engine in action across our pre-seeded portfolio of **100 diverse manufacturing and industrial processes**.
>
> Here in the Portfolio view, all 100 processes are ranked from 1 to 100 with exact percentile distributions.
>
> Let's open our top-ranked candidate: *Vibration-Based Bearing Failure Prediction*.
>
> Notice the score: **82.5 out of 100**, placing it in the **Automate** band. How did we get this number?
>
> Look at this **Score-Factor Waterfall Chart**. The LLM extracted ratings across 8 operational dimensions—such as Data Availability, Process Repeatability, Rule Clarity, and Human Judgment.
>
> Our deterministic scoring engine evaluated these ratings against our configurable YAML rubric:
> - **Positive Drivers (green bars):** Data Availability is rated 5/5, contributing +18.0 points. Process Repeatability contributes +16.0 points.
> - **Negative Constraints (orange/red bars):** Human Judgment Dependency is rated 2/5, deducting minimal constraint points.
>
> The sum of these signed contributions **equals the total score of 82.5 exactly**—a mathematical invariant enforced in code.
>
> Furthermore, look at our **Safety Override Rule**: if a process has maximum Regulatory Constraint (5/5) and high Human Judgment ($\ge 4/5$), the system automatically caps the decision at 'Augment', preventing dangerous over-automation in regulated environments."

---

### 4. RAG Evidence & Trust Chain (4:30–6:30)

**[Screen: Scroll down to the Evidence & Claims section on the Process Detail page]**

> **Speaker:**  
> "An enterprise recommendation is useless if leaders cannot verify the underlying facts.
>
> During the extraction stage, the LLM extracted factual claims about this process. But because LLMs can hallucinate, PIE does not trust them blindly.
>
> In the **Research Stage**, PIE queried our knowledge base of **25 industrial engineering reference standards** (covering ISO vibration diagnostics, FDA GMP compliance, IPC assembly standards, and Six Sigma SPC).
>
> The system executes a dual search: lexical token matching combined with pgvector cosine similarity.
>
> Once relevant chunks are retrieved, the LLM selects a candidate quote, and our Python engine performs **deterministic quote verification**: an exact, normalized substring match against the source text.
>
> Here you can see the verified quote: *'High-frequency accelerometer data captures characteristic bearing defect frequencies...'* highlighted with a green badge, linked directly to **ISO 13373-1**, published by the International Organization for Standardization.
>
> This creates an unbroken, auditable trust chain from raw narrative to ground-truth technical literature."

---

### 5. Ask PIE: Secure Natural Language Querying (6:30–8:00)

**[Screen: Navigate to `/#/ask` — Type: "Show top 3 automation candidates in the Maintenance department"]**

> **Speaker:**  
> "Now let's explore **Ask PIE**, our natural language query interface for business stakeholders.
>
> Most 'Chat with your Database' implementations use dynamic Text-to-SQL generation. In an enterprise environment, that is a severe security vulnerability—prone to SQL injection, schema hallucination, and data corruption.
>
> PIE takes a completely different approach. Let's ask: *'Show top 3 automation candidates in the Maintenance department'*.
>
> **[Click Ask]**
>
> Look at what happened:
> 1. The LLM was used strictly for **Intent Classification**, mapping the question to the `rank_top` intent with filter `band: "Automate"` and `limit: 3`.
> 2. It generated a strongly typed **QueryPlan** Pydantic model.
> 3. Our backend passed this QueryPlan to a **pre-compiled, whitelisted SQLAlchemy executor**. Zero arbitrary SQL was generated by the LLM.
> 4. The raw database results were then summarized into a clear, 2-sentence executive prose explanation.
>
> It is fast, 100% deterministic, and completely immune to SQL injection."

---

### 6. Process 101: Live Asynchronous Ingestion (8:00–10:00)

**[Screen: Navigate to `/#/ingest` — Paste a new process description and click Submit]**

> **Speaker:**  
> "Let's demonstrate dynamic ingestion by submitting **Process 101**—a brand new, unseen manufacturing process.
>
> Let's enter: *'Automated Optical Inspection (AOI) for PCB Assembly'* with a description explaining our SMT line inspection, camera feeds, and false-call review under microscopes.
>
> **[Click Ingest Process]**
>
> The API immediately returns a 202 Accepted response and dispatches an asynchronous background worker.
>
> Notice the live progress bar:
> - It validates input and normalizes text...
> - Computes the SHA-256 hash for deduplication...
> - Calls Groq for JSON-mode factor extraction...
> - Persists feature records...
> - Runs RAG research and quote verification against the corpus...
> - Computes deterministic scoring...
> - And re-ranks the entire portfolio!
>
> **[Page transitions to the new Process Detail page]**
>
> Process 101 has received its score (76.8, Automate band), its factor waterfall, and its verified evidence. If we return to the Portfolio view, you can see that Process 101 is now actively ranked alongside the original 100 processes."

---

### 7. Engineering Quality & Test Suite (10:00–11:30)

**[Screen: Terminal showing `pytest` running across 45 tests with 100% pass rate]**

> **Speaker:**  
> "Behind this intuitive interface lies an uncompromising commitment to enterprise software engineering quality:
> - Our automated test suite contains **45 comprehensive unit and integration tests** in Pytest, executing in under 1 second.
> - We test mathematical boundary conditions: all 1s, all 3s, all 5s, and randomized feature vectors, verifying that the linear additive scoring invariant holds in every single case.
> - We test deduplication idempotency, verifying that identical process narratives always generate identical SHA-256 hashes.
> - We test quote verification across exact matches, whitespace variations, and negative hallucination cases.
> - The entire frontend build executes with **zero TypeScript errors and zero lint warnings**."

---

### 8. Core Philosophy & Closing (11:30–12:30)

**[Screen: Return to the Executive Dashboard — `/#/dashboard`]**

> **Speaker:**  
> "To summarize our work on the Process Intelligence Engine:
>
> We set out to prove that enterprise AI systems do not have to be black-box chatbots. By strictly separating **probabilistic semantic interpretation** from **deterministic mathematical decisions**, PIE provides:
> 1. **Objective, repeatable scoring** driven by configurable rubrics.
> 2. **Ground-truth traceability** via verified verbatim quotes.
> 3. **Enterprise security** through typed QueryPlans and zero text-to-SQL.
> 4. **A scalable architecture** combining FastAPI, pgvector, Groq, and React.
>
> Thank you for reviewing the Process Intelligence Engine for the MODUS Enterprise AI Build Challenge. We invite you to inspect our repository and test the live application."

---
