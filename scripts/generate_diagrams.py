#!/usr/bin/env python3
"""
Generate professional, enterprise-grade architecture diagrams in PNG and PDF formats:
1. System Architecture (submission/architecture/system-architecture.{png,pdf})
2. AI Architecture (submission/architecture/ai-architecture.{png,pdf})
3. Database ER Diagram (submission/architecture/database-er-diagram.{png,pdf})
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("submission/architecture", exist_ok=True)

# Set global styles
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# ─────────────────────────────────────────────────────────────────────────────
# 1. SYSTEM ARCHITECTURE DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────
def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(18, 12), dpi=300)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Background
    fig.patch.set_facecolor('#0f1117')
    ax.set_facecolor('#0f1117')

    # Title Header
    ax.text(9, 11.4, "PROCESS INTELLIGENCE ENGINE (PIE) — SYSTEM ARCHITECTURE", 
            ha='center', va='center', color='#ffffff', fontsize=18, fontweight='bold')
    ax.text(9, 11.0, 'Core Architectural Invariant: "AI interprets unstructured text. Deterministic software makes business decisions."',
            ha='center', va='center', color='#818cf8', fontsize=11, style='italic')

    # Legend / Category Containers
    # User / Frontend Tier
    frontend_box = patches.FancyBboxPatch((0.8, 8.5), 16.4, 2.0, boxstyle="round,pad=0.3,rounding_size=0.2",
                                          ec='#3a3d4f', fc='#1a1d27', lw=1.5)
    ax.add_patch(frontend_box)
    ax.text(1.2, 10.1, "PRESENTATION TIER (React 18 + TypeScript + Vite)", color='#6366f1', fontsize=12, fontweight='bold')
    
    # Frontend Component Cards
    fe_items = [
        ("Executive Dashboard", "Portfolio stats, band\ndistribution pie chart,\nscore histogram (Recharts)", 1.2),
        ("Process Explorer", "Search, department\nfilters, pagination,\nsortable table", 4.4),
        ("Deep Process Detail", "Factor waterfall chart,\nverbatim evidence chain,\nprovenance inspection", 7.6),
        ("Ask PIE (NL Interface)", "Natural language Q&A,\nreal-time query plan,\nparameterized outputs", 10.8),
        ("Process 101 Ingestion", "Raw text submission,\n9-stage live job\nprogress tracker", 14.0)
    ]
    for title, desc, x in fe_items:
        card = patches.FancyBboxPatch((x, 8.7), 2.8, 1.2, boxstyle="round,pad=0.15,rounding_size=0.1",
                                     ec='#4f46e5', fc='#21242f', lw=1)
        ax.add_patch(card)
        ax.text(x + 1.4, 9.55, title, ha='center', va='center', color='#ffffff', fontsize=9.5, fontweight='bold')
        ax.text(x + 1.4, 9.05, desc, ha='center', va='center', color='#9ba1b0', fontsize=7.5)

    # API & Gateway Tier
    api_box = patches.FancyBboxPatch((0.8, 6.4), 16.4, 1.7, boxstyle="round,pad=0.3,rounding_size=0.2",
                                     ec='#3a3d4f', fc='#1a1d27', lw=1.5)
    ax.add_patch(api_box)
    ax.text(1.2, 7.75, "APPLICATION & CONTROL TIER (FastAPI 0.111 + Pydantic v2)", color='#38bdf8', fontsize=12, fontweight='bold')
    
    api_items = [
        ("REST API Gateways", "8 Routers: /processes, /portfolio,\n/rubric, /ask, /jobs, /evidence", 1.2, '#0284c7'),
        ("Async Pipeline Runner", "BackgroundTasks worker with\nstep-by-step progress tracking", 5.2, '#0284c7'),
        ("QueryPlan Dispatcher", "Strongly typed intent router;\nZero raw text-to-SQL generation", 9.2, '#0284c7'),
        ("Evidence Verifier", "Deterministic substring quote\nverification against source chunks", 13.2, '#0284c7')
    ]
    for title, desc, x, color in api_items:
        card = patches.FancyBboxPatch((x, 6.6), 3.6, 0.95, boxstyle="round,pad=0.15,rounding_size=0.1",
                                     ec=color, fc='#21242f', lw=1)
        ax.add_patch(card)
        ax.text(x + 1.8, 7.25, title, ha='center', va='center', color='#ffffff', fontsize=9.5, fontweight='bold')
        ax.text(x + 1.8, 6.85, desc, ha='center', va='center', color='#9ba1b0', fontsize=7.5)

    # Processing & Intelligence Engines Tier (Left: AI, Right: Deterministic)
    # AI Subsystem
    ai_box = patches.FancyBboxPatch((0.8, 3.2), 7.9, 2.8, boxstyle="round,pad=0.3,rounding_size=0.2",
                                    ec='#eab308', fc='#1a1d27', lw=1.5)
    ax.add_patch(ai_box)
    ax.text(1.2, 5.65, "PROBABILISTIC AI INTERPRETATION LAYER", color='#eab308', fontsize=11, fontweight='bold')
    
    ai_cards = [
        ("Groq API (Llama-3.1-8B-Instant)", "Strict JSON-mode feature rating (1–5),\nfactual claim extraction, intent routing.\nExponential backoff + schema repair retry.", 1.2, 4.4, 7.1, 1.05),
        ("Embedding Model (all-mpnet-base-v2)", "768-dimensional dense semantic vectors\nfor claim retrieval against industrial corpus.", 1.2, 3.4, 7.1, 0.85)
    ]
    for title, desc, x, y, w, h in ai_cards:
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.1",
                                     ec='#ca8a04', fc='#21242f', lw=1)
        ax.add_patch(card)
        ax.text(x + w/2, y + h*0.7, title, ha='center', va='center', color='#fef08a', fontsize=9, fontweight='bold')
        ax.text(x + w/2, y + h*0.3, desc, ha='center', va='center', color='#cbd5e1', fontsize=7.5)

    # Deterministic Subsystem
    det_box = patches.FancyBboxPatch((9.3, 3.2), 7.9, 2.8, boxstyle="round,pad=0.3,rounding_size=0.2",
                                     ec='#22c55e', fc='#1a1d27', lw=1.5)
    ax.add_patch(det_box)
    ax.text(9.7, 5.65, "DETERMINISTIC DECISION & EXECUTION ENGINE", color='#22c55e', fontsize=11, fontweight='bold')
    
    det_cards = [
        ("Mathematical Scoring Engine (rubric_v1.yaml)", "Score = Σ(weight × signed_feature × 100)\nAutomate (≥70), Augment (45–69), Human-Led (<45)\nHard Safety Override rule for regulated domains.", 9.7, 4.4, 7.1, 1.05),
        ("Portfolio Ranker & Whitelisted SQL", "Recomputes exact ranks/percentiles across 100+ items.\nParameterized SQLAlchemy queries only.", 9.7, 3.4, 7.1, 0.85)
    ]
    for title, desc, x, y, w, h in det_cards:
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.1",
                                     ec='#16a34a', fc='#21242f', lw=1)
        ax.add_patch(card)
        ax.text(x + w/2, y + h*0.7, title, ha='center', va='center', color='#86efac', fontsize=9, fontweight='bold')
        ax.text(x + w/2, y + h*0.3, desc, ha='center', va='center', color='#cbd5e1', fontsize=7.5)

    # Persistence & Knowledge Tier
    db_box = patches.FancyBboxPatch((0.8, 0.6), 16.4, 2.2, boxstyle="round,pad=0.3,rounding_size=0.2",
                                    ec='#3a3d4f', fc='#1a1d27', lw=1.5)
    ax.add_patch(db_box)
    ax.text(1.2, 2.45, "PERSISTENCE & STORAGE TIER (PostgreSQL 16 + pgvector Extension)", color='#a855f7', fontsize=12, fontweight='bold')
    
    db_cards = [
        ("Relational Core", "Process, ProcessFeature, Score,\nScoreFactor, Job, ExtractionRun,\nQueryLog tables with foreign keys", 1.2, 0.8, 4.8, 1.4),
        ("pgvector Vector Store", "SourceChunk embeddings (768-dim),\nCosine distance index (<=>)\nfor fast semantic similarity retrieval", 6.6, 0.8, 4.8, 1.4),
        ("Ground-Truth Knowledge Corpus", "25 Markdown industrial research\ndocuments with YAML frontmatter,\nparagraph chunking & overlap", 12.0, 0.8, 4.8, 1.4)
    ]
    for title, desc, x, y, w, h in db_cards:
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.1",
                                     ec='#9333ea', fc='#21242f', lw=1)
        ax.add_patch(card)
        ax.text(x + w/2, y + h*0.7, title, ha='center', va='center', color='#e9d5ff', fontsize=9.5, fontweight='bold')
        ax.text(x + w/2, y + h*0.35, desc, ha='center', va='center', color='#9ba1b0', fontsize=8)

    # Connecting Arrows
    arrow_props = dict(facecolor='#818cf8', edgecolor='none', width=2, headwidth=7, headlength=7)
    
    # Frontend <-> API
    ax.annotate('', xy=(9, 8.5), xytext=(9, 8.1), arrowprops=arrow_props)
    ax.annotate('', xy=(9, 8.1), xytext=(9, 8.5), arrowprops=arrow_props)
    
    # API <-> AI & Deterministic
    ax.annotate('', xy=(4.75, 6.4), xytext=(4.75, 6.0), arrowprops=arrow_props)
    ax.annotate('', xy=(13.25, 6.4), xytext=(13.25, 6.0), arrowprops=arrow_props)
    
    # AI & Deterministic <-> DB
    ax.annotate('', xy=(4.75, 3.2), xytext=(4.75, 2.8), arrowprops=arrow_props)
    ax.annotate('', xy=(13.25, 3.2), xytext=(13.25, 2.8), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig("submission/architecture/system-architecture.png", dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.savefig("submission/architecture/system-architecture.pdf", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("✓ Created system-architecture.png and system-architecture.pdf")

# ─────────────────────────────────────────────────────────────────────────────
# 2. AI ARCHITECTURE DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────
def generate_ai_architecture():
    fig, ax = plt.subplots(figsize=(18, 12), dpi=300)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    fig.patch.set_facecolor('#0f1117')
    ax.set_facecolor('#0f1117')

    # Title
    ax.text(9, 11.4, "PROCESS INTELLIGENCE ENGINE (PIE) — AI & INTELLIGENCE ARCHITECTURE", 
            ha='center', va='center', color='#ffffff', fontsize=17, fontweight='bold')
    ax.text(9, 11.0, "Three Controlled AI Interaction Pathways: Extraction, Evidence Retrieval (RAG), and Natural Language Query",
            ha='center', va='center', color='#38bdf8', fontsize=11)

    # ── PATHWAY 1: 9-STAGE EXTRACTION & SCORING (Top to Bottom left) ─────────
    p1_box = patches.FancyBboxPatch((0.6, 0.6), 5.4, 10.0, boxstyle="round,pad=0.25,rounding_size=0.15",
                                    ec='#6366f1', fc='#1a1d27', lw=1.5)
    ax.add_patch(p1_box)
    ax.text(3.3, 10.25, "PATHWAY 1: 9-STAGE PIPELINE", ha='center', va='center', color='#818cf8', fontsize=11, fontweight='bold')
    
    p1_steps = [
        ("1. Input Process Description", "Raw unstructured text from industrial operations", '#21242f', '#ffffff'),
        ("2. Validation & Normalization", "Regex cleanup, strip punctuation, lowercase", '#21242f', '#ffffff'),
        ("3. SHA-256 Deduplication", "Idempotent hash check prevents duplicate runs", '#21242f', '#ffffff'),
        ("4. Groq LLM Feature Extraction", "JSON-mode ratings (1–5) on 8 rubric factors +\n3–5 factual claims + rationale & confidence", '#3b2d18', '#fde047'),
        ("5. Feature Normalization", "Ordinals mapped deterministically to [0.0, 1.0]", '#21242f', '#ffffff'),
        ("6. Deterministic Rubric Scoring", "Rubric YAML weights × signed direction;\nAutomate / Augment / Human-Led decision", '#193322', '#86efac'),
        ("7. Safety Override Enforcement", "Caps at Augment if Safety=5 & Judgment≥4", '#3b1c1c', '#fca5a5'),
        ("8. Persistence & Audit Log", "Saves score, factors, run ID, inputs hash", '#21242f', '#ffffff'),
        ("9. Portfolio Re-Ranking", "Exact ranks (1..N) and percentiles computed", '#21242f', '#ffffff')
    ]
    for idx, (title, desc, bg, textcol) in enumerate(p1_steps):
        y = 9.35 - (idx * 0.95)
        card = patches.FancyBboxPatch((0.9, y), 4.8, 0.78, boxstyle="round,pad=0.1,rounding_size=0.08",
                                     ec='#475569', fc=bg, lw=1)
        ax.add_patch(card)
        ax.text(1.1, y + 0.52, title, color=textcol, fontsize=8.5, fontweight='bold')
        ax.text(1.1, y + 0.22, desc, color='#94a3b8', fontsize=7.2)

    # ── PATHWAY 2: RAG & VERBATIM EVIDENCE VERIFICATION (Center) ─────────────
    p2_box = patches.FancyBboxPatch((6.3, 0.6), 5.4, 10.0, boxstyle="round,pad=0.25,rounding_size=0.15",
                                    ec='#eab308', fc='#1a1d27', lw=1.5)
    ax.add_patch(p2_box)
    ax.text(9.0, 10.25, "PATHWAY 2: EVIDENCE & RAG", ha='center', va='center', color='#fde047', fontsize=11, fontweight='bold')
    
    p2_steps = [
        ("1. Extracted Factual Claims", "Claims generated by LLM during Stage 4", '#21242f', '#ffffff'),
        ("2. Dual-Engine Retrieval", "Lexical keyword matching +\npgvector cosine similarity (all-mpnet-base-v2)", '#21242f', '#ffffff'),
        ("3. 25 Industrial Corpus Docs", "Ground-truth engineering & operational standards", '#21242f', '#ffffff'),
        ("4. Top-K Candidate Chunks", "Relevant paragraph segments (500 tokens)", '#21242f', '#ffffff'),
        ("5. LLM Verbatim Quote Selection", "Prompted to return exact quote or NO_QUOTE", '#3b2d18', '#fde047'),
        ("6. Deterministic Quote Verification", "Exact substring check: normalized(quote)\nin normalized(chunk_text)", '#193322', '#86efac'),
        ("7. Provenance Record Creation", "Link verified quote -> chunk -> source URL/year", '#21242f', '#ffffff'),
        ("8. Audit Trust Chain", "Claims flagged supported=True/False with full citation", '#21242f', '#ffffff')
    ]
    for idx, (title, desc, bg, textcol) in enumerate(p2_steps):
        y = 9.35 - (idx * 1.1)
        card = patches.FancyBboxPatch((6.6, y), 4.8, 0.88, boxstyle="round,pad=0.1,rounding_size=0.08",
                                     ec='#ca8a04', fc=bg, lw=1)
        ax.add_patch(card)
        ax.text(6.8, y + 0.58, title, color=textcol, fontsize=8.5, fontweight='bold')
        ax.text(6.8, y + 0.24, desc, color='#94a3b8', fontsize=7.2)

    # ── PATHWAY 3: ASK PIE NATURAL LANGUAGE QUERY (Right) ───────────────────
    p3_box = patches.FancyBboxPatch((12.0, 0.6), 5.4, 10.0, boxstyle="round,pad=0.25,rounding_size=0.15",
                                    ec='#22c55e', fc='#1a1d27', lw=1.5)
    ax.add_patch(p3_box)
    ax.text(14.7, 10.25, "PATHWAY 3: NATURAL LANGUAGE QUERY", ha='center', va='center', color='#86efac', fontsize=11, fontweight='bold')
    
    p3_steps = [
        ("1. User Business Question", '"Which maintenance processes should we automate?"', '#21242f', '#ffffff'),
        ("2. Closed Intent Classification", "Groq classifies into 7 whitelisted intents:\nrank_top, filter_by_band, explain_process,\nportfolio_stats, compare, open_research, unmappable", '#3b2d18', '#fde047'),
        ("3. Strongly Typed QueryPlan", "Pydantic model with validated parameters\n(limit, band filter, metric, target_id)", '#21242f', '#ffffff'),
        ("4. Whitelisted Query Executor", "NO TEXT-TO-SQL. Pre-compiled SQLAlchemy\nparameterized queries mapped to intent.", '#193322', '#86efac'),
        ("5. Secure Database Execution", "Direct, parameterized PostgreSQL execution", '#21242f', '#ffffff'),
        ("6. LLM Prose Explanation", "LLM explains pre-computed numbers;\nZero calculation done by LLM.", '#3b2d18', '#fde047'),
        ("7. UI Response Rendering", "Tabular data + prose + debug QueryPlan", '#21242f', '#ffffff')
    ]
    for idx, (title, desc, bg, textcol) in enumerate(p3_steps):
        y = 9.35 - (idx * 1.25)
        card = patches.FancyBboxPatch((12.3, y), 4.8, 1.0, boxstyle="round,pad=0.1,rounding_size=0.08",
                                     ec='#16a34a', fc=bg, lw=1)
        ax.add_patch(card)
        ax.text(12.5, y + 0.68, title, color=textcol, fontsize=8.5, fontweight='bold')
        ax.text(12.5, y + 0.28, desc, color='#94a3b8', fontsize=7.2)

    plt.tight_layout()
    plt.savefig("submission/architecture/ai-architecture.png", dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.savefig("submission/architecture/ai-architecture.pdf", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("✓ Created ai-architecture.png and ai-architecture.pdf")

# ─────────────────────────────────────────────────────────────────────────────
# 3. DATABASE ER DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────
def generate_database_er_diagram():
    fig, ax = plt.subplots(figsize=(20, 14), dpi=300)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    fig.patch.set_facecolor('#0f1117')
    ax.set_facecolor('#0f1117')

    ax.text(10, 13.4, "PROCESS INTELLIGENCE ENGINE (PIE) — DATABASE ENTITY-RELATIONSHIP (ER) MODEL", 
            ha='center', va='center', color='#ffffff', fontsize=17, fontweight='bold')
    ax.text(10, 13.0, "PostgreSQL 16 with pgvector Extension — 11 Relational & Vector Tables",
            ha='center', va='center', color='#a855f7', fontsize=11)

    tables = [
        # Table 1: Process (Root entity)
        ("process", 0.8, 8.2, 3.8, 4.2, [
            ("id", "INTEGER (PK)", True),
            ("external_key", "VARCHAR(128)", False),
            ("name", "VARCHAR(256)", False),
            ("raw_description", "TEXT", False),
            ("normalized_text", "TEXT", False),
            ("content_hash", "VARCHAR(64) UNIQUE", False),
            ("department", "VARCHAR(128)", False),
            ("industry", "VARCHAR(128)", False),
            ("status", "ENUM (ProcessStatus)", False),
            ("created_at", "DATETIME", False)
        ]),
        
        # Table 2: ProcessFeature
        ("process_feature", 5.2, 8.2, 4.2, 4.2, [
            ("id", "INTEGER (PK)", True),
            ("process_id", "INTEGER (FK -> process.id)", True),
            ("rubric_version", "VARCHAR(32)", False),
            ("feature_key", "VARCHAR(64)", False),
            ("ordinal_value", "INTEGER (1..5)", False),
            ("normalized_value", "FLOAT (0.0..1.0)", False),
            ("rationale", "TEXT", False),
            ("confidence", "FLOAT", False),
            ("extraction_run_id", "INTEGER (FK -> extraction_run)", False)
        ]),

        # Table 3: Score
        ("score", 10.0, 8.2, 4.4, 4.2, [
            ("id", "INTEGER (PK)", True),
            ("process_id", "INTEGER (FK -> process.id)", True),
            ("rubric_version", "VARCHAR(32)", False),
            ("total_score", "FLOAT (0.0..100.0)", False),
            ("band", "VARCHAR(32)", False),
            ("recommendation", "VARCHAR(64)", False),
            ("recommendation_text", "TEXT", False),
            ("inputs_hash", "VARCHAR(64)", False),
            ("computed_at", "DATETIME", False),
            ("UQ_SCORE_VERSION", "UNIQUE(process_id, version)", False)
        ]),

        # Table 4: ScoreFactor
        ("score_factor", 15.0, 8.2, 4.2, 4.2, [
            ("id", "INTEGER (PK)", True),
            ("score_id", "INTEGER (FK -> score.id)", True),
            ("factor_key", "VARCHAR(64)", False),
            ("feature_value", "FLOAT", False),
            ("weight", "FLOAT", False),
            ("contribution", "FLOAT", False),
            ("direction", "VARCHAR(8) ('+' / '-')", False)
        ]),

        # Table 5: ExtractionRun
        ("extraction_run", 0.8, 3.8, 3.8, 3.8, [
            ("id", "INTEGER (PK)", True),
            ("process_id", "INTEGER (FK -> process.id)", True),
            ("model", "VARCHAR(128)", False),
            ("prompt_version", "VARCHAR(32)", False),
            ("raw_response", "TEXT", False),
            ("created_at", "DATETIME", False)
        ]),

        # Table 6: Claim
        ("claim", 5.2, 3.8, 4.2, 3.8, [
            ("id", "INTEGER (PK)", True),
            ("process_id", "INTEGER (FK -> process.id)", True),
            ("claim_text", "TEXT", False),
            ("claim_type", "VARCHAR(64)", False),
            ("supported", "BOOLEAN", False),
            ("created_at", "DATETIME", False)
        ]),

        # Table 7: Evidence
        ("evidence", 10.0, 3.8, 4.4, 3.8, [
            ("id", "INTEGER (PK)", True),
            ("claim_id", "INTEGER (FK -> claim.id)", True),
            ("source_chunk_id", "INTEGER (FK -> source_chunk.id)", True),
            ("quote", "TEXT", False),
            ("verified", "BOOLEAN", False),
            ("verification_method", "VARCHAR(64)", False)
        ]),

        # Table 8: SourceChunk (Vector)
        ("source_chunk", 15.0, 3.8, 4.2, 3.8, [
            ("id", "INTEGER (PK)", True),
            ("source_id", "INTEGER (FK -> source.id)", True),
            ("chunk_index", "INTEGER", False),
            ("text", "TEXT", False),
            ("embedding", "VECTOR(768) [pgvector]", False)
        ]),

        # Table 9: Source
        ("source", 15.0, 0.4, 4.2, 2.8, [
            ("id", "INTEGER (PK)", True),
            ("title", "VARCHAR(512)", False),
            ("publisher", "VARCHAR(256)", False),
            ("url", "VARCHAR(1024)", False),
            ("year", "INTEGER", False),
            ("credibility_tier", "INTEGER", False)
        ]),

        # Table 10: ProcessRank
        ("process_rank", 0.8, 0.4, 3.8, 2.8, [
            ("id", "INTEGER (PK)", True),
            ("process_id", "INTEGER (FK -> process.id)", True),
            ("rubric_version", "VARCHAR(32)", False),
            ("rank", "INTEGER", False),
            ("percentile", "FLOAT", False),
            ("computed_at", "DATETIME", False)
        ]),

        # Table 11: Job & QueryLog
        ("job & query_log", 5.2, 0.4, 9.2, 2.8, [
            ("job.id (PK)", "kind, target_process_id (FK), status, stage, progress, error, finished_at", True),
            ("query_log.id (PK)", "question, intent, query_plan_json (JSON), result_summary, created_at", True),
            ("rubric_version (PK)", "version (PK), definition_json (JSON), created_at, notes", True)
        ])
    ]

    for name, x, y, w, h, cols in tables:
        # Table Box
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.1",
                                     ec='#4f46e5', fc='#1a1d27', lw=1.2)
        ax.add_patch(card)
        
        # Header bar
        hbar = patches.FancyBboxPatch((x, y + h - 0.45), w, 0.45, boxstyle="round,pad=0.05,rounding_size=0.05",
                                     ec='#6366f1', fc='#312e81', lw=1)
        ax.add_patch(hbar)
        ax.text(x + w/2, y + h - 0.22, name.upper(), ha='center', va='center', color='#ffffff', fontsize=9.5, fontweight='bold')
        
        # Column rows
        row_y = y + h - 0.7
        for cname, ctype, is_key in cols:
            kcol = '#f59e0b' if is_key else '#94a3b8'
            ax.text(x + 0.15, row_y, cname, color='#e2e8f0', fontsize=7.5, fontweight='bold' if is_key else 'normal')
            ax.text(x + w - 0.15, row_y, ctype, ha='right', color=kcol, fontsize=7.0)
            row_y -= 0.32

    # Relationship Lines / Arrows
    lines = [
        # process -> features
        ((4.6, 10.3), (5.2, 10.3)),
        # process -> score
        ((4.6, 9.5), (10.0, 9.5)),
        # score -> score_factor
        ((14.4, 10.3), (15.0, 10.3)),
        # process -> extraction_run
        ((2.7, 8.2), (2.7, 7.6)),
        # process -> claim
        ((4.6, 8.2), (5.2, 5.7)),
        # claim -> evidence
        ((9.4, 5.7), (10.0, 5.7)),
        # evidence -> source_chunk
        ((14.4, 5.7), (15.0, 5.7)),
        # source -> source_chunk
        ((17.1, 3.2), (17.1, 3.8)),
        # process -> process_rank
        ((2.7, 8.2), (2.7, 3.2))
    ]
    for start, end in lines:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(facecolor='#a855f7', edgecolor='#a855f7', width=1.5, headwidth=5, headlength=5))

    plt.tight_layout()
    plt.savefig("submission/architecture/database-er-diagram.png", dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.savefig("submission/architecture/database-er-diagram.pdf", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("✓ Created database-er-diagram.png and database-er-diagram.pdf")

if __name__ == '__main__':
    generate_system_architecture()
    generate_ai_architecture()
    generate_database_er_diagram()
    print("All architecture diagrams generated successfully!")
