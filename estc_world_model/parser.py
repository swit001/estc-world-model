from __future__ import annotations

import re
from typing import Callable

from .models import Entity

# ---------------------------------------------------------------------------
# Supported operators (v0.2.0)
# Syntax: field operator value
# field    — an attribute key on entity.attributes
# operator — one of: == != <= >= < >
# value    — number, boolean (true/false), or bare string (no quotes required)
# ---------------------------------------------------------------------------

_OPERATOR_RE = re.compile(
    r"^(?P<field>\w+)\s*(?P<op>==|!=|<=|>=|<|>)\s*(?P<value>.+)$"
)

_OPERATORS: dict[str, Callable[[object, object], bool]] = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
    "<":  lambda a, b: a < b,
    ">":  lambda a, b: a > b,
}


class RuleParseError(ValueError):
    """Raised when a constraint rule string cannot be parsed."""


def _coerce_value(raw: str) -> object:
    """Coerce a raw string token to the appropriate Python type.

    Recognised types (in order):
    - boolean literals:  true / false  (case-insensitive)
    - integer
    - float
    - bare string (everything else — quotes are not required in YAML values)
    """
    stripped = raw.strip()
    lower = stripped.lower()

    if lower == "true":
        return True
    if lower == "false":
        return False

    try:
        return int(stripped)
    except ValueError:
        pass

    try:
        return float(stripped)
    except ValueError:
        pass

    # Strip optional surrounding quotes that may appear in YAML inline values.
    if (stripped.startswith('"') and stripped.endswith('"')) or (
        stripped.startswith("'") and stripped.endswith("'")
    ):
        return stripped[1:-1]

    return stripped


def compile_rule(rule: str) -> Callable[[Entity], bool]:
    """Parse a rule string into an executable predicate.

    Supported syntax::

        field operator value

    Examples::

        days_since_delivery <= 7
        refund_status == none
        item_refundable == true
        score > 0.8

    No ``eval()`` is used. The rule is parsed into an explicit Python callable.

    Raises:
        RuleParseError: if the rule does not match the supported syntax.
    """
    stripped_rule = rule.strip()

    if "&&" in stripped_rule or "||" in stripped_rule:
        raise RuleParseError(
            f"Compound rules are not supported in v0.2.0: {rule!r}. "
            "Use one condition per constraint. Compound support is planned for v0.3."
        )

    match = _OPERATOR_RE.match(stripped_rule)
    if not match:
        raise RuleParseError(
            f"Cannot parse rule: {rule!r}. "
            "Expected format: 'field operator value' "
            "(operators: ==, !=, <=, >=, <, >)."
        )

    field = match.group("field")
    op_str = match.group("op")
    expected = _coerce_value(match.group("value"))
    op_fn = _OPERATORS[op_str]

    def predicate(entity: Entity) -> bool:
        actual = entity.attributes.get(field)
        return bool(op_fn(actual, expected))

    predicate.__doc__ = f"rule: {rule.strip()}"
    return predicate
