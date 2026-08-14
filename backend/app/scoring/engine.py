"""
Scoring engine: loads rubric YAML, computes scores deterministically.
No LLM involvement — pure Python + YAML.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Optional
import yaml


RUBRIC_DIR = os.path.join(os.path.dirname(__file__))


@dataclass
class FactorResult:
    factor_key: str
    feature_value: float        # ordinal 1–5
    weight: float
    contribution: float         # weight * signed * 100
    direction: str              # '+' or '-'
    normalized_value: float
    signed_value: float


@dataclass
class ScoreResult:
    total_score: float          # 0..100, rounded to 2dp
    band: str                   # Automate / Augment / Human-Led
    recommendation: str         # same as band
    recommendation_text: str
    factors: list[FactorResult] = field(default_factory=list)
    override_applied: bool = False
    inputs_hash: str = ""


def load_rubric(version: str = "v1") -> dict:
    """Load and validate a rubric YAML file. Raises on invalid weights."""
    path = os.path.join(RUBRIC_DIR, f"rubric_{version}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Rubric file not found: {path}")
    with open(path, "r") as f:
        rubric = yaml.safe_load(f)

    factors = rubric.get("factors", {})
    total_weight = sum(v["weight"] for v in factors.values())
    if abs(total_weight - 1.0) > 0.001:
        raise ValueError(
            f"Rubric {version} weights sum to {total_weight:.4f}, must be 1.0 ± 0.001"
        )
    rubric["version"] = version
    return rubric


def compute_score(features: dict[str, int], rubric: dict) -> ScoreResult:
    """
    Compute a deterministic AI-potential score from ordinal feature values.

    Args:
        features: dict mapping factor_key -> ordinal (1–5)
        rubric: loaded rubric dict from load_rubric()

    Returns:
        ScoreResult with total_score, band, factors, recommendation_text
    """
    factor_defs = rubric["factors"]
    override_cfg = rubric.get("override", {})

    factor_results: list[FactorResult] = []

    for key, fdef in factor_defs.items():
        ordinal = features.get(key, 3)  # default middle if missing
        ordinal = max(1, min(5, int(ordinal)))
        weight = fdef["weight"]
        direction = fdef["direction"]

        normalized = (ordinal - 1) / 4.0         # 0..1
        signed = normalized if direction == "+" else (1.0 - normalized)
        contribution = weight * signed * 100.0

        factor_results.append(FactorResult(
            factor_key=key,
            feature_value=float(ordinal),
            weight=weight,
            contribution=contribution,
            direction=direction,
            normalized_value=normalized,
            signed_value=signed,
        ))

    total_score = round(sum(f.contribution for f in factor_results), 2)

    # Determine band
    automate_threshold = rubric["bands"]["automate_threshold"]
    augment_threshold = rubric["bands"]["augment_threshold"]

    if total_score >= automate_threshold:
        band = "Automate"
    elif total_score >= augment_threshold:
        band = "Augment"
    else:
        band = "Human-Led"

    # Hard override rule
    override_applied = False
    if override_cfg:
        reg_val = features.get("regulatory_safety_constraint", 1)
        hj_val = features.get("human_judgment_dependency", 1)
        req_reg = override_cfg.get("regulatory_safety_constraint_eq", 5)
        req_hj = override_cfg.get("human_judgment_dependency_gte", 4)
        if reg_val == req_reg and hj_val >= req_hj and band == "Automate":
            band = override_cfg.get("cap_band", "Augment")
            override_applied = True
            # Record override as a named factor row
            factor_results.append(FactorResult(
                factor_key="override_cap",
                feature_value=0.0,
                weight=0.0,
                contribution=0.0,
                direction="cap",
                normalized_value=0.0,
                signed_value=0.0,
            ))

    recommendation = band

    # Build recommendation text from top-3 contributing and top-2 blocking factors
    recommendation_text = _build_recommendation_text(band, factor_results, total_score, override_applied)

    # Compute inputs_hash
    sorted_features = sorted(features.items())
    inputs_hash = hashlib.sha256(
        json.dumps(sorted_features).encode()
    ).hexdigest()

    result = ScoreResult(
        total_score=total_score,
        band=band,
        recommendation=recommendation,
        recommendation_text=recommendation_text,
        factors=factor_results,
        override_applied=override_applied,
        inputs_hash=inputs_hash,
    )

    # Invariant check
    real_factors = [f for f in factor_results if f.factor_key != "override_cap"]
    factor_sum = round(sum(f.contribution for f in real_factors), 2)
    assert abs(factor_sum - total_score) < 0.01, (
        f"Score invariant violated: sum(contributions)={factor_sum} != total_score={total_score}"
    )

    return result


def _build_recommendation_text(
    band: str,
    factors: list[FactorResult],
    total_score: float,
    override_applied: bool,
) -> str:
    """Build deterministic recommendation text from factors. Never LLM-generated."""
    real_factors = [f for f in factors if f.factor_key != "override_cap"]

    # Sort by contribution descending for top contributors
    sorted_by_contribution = sorted(real_factors, key=lambda f: f.contribution, reverse=True)
    top_3 = sorted_by_contribution[:3]

    # Blocking factors: negative-direction factors with low ordinal (high blocking effect)
    # or positive-direction factors with low ordinal (low contribution)
    blocking = sorted(real_factors, key=lambda f: f.contribution)[:2]

    band_text = {
        "Automate": "This process is a strong candidate for automation.",
        "Augment": "This process is best handled with AI augmentation supporting human decision-making.",
        "Human-Led": "This process should remain primarily human-led, with limited AI assistance.",
    }.get(band, "Recommendation pending.")

    contributors_text = ", ".join(
        f"{_factor_label(f.factor_key)} ({f.contribution:.1f}pts)"
        for f in top_3
        if f.factor_key != "override_cap"
    )

    blockers_text = ", ".join(
        f"{_factor_label(f.factor_key)} ({f.contribution:.1f}pts)"
        for f in blocking
        if f.factor_key != "override_cap"
    )

    text = f"{band_text} Score: {total_score:.1f}/100."
    if contributors_text:
        text += f" Key drivers: {contributors_text}."
    if blockers_text:
        text += f" Constraints: {blockers_text}."
    if override_applied:
        text += (
            " Note: Band capped at Augment due to high regulatory/safety constraint "
            "combined with high human judgment dependency."
        )
    return text


def _factor_label(key: str) -> str:
    labels = {
        "data_availability": "Data Availability",
        "process_repeatability": "Process Repeatability",
        "rule_clarity": "Rule Clarity",
        "volume_frequency": "Volume/Frequency",
        "digital_maturity": "Digital Maturity",
        "error_cost_tolerance": "Error Tolerance",
        "human_judgment_dependency": "Human Judgment",
        "regulatory_safety_constraint": "Regulatory Constraint",
        "override_cap": "Override Cap",
    }
    return labels.get(key, key.replace("_", " ").title())
