"""Tests for scoring invariant, dedup, verify_quote, QueryPlan."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.scoring.engine import load_rubric, compute_score
from app.pipeline.normalize import normalize_text, compute_hash
from app.corpus.verify_quote import verify_quote
from app.query.plan import QueryPlan


# ── Scoring invariant ────────────────────────────────────────────────────────

def test_scoring_invariant_all_threes():
    r = load_rubric("v1")
    feat = {k: 3 for k in r["factors"]}
    res = compute_score(feat, r)
    real = [f for f in res.factors if f.factor_key != "override_cap"]
    assert abs(round(sum(f.contribution for f in real), 2) - res.total_score) < 0.01

def test_scoring_invariant_all_ones():
    r = load_rubric("v1")
    feat = {k: 1 for k in r["factors"]}
    res = compute_score(feat, r)
    real = [f for f in res.factors if f.factor_key != "override_cap"]
    assert abs(round(sum(f.contribution for f in real), 2) - res.total_score) < 0.01
    assert res.band == "Human-Led"

def test_scoring_invariant_all_fives():
    r = load_rubric("v1")
    feat = {k: 5 for k in r["factors"]}
    res = compute_score(feat, r)
    real = [f for f in res.factors if f.factor_key != "override_cap"]
    assert abs(round(sum(f.contribution for f in real), 2) - res.total_score) < 0.01

def test_rubric_weights_sum_to_one():
    r = load_rubric("v1")
    total = sum(v["weight"] for v in r["factors"].values())
    assert abs(total - 1.0) < 0.001

def test_band_automate():
    r = load_rubric("v1")
    # Max positive, min negative -> high score
    feat = {k: 5 for k in r["factors"]}
    feat["human_judgment_dependency"] = 1
    feat["regulatory_safety_constraint"] = 1
    res = compute_score(feat, r)
    assert res.band == "Automate"
    assert res.total_score >= 70

def test_band_human_led():
    r = load_rubric("v1")
    feat = {k: 1 for k in r["factors"]}
    feat["human_judgment_dependency"] = 5
    feat["regulatory_safety_constraint"] = 5
    res = compute_score(feat, r)
    assert res.band == "Human-Led"
    assert res.total_score < 45

def test_override_rule_caps_automate():
    r = load_rubric("v1")
    feat = {k: 5 for k in r["factors"]}  # would be Automate
    feat["regulatory_safety_constraint"] = 5
    feat["human_judgment_dependency"] = 4
    res = compute_score(feat, r)
    assert res.band == "Augment"
    assert res.override_applied is True

def test_override_rule_does_not_affect_human_led():
    r = load_rubric("v1")
    feat = {k: 1 for k in r["factors"]}
    feat["regulatory_safety_constraint"] = 5
    feat["human_judgment_dependency"] = 5
    res = compute_score(feat, r)
    # override only caps Automate → Augment; Human-Led stays Human-Led
    assert res.band == "Human-Led"


# ── Dedup / normalize ────────────────────────────────────────────────────────

def test_normalize_lowercases():
    assert normalize_text("HELLO WORLD") == "hello world"

def test_normalize_collapses_whitespace():
    assert normalize_text("hello   world") == "hello world"

def test_normalize_strips_punctuation():
    n = normalize_text("hello, world!")
    assert "," not in n and "!" not in n

def test_dedup_same_content_same_hash():
    h1 = compute_hash(normalize_text("Predictive Maintenance!  Process."))
    h2 = compute_hash(normalize_text("predictive maintenance process"))
    assert h1 == h2

def test_dedup_different_content_different_hash():
    h1 = compute_hash(normalize_text("process alpha"))
    h2 = compute_hash(normalize_text("process beta"))
    assert h1 != h2


# ── verify_quote ─────────────────────────────────────────────────────────────

def test_verify_quote_exact():
    assert verify_quote("machine learning", "Machine Learning models predict failures")

def test_verify_quote_case_insensitive():
    assert verify_quote("PREDICTIVE MAINTENANCE", "predictive maintenance is the process")

def test_verify_quote_whitespace_normalized():
    assert verify_quote("machine  learning", "machine learning models")

def test_verify_quote_not_found():
    assert not verify_quote("unicorn factory", "machine learning models predict failures")

def test_verify_quote_empty_quote():
    assert not verify_quote("", "some text")

def test_verify_quote_empty_chunk():
    assert not verify_quote("something", "")


# ── QueryPlan ────────────────────────────────────────────────────────────────

def test_queryplan_defaults():
    p = QueryPlan(intent="rank_top")
    assert p.limit == 10
    assert p.filters == {}
    assert p.rubric_version == "v1"

def test_queryplan_band_filter():
    p = QueryPlan(intent="filter_by_band", filters={"band": "Automate"})
    assert p.filters["band"] == "Automate"

def test_queryplan_limit_capped():
    # build_plan caps at 50
    from unittest.mock import MagicMock
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    from app.query.plan import build_plan
    plan = build_plan({"intent": "rank_top", "limit": 999}, db)
    assert plan.limit <= 50
