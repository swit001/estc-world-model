from __future__ import annotations

from typing import Any

from .models import VerdictOutcome, WorldSpec


def world_schema() -> dict[str, Any]:
    """Return JSON Schema for world.yaml validation."""
    return WorldSpec.model_json_schema()


def verdict_schema() -> dict[str, Any]:
    """Return JSON Schema for the VerdictOutcome runtime contract."""
    return VerdictOutcome.model_json_schema()
