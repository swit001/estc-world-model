from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class VerdictStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


class Entity(BaseModel):
    """An executable object in the world model."""

    id: str
    type: str
    state: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Transition(BaseModel):
    """A permitted state-changing path for an entity type."""

    name: str
    entity_type: str
    from_state: str
    to_state: str
    description: Optional[str] = None


class GuardResult(BaseModel):
    """Structured result of a constraint or guard evaluation."""

    name: str
    passed: bool
    reason: Optional[str] = None


class Constraint(BaseModel):
    """A symbolic rule that decides whether a transition may proceed.

    The predicate is intentionally excluded from serialization because it is
    executable Python logic. For YAML/JSON-based worlds, compile declarative
    rules into predicates before runtime.
    """

    name: str
    applies_to: str
    description: Optional[str] = None
    on_violation: VerdictStatus = VerdictStatus.DENY
    predicate: Callable[[Entity], bool] = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def evaluate(self, entity: Entity) -> GuardResult:
        try:
            passed = bool(self.predicate(entity))
            return GuardResult(
                name=self.name,
                passed=passed,
                reason=None if passed else self.description,
            )
        except Exception as exc:  # pragma: no cover - defensive path
            return GuardResult(
                name=self.name,
                passed=False,
                reason=f"Constraint evaluation failed: {exc}",
            )


class CommittedState(BaseModel):
    entity_id: str
    entity_type: str
    previous_state: str
    current_state: str
    committed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VerdictOutcome(BaseModel):
    """The formal decision returned by the world model runtime."""

    status: VerdictStatus
    requested_transition: str
    entity_id: str
    approved_action: Optional[str] = None
    rejected_action: Optional[str] = None
    next_state: Optional[str] = None
    guards_passed: List[str] = Field(default_factory=list)
    guard_result: List[GuardResult] = Field(default_factory=list)
    committed_state: Optional[CommittedState] = None
    alternatives: List[str] = Field(default_factory=list)
    audit_ref: str = Field(default_factory=lambda: f"audit_{uuid4().hex[:12]}")
    message: Optional[str] = None
