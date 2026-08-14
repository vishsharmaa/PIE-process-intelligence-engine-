"""
Groq-only LLM client.
- Uses OpenAI-compatible API (https://api.groq.com/openai/v1)
- JSON mode with Pydantic schema validation
- One repair retry on invalid JSON
- Exponential backoff on 429/timeout (max 2 retries, NEVER falls back to another provider)
- On-disk extraction cache keyed by SHA-256 of (normalized_text + model + prompt_version)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Optional

from openai import OpenAI, RateLimitError, APITimeoutError, APIError
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import ExtractionResult

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You are an AI-potential analyst for manufacturing and industrial operations.
You analyze process descriptions and rate each factor using a strict 1-5 ordinal scale.
You respond ONLY with valid JSON — no explanations outside the JSON structure."""

EXTRACTION_TEMPLATE = """Analyze the following manufacturing/industrial process and rate each factor.

PROCESS NAME: {name}
PROCESS DESCRIPTION:
{description}

Rate each factor from 1 (lowest) to 5 (highest) with a rationale (1-2 sentences) and confidence (0.0-1.0):

Factor definitions:
- data_availability (1=no structured data, 5=rich structured data streams)
- process_repeatability (1=highly variable/creative, 5=fully standardized & repetitive)
- rule_clarity (1=ambiguous/expert judgment required, 5=explicit rules cover all cases)
- volume_frequency (1=rare/low volume, 5=continuous/very high volume)
- digital_maturity (1=paper-based, 5=fully digital with sensors/systems)
- error_cost_tolerance (1=zero tolerance/life-critical, 5=highly tolerant/easy to correct)
- human_judgment_dependency (1=fully algorithmic, 5=deep expertise required at every step)
- regulatory_safety_constraint (1=no regulation, 5=heavily regulated/safety-critical)

Also provide up to 5 factual, verifiable claims about this process that could be checked against industry documentation.

Respond ONLY with this exact JSON structure:
{{
  "data_availability": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "process_repeatability": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "rule_clarity": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "volume_frequency": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "digital_maturity": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "error_cost_tolerance": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "human_judgment_dependency": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "regulatory_safety_constraint": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "claims": ["<claim1>", "<claim2>", "<claim3>"]
}}"""

REPAIR_TEMPLATE = """Your previous response was not valid JSON or did not match the required schema.

Error: {error}

Previous response:
{raw_response}

Please respond with ONLY valid JSON matching this exact schema (no other text):
{{
  "data_availability": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "process_repeatability": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "rule_clarity": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "volume_frequency": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "digital_maturity": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "error_cost_tolerance": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "human_judgment_dependency": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "regulatory_safety_constraint": {{"ordinal_value": <1-5>, "rationale": "<text>", "confidence": <0.0-1.0>}},
  "claims": ["<claim1>", "<claim2>"]
}}"""


def _get_cache_path(cache_dir: str, cache_key: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{cache_key}.json")


def _cache_key(normalized_text: str, model: str, prompt_version: str) -> str:
    payload = f"{model}::{prompt_version}::{normalized_text}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _load_from_cache(cache_dir: str, key: str) -> Optional[ExtractionResult]:
    path = _get_cache_path(cache_dir, key)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return ExtractionResult(**data)
        except Exception as e:
            logger.warning(f"Cache load failed for {key}: {e}")
    return None


def _save_to_cache(cache_dir: str, key: str, result: ExtractionResult) -> None:
    path = _get_cache_path(cache_dir, key)
    try:
        with open(path, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
    except Exception as e:
        logger.warning(f"Cache save failed for {key}: {e}")


def _parse_extraction(raw: str) -> ExtractionResult:
    """Parse and validate LLM response. Raises ValueError with details on failure."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}") from e
    try:
        return ExtractionResult(**data)
    except (ValidationError, TypeError) as e:
        raise ValueError(f"Schema validation error: {e}") from e


def _call_groq(
    client: OpenAI,
    model: str,
    messages: list[dict],
    timeout: float = 60.0,
) -> str:
    """Single Groq API call with JSON mode. Returns raw string content."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,
        timeout=timeout,
    )
    return response.choices[0].message.content or ""


def extract_process(
    name: str,
    description: str,
    normalized_text: str,
) -> ExtractionResult:
    """
    Extract rubric features for a process using Groq.
    Uses on-disk cache; falls back to API call.
    NEVER falls back to any other provider.
    """
    settings = get_settings()
    model = settings.groq_model
    cache_dir = settings.extraction_cache_dir

    key = _cache_key(normalized_text, model, PROMPT_VERSION)
    cached = _load_from_cache(cache_dir, key)
    if cached is not None:
        logger.info(f"Extraction cache hit for key {key[:8]}…")
        return cached

    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    prompt = EXTRACTION_TEMPLATE.format(name=name, description=description)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    raw_response: str = ""
    last_error: Optional[Exception] = None

    # Initial call + up to 2 retries for rate limit / timeout
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            raw_response = _call_groq(client, model, messages)
            break
        except RateLimitError as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** (attempt + 2)  # 4s, 8s
                logger.warning(f"Groq 429 (attempt {attempt+1}), waiting {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(
                    "Groq rate limit exceeded after retries. "
                    "Not falling back to any other provider. "
                    "Wait and retry."
                ) from e
        except APITimeoutError as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(f"Groq timeout (attempt {attempt+1}), waiting {wait}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(
                    "Groq timeout after retries. Not falling back to any other provider."
                ) from e
        except APIError as e:
            raise RuntimeError(f"Groq API error: {e}") from e

    # Try to parse
    try:
        result = _parse_extraction(raw_response)
        _save_to_cache(cache_dir, key, result)
        return result
    except ValueError as parse_err:
        logger.warning(f"First parse failed: {parse_err}. Attempting repair…")

    # One repair retry
    repair_messages = messages + [
        {"role": "assistant", "content": raw_response},
        {"role": "user", "content": REPAIR_TEMPLATE.format(
            error=str(parse_err), raw_response=raw_response[:500]
        )},
    ]
    try:
        repaired_raw = _call_groq(client, model, repair_messages)
        result = _parse_extraction(repaired_raw)
        _save_to_cache(cache_dir, key, result)
        return result
    except (ValueError, RateLimitError, APITimeoutError, APIError) as e:
        raise RuntimeError(
            f"Extraction failed after repair attempt: {e}. "
            f"Raw response: {raw_response[:200]}"
        ) from e


def classify_intent(question: str) -> dict:
    """
    Classify a natural-language question into a closed intent label.
    Returns dict with 'intent' and extracted parameters.
    """
    settings = get_settings()
    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    system = (
        "You are a query router for a manufacturing process intelligence system. "
        "Classify the user's question into exactly one of these intents:\n"
        "- rank_top: user wants top/bottom N processes by score\n"
        "- filter_by_band: user wants processes in a specific band (Automate/Augment/Human-Led)\n"
        "- explain_process: user wants explanation of a specific process score\n"
        "- portfolio_stats: user wants overall statistics or distribution\n"
        "- compare: user wants to compare two processes\n"
        "- open_research: user asks an open-ended question about process automation\n"
        "- unmappable: question cannot be answered by this system\n"
        "\nRespond ONLY with JSON."
    )
    user_msg = f"""Question: {question}

Respond with JSON:
{{
  "intent": "<one of the intent labels>",
  "limit": <integer, default 10>,
  "band": "<Automate|Augment|Human-Led|null>",
  "process_name_hint": "<partial process name if mentioned, else null>",
  "sort": "<score_desc|score_asc|null>",
  "target_process_id": <integer if specific process id mentioned, else null>
}}"""

    for attempt in range(3):
        try:
            raw = _call_groq(client, settings.groq_model, [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ], timeout=30.0)
            data = json.loads(raw)
            # Validate intent is in allowed set
            allowed = {"rank_top", "filter_by_band", "explain_process",
                       "portfolio_stats", "compare", "open_research", "unmappable"}
            if data.get("intent") not in allowed:
                data["intent"] = "unmappable"
            return data
        except (RateLimitError, APITimeoutError):
            if attempt < 2:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning(f"Intent classification error: {e}")
            break

    return {"intent": "unmappable"}


def explain_result(question: str, result_json: str) -> str:
    """
    Generate a 2-3 sentence prose explanation of an already-computed result.
    The LLM explains numbers it is given — it does NOT compute anything.
    """
    settings = get_settings()
    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    system = (
        "You are explaining pre-computed manufacturing process intelligence data to a business user. "
        "Write 2-3 clear sentences. Do not invent or modify any numbers. "
        "Only explain what is in the data provided."
    )
    user_msg = f"Question: {question}\n\nData:\n{result_json}\n\nWrite a 2-3 sentence explanation."

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            timeout=30.0,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.warning(f"Explanation generation failed: {e}")
        return ""
