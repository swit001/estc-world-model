from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .models import (
    CommittedState,
    Constraint,
    Entity,
    GuardResult,
    Transition,
    VerdictOutcome,
    VerdictStatus,
)


class WorldModel:
    """Minimal ESTC runtime.

    The world model receives a transition candidate, checks that it belongs to
    the declared transition space, evaluates constraints, commits the state if
    allowed, and returns a structured VerdictOutcome.
    """

    def __init__(
        self,
        *,
        entities: Iterable[Entity],
        transitions: Iterable[Transition],
        constraints: Optional[Iterable[Constraint]] = None,
    ) -> None:
        self.entities: Dict[str, Entity] = {entity.id: entity for entity in entities}
        self.transitions: Dict[str, Transition] = {
            transition.name: transition for transition in transitions
        }
        self.constraints: List[Constraint] = list(constraints or [])

    def propose(self, *, entity_id: str, transition: str, requested_by: Optional[str] = None) -> VerdictOutcome:
        """Evaluate an agent-proposed transition candidate."""

        entity = self.entities.get(entity_id)
        if entity is None:
            return VerdictOutcome(
                status=VerdictStatus.DENY,
                requested_transition=transition,
                entity_id=entity_id,
                rejected_action=transition,
                message=f"Entity not found: {entity_id}",
            )

        transition_spec = self.transitions.get(transition)
        if transition_spec is None:
            return VerdictOutcome(
                status=VerdictStatus.DENY,
                requested_transition=transition,
                entity_id=entity_id,
                rejected_action=transition,
                alternatives=self._available_transitions(entity),
                message=f"Transition is not declared in this world: {transition}",
            )

        if transition_spec.entity_type != entity.type:
            return VerdictOutcome(
                status=VerdictStatus.DENY,
                requested_transition=transition,
                entity_id=entity_id,
                rejected_action=transition,
                alternatives=self._available_transitions(entity),
                message=(
                    f"Transition {transition} applies to {transition_spec.entity_type}, "
                    f"not {entity.type}."
                ),
            )

        if transition_spec.from_state != entity.state:
            return VerdictOutcome(
                status=VerdictStatus.DENY,
                requested_transition=transition,
                entity_id=entity_id,
                rejected_action=transition,
                alternatives=self._available_transitions(entity),
                message=(
                    f"Transition {transition} requires state {transition_spec.from_state}, "
                    f"but entity is in state {entity.state}."
                ),
            )

        guard_results = [
            constraint.evaluate(entity)
            for constraint in self.constraints
            if constraint.applies_to == transition
        ]

        failed_guards = [result for result in guard_results if not result.passed]
        if failed_guards:
            status = self._violation_status(transition)
            return VerdictOutcome(
                status=status,
                requested_transition=transition,
                entity_id=entity_id,
                rejected_action=transition,
                guard_result=guard_results,
                guards_passed=[result.name for result in guard_results if result.passed],
                alternatives=self._available_transitions(entity, exclude=transition),
                message="Transition failed one or more constraints.",
            )

        previous_state = entity.state
        entity.state = transition_spec.to_state
        committed_state = CommittedState(
            entity_id=entity.id,
            entity_type=entity.type,
            previous_state=previous_state,
            current_state=entity.state,
        )

        return VerdictOutcome(
            status=VerdictStatus.ALLOW,
            requested_transition=transition,
            entity_id=entity_id,
            approved_action=transition,
            next_state=entity.state,
            guards_passed=[result.name for result in guard_results if result.passed],
            guard_result=guard_results,
            committed_state=committed_state,
            message=f"Transition committed by {requested_by or 'unknown principal'}.",
        )

    def _available_transitions(self, entity: Entity, exclude: Optional[str] = None) -> List[str]:
        return [
            transition.name
            for transition in self.transitions.values()
            if transition.entity_type == entity.type
            and transition.from_state == entity.state
            and transition.name != exclude
        ]

    def _violation_status(self, transition: str) -> VerdictStatus:
        matching = [constraint for constraint in self.constraints if constraint.applies_to == transition]
        if any(constraint.on_violation == VerdictStatus.ESCALATE for constraint in matching):
            return VerdictStatus.ESCALATE
        return VerdictStatus.DENY
