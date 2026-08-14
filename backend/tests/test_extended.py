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
