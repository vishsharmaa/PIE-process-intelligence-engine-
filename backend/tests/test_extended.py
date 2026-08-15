"""Extended tests: additional scoring edge cases, pipeline validation, seed YAML, and API schemas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import yaml
import pytest

from app.scoring.engine import load_rubric, compute_score
from app.pipeline.normalize import normalize_text, compute_hash
from app.pipeline.validate import validate, ValidationError
from app.corpus.verify_quote import verify_quote
from app.corpus.chunker import chunk_text
from app.schemas import ExtractionResult, FactorExtraction, ProcessCreate
from pydantic import ValidationError as PydanticValidationError


# ── Validation stage ─────────────────────────────────────────────────────────

def test_validate_rejects_empty_name():
    with pytest.raises(ValidationError):
        validate("", "A sufficiently long description for testing purposes")

def test_validate_rejects_short_description():
    with pytest.raises(ValidationError):
        validate("Good Name", "Too short")

def test_validate_accepts_valid_input():
    validate("Good Name", "This is a sufficiently long process description for validation")

def test_validate_rejects_long_name():
    with pytest.raises(ValidationError):
        validate("A" * 257, "A sufficiently long description for testing purposes")


# ── Scoring edge cases ──────────────────────────────────────────────────────

def test_scoring_mixed_values():
    r = load_rubric("v1")
    feat = {
        "data_availability": 5,
        "process_repeatability": 4,
        "rule_clarity": 3,
        "volume_frequency": 5,
        "digital_maturity": 2,
        "error_cost_tolerance": 4,
        "human_judgment_dependency": 2,
        "regulatory_safety_constraint": 1,
    }
    res = compute_score(feat, r)
    real = [f for f in res.factors if f.factor_key != "override_cap"]
    assert abs(round(sum(f.contribution for f in real), 2) - res.total_score) < 0.01
    assert res.total_score > 0

def test_scoring_clamps_out_of_range_ordinals():
    r = load_rubric("v1")
    feat = {k: 10 for k in r["factors"]}  # out of range, should clamp to 5
    res = compute_score(feat, r)
    for f in res.factors:
        assert f.feature_value <= 5.0

def test_scoring_missing_factor_defaults_to_3():
    r = load_rubric("v1")
    feat = {"data_availability": 5}  # all others missing
    res = compute_score(feat, r)
    assert res.total_score > 0  # should compute with defaults

def test_score_result_has_recommendation_text():
    r = load_rubric("v1")
    feat = {k: 3 for k in r["factors"]}
    res = compute_score(feat, r)
    assert len(res.recommendation_text) > 10
    assert res.band in res.recommendation_text or "Score" in res.recommendation_text

def test_score_result_has_inputs_hash():
    r = load_rubric("v1")
    feat = {k: 3 for k in r["factors"]}
    res = compute_score(feat, r)
    assert len(res.inputs_hash) == 64  # SHA-256

def test_different_inputs_produce_different_hashes():
    r = load_rubric("v1")
    feat1 = {k: 3 for k in r["factors"]}
    feat2 = {k: 4 for k in r["factors"]}
    res1 = compute_score(feat1, r)
    res2 = compute_score(feat2, r)
    assert res1.inputs_hash != res2.inputs_hash


# ── Extraction schema validation ──────────────────────────────────────────────

def test_extraction_result_valid():
    data = {
        "data_availability": {"ordinal_value": 4, "rationale": "Good data coverage", "confidence": 0.85},
        "process_repeatability": {"ordinal_value": 3, "rationale": "Moderate repeatability", "confidence": 0.7},
        "rule_clarity": {"ordinal_value": 2, "rationale": "Ambiguous rules", "confidence": 0.6},
        "volume_frequency": {"ordinal_value": 5, "rationale": "Very high volume", "confidence": 0.9},
        "digital_maturity": {"ordinal_value": 3, "rationale": "Some digital tools", "confidence": 0.75},
        "error_cost_tolerance": {"ordinal_value": 4, "rationale": "Tolerant of errors", "confidence": 0.8},
        "human_judgment_dependency": {"ordinal_value": 2, "rationale": "Limited judgment needed", "confidence": 0.7},
        "regulatory_safety_constraint": {"ordinal_value": 1, "rationale": "No regulation", "confidence": 0.9},
        "claims": ["Claim 1", "Claim 2"],
    }
    result = ExtractionResult(**data)
    assert len(result.to_factor_dict()) == 8

def test_extraction_result_rejects_out_of_range():
    data = {
        "data_availability": {"ordinal_value": 6, "rationale": "Bad value", "confidence": 0.5},
        "process_repeatability": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
        "rule_clarity": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
        "volume_frequency": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
        "digital_maturity": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
        "error_cost_tolerance": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
        "human_judgment_dependency": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
        "regulatory_safety_constraint": {"ordinal_value": 3, "rationale": "OK", "confidence": 0.5},
    }
    with pytest.raises(PydanticValidationError):
        ExtractionResult(**data)

def test_process_create_schema_validates():
    pc = ProcessCreate(name="Test Process", raw_description="A sufficiently long test description for the process")
    assert pc.name == "Test Process"

def test_process_create_rejects_empty_name():
    with pytest.raises(PydanticValidationError):
        ProcessCreate(name="", raw_description="A sufficiently long test description")


# ── Chunker ──────────────────────────────────────────────────────────────────

def test_chunker_returns_nonempty():
    text = "Paragraph one about testing.\n\nParagraph two about chunking.\n\nParagraph three about verification."
    chunks = chunk_text(text, chunk_tokens=50, overlap_tokens=10)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c.strip()) > 0

def test_chunker_handles_single_paragraph():
    text = "A single paragraph with some words in it."
    chunks = chunk_text(text)
    assert len(chunks) == 1

def test_chunker_handles_empty_text():
    chunks = chunk_text("")
    assert len(chunks) == 0


# ── verify_quote edge cases ──────────────────────────────────────────────────

def test_verify_quote_long_quote():
    chunk = "Machine learning models trained on historical failure data can identify patterns that precede equipment failure."
    quote = "Machine learning models trained on historical failure data can identify patterns"
    assert verify_quote(quote, chunk)

def test_verify_quote_with_newlines():
    assert verify_quote("hello world", "hello\n  world")


# ── Seed YAML validation ────────────────────────────────────────────────────

def test_seed_yaml_loads_and_has_100_processes():
    seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seeds", "processes_100.yaml")
    with open(seed_path, "r") as f:
        data = yaml.safe_load(f)
    processes = data.get("processes", [])
    assert len(processes) == 100

def test_seed_yaml_all_have_required_fields():
    seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seeds", "processes_100.yaml")
    with open(seed_path, "r") as f:
        data = yaml.safe_load(f)
    for i, p in enumerate(data["processes"]):
        assert p.get("name"), f"Process #{i+1} missing name"
        assert p.get("raw_description"), f"Process #{i+1} missing raw_description"
        assert len(p["raw_description"].strip()) >= 20, f"Process #{i+1} description too short"

def test_seed_yaml_no_duplicate_names():
    seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seeds", "processes_100.yaml")
    with open(seed_path, "r") as f:
        data = yaml.safe_load(f)
    names = [p["name"] for p in data["processes"]]
    assert len(names) == len(set(names)), "Duplicate process names found"

def test_seed_yaml_no_duplicate_hashes():
    seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seeds", "processes_100.yaml")
    with open(seed_path, "r") as f:
        data = yaml.safe_load(f)
    hashes = [compute_hash(normalize_text(p["raw_description"])) for p in data["processes"]]
    assert len(hashes) == len(set(hashes)), "Duplicate content hashes found"

# ── Conditional Embedding / OOM Prevention Tests ─────────────────────────────

def test_embed_corpus_false_does_not_load_transformer(monkeypatch):
    from app.config import get_settings
    from app.corpus.embedder import embed_texts
    
    monkeypatch.setattr(get_settings(), "embed_corpus", False)
    
    import app.corpus.embedder
    app.corpus.embedder._model = None
    
    res = embed_texts(["test text"])
    assert res == [None]
    assert app.corpus.embedder._model is None

def test_embed_corpus_true_embeds_normally(monkeypatch):
    from app.config import get_settings
    from app.corpus.embedder import embed_texts
    
    monkeypatch.setattr(get_settings(), "embed_corpus", True)
    
    called = []
    class MockModel:
        def encode(self, texts, **kwargs):
            called.append(True)
            import numpy as np
            return np.array([[0.1] * 768])
            
    monkeypatch.setattr("app.corpus.embedder.get_model", lambda: MockModel())
    res = embed_texts(["some text"])
    assert called == [True]
    assert len(res) == 1
    assert len(res[0]) == 768

def test_lexical_search_works_without_embeddings():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, SourceChunk
    from app.corpus.loader import lexical_search
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        db.add(SourceChunk(source_id=1, chunk_index=0, text="vibration bearing monitoring"))
        db.add(SourceChunk(source_id=1, chunk_index=1, text="additive manufacturing quality control"))
        db.commit()
        
        results = lexical_search(db, "vibration bearing", top_k=5)
        assert len(results) == 1
        assert results[0].text == "vibration bearing monitoring"
    finally:
        db.close()

def test_vector_search_falls_back_gracefully_when_no_embeddings():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base
    from app.corpus.loader import embedding_search
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        results = embedding_search(db, [0.1] * 768, top_k=5)
        assert results == []
    finally:
        db.close()

def test_quote_verification_still_works():
    from app.corpus.verify_quote import verify_quote
    assert verify_quote("bearing defect", "the machine has a bearing defect anomaly")
    assert not verify_quote("unrelated text", "the machine has a bearing defect anomaly")


# ── LLM Provider Migration Tests ─────────────────────────────────────────────

def test_qwen_config_loading(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("LLM_API_KEY", "test-qwen-key")
    monkeypatch.setenv("LLM_MODEL", "qwen-plus")
    
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "qwen"
    assert settings.llm_api_key == "test-qwen-key"
    assert settings.llm_model == "qwen-plus"
    assert settings.llm_base_url == "https://ws-h28trj7vdat6f6dv.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"

def test_groq_switchable(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "groq"
    assert settings.llm_api_key == "test-groq-key"
    assert settings.llm_model == "llama-3.1-8b-instant"
    assert settings.llm_base_url == "https://api.groq.com/openai/v1"

def test_get_llm_client_instantiation(monkeypatch):
    from app.config import Settings
    from app.llm.client import _get_llm_client
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("LLM_API_KEY", "test-qwen-key")
    settings = Settings(_env_file=None)
    client = _get_llm_client(settings)
    assert client.api_key == "test-qwen-key"
    assert str(client.base_url) == "https://ws-h28trj7vdat6f6dv.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/"

def test_extraction_and_json_validation_with_mock(monkeypatch):
    import json
    from app.llm.client import extract_process, get_settings
    
    class MockCompletions:
        def create(self, **kwargs):
            class MockMessage:
                content = json.dumps({
                    "data_availability": {"ordinal_value": 5, "rationale": "High availability", "confidence": 0.9},
                    "process_repeatability": {"ordinal_value": 4, "rationale": "Repetitive steps", "confidence": 0.8},
                    "rule_clarity": {"ordinal_value": 4, "rationale": "Clear rules", "confidence": 0.85},
                    "volume_frequency": {"ordinal_value": 5, "rationale": "High volume", "confidence": 0.95},
                    "digital_maturity": {"ordinal_value": 3, "rationale": "Some systems", "confidence": 0.7},
                    "error_cost_tolerance": {"ordinal_value": 4, "rationale": "Tolerable", "confidence": 0.8},
                    "human_judgment_dependency": {"ordinal_value": 2, "rationale": "Low dependency", "confidence": 0.75},
                    "regulatory_safety_constraint": {"ordinal_value": 1, "rationale": "Unregulated", "confidence": 0.9},
                    "claims": ["Claim A", "Claim B"]
                })
            class MockChoice:
                message = MockMessage()
            class MockResponse:
                choices = [MockChoice()]
            return MockResponse()

    class MockChat:
        completions = MockCompletions()

    class MockOpenAI:
        chat = MockChat()
        api_key = "dummy"
        base_url = "dummy"

    monkeypatch.setattr("app.llm.client._get_llm_client", lambda settings: MockOpenAI())
    monkeypatch.setattr(get_settings(), "extraction_cache_dir", "/tmp/fake_cache_pie_test")
    
    res = extract_process("Test Name", "Test Description", "test_hash_unique_123")
    assert res.data_availability.ordinal_value == 5
    assert res.claims == ["Claim A", "Claim B"]

def test_research_works_with_mock(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, SourceChunk
    from app.pipeline.research import run_research
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    db.add(SourceChunk(source_id=1, chunk_index=0, text="standard operating procedure for bearing failure prediction"))
    db.commit()

    class MockCompletions:
        def create(self, **kwargs):
            class MockMessage:
                content = "bearing failure prediction"
            class MockChoice:
                message = MockMessage()
            class MockResponse:
                choices = [MockChoice()]
            return MockResponse()

    class MockChat:
        completions = MockCompletions()

    class MockOpenAI:
        chat = MockChat()
        api_key = "dummy"
        base_url = "dummy"

    monkeypatch.setattr("app.pipeline.research.OpenAI", lambda *args, **kwargs: MockOpenAI())
    
    try:
        run_research(db, process_id=999, claims=["vibration analysis detects bearing failure"])
        from app.models import Claim
        saved = db.query(Claim).filter(Claim.process_id == 999).first()
        assert saved is not None
        assert saved.supported is True
    finally:
        db.close()


