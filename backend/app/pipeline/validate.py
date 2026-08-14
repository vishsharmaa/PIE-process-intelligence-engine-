"""Pipeline stage: validate process input."""
from __future__ import annotations


class ValidationError(Exception):
    pass


def validate(name: str, description: str) -> None:
    """Validate process input. Raises ValidationError on failure."""
    if not name or not name.strip():
        raise ValidationError("Process name cannot be empty.")
    if len(name.strip()) > 256:
        raise ValidationError("Process name exceeds 256 characters.")
    if not description or not description.strip():
        raise ValidationError("Process description cannot be empty.")
    if len(description.strip()) < 20:
        raise ValidationError("Process description must be at least 20 characters.")
