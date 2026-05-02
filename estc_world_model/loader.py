from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PyYAML is required for YAML world loading. "
        "Install it with: pip install pyyaml"
    ) from exc

from .models import Constraint, Entity, Transition, VerdictStatus
from .parser import RuleParseError, compile_rule
from .runtime import WorldModel


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_world_from_yaml(
    source: Union[str, Path],
    *,
    entities: Optional[Iterable[Entity]] = None,
) -> WorldModel:
    """Load a WorldModel from a YAML world definition file.

    The YAML file declares transitions and constraints. Entities represent
    live runtime state and are supplied separately (they are not part of the
    static world definition).

    Args:
        source: Path to a ``.world.yaml`` or ``.yaml`` file.
        entities: Optional initial entities. When omitted an empty world is
            returned (useful for validation-only workflows).

    Returns:
        A fully configured :class:`WorldModel` ready to call ``propose()`` on.

    Raises:
        FileNotFoundError: if *source* does not exist.
        yaml.YAMLError: if the file is not valid YAML.
        RuleParseError: if a constraint rule cannot be parsed.
        ValueError: if required fields are missing in the YAML.
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"World file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        data: Dict[str, Any] = yaml.safe_load(fh)

    transitions = _load_transitions(data)
    constraints = _load_constraints(data)

    return WorldModel(
        entities=list(entities or []),
        transitions=transitions,
        constraints=constraints,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_transitions(data: Dict[str, Any]) -> list[Transition]:
    raw = data.get("transitions") or []
    transitions: list[Transition] = []

    for item in raw:
        _require_keys(item, ("name", "entity_type", "from_state", "to_state"), "transition")
        transitions.append(
            Transition(
                name=item["name"],
                entity_type=item["entity_type"],
                from_state=item["from_state"],
                to_state=item["to_state"],
                description=item.get("description"),
            )
        )

    return transitions


def _load_constraints(data: Dict[str, Any]) -> list[Constraint]:
    raw = data.get("constraints") or []
    constraints: list[Constraint] = []

    for item in raw:
        _require_keys(item, ("name", "applies_to", "rule"), "constraint")

        rule_str: str = item["rule"]
        predicate = compile_rule(rule_str)

        on_violation_raw: str = item.get("on_violation", "DENY").upper()
        try:
            on_violation = VerdictStatus(on_violation_raw)
        except ValueError:
            raise ValueError(
                f"Invalid on_violation value: {on_violation_raw!r}. "
                f"Must be one of: {[s.value for s in VerdictStatus]}."
            )

        constraints.append(
            Constraint(
                name=item["name"],
                applies_to=item["applies_to"],
                description=item.get("description", rule_str),
                on_violation=on_violation,
                predicate=predicate,
            )
        )

    return constraints


def _require_keys(
    item: Dict[str, Any], keys: tuple[str, ...], section: str
) -> None:
    for key in keys:
        if key not in item:
            raise ValueError(
                f"Missing required field {key!r} in {section}: {item!r}"
            )
