import pytest
from pathlib import Path

from estc_world_model import (
    Entity,
    RuleParseError,
    VerdictStatus,
    compile_rule,
    load_world_from_yaml,
)

WORLD_YAML = Path(__file__).parent.parent / "examples" / "commerce_refund" / "world.yaml"


# ---------------------------------------------------------------------------
# compile_rule — safe parser
# ---------------------------------------------------------------------------


class TestCompileRule:
    def _entity(self, **attrs) -> Entity:
        return Entity(id="e1", type="T", state="S", attributes=attrs)

    def test_int_lte_passes(self):
        pred = compile_rule("days_since_delivery <= 7")
        assert pred(self._entity(days_since_delivery=5)) is True

    def test_int_lte_fails(self):
        pred = compile_rule("days_since_delivery <= 7")
        assert pred(self._entity(days_since_delivery=10)) is False

    def test_int_lt(self):
        pred = compile_rule("retry_count < 3")
        assert pred(self._entity(retry_count=2)) is True
        assert pred(self._entity(retry_count=3)) is False

    def test_int_gte(self):
        pred = compile_rule("order_amount >= 100")
        assert pred(self._entity(order_amount=100)) is True
        assert pred(self._entity(order_amount=99)) is False

    def test_int_gt(self):
        pred = compile_rule("score > 0")
        assert pred(self._entity(score=1)) is True
        assert pred(self._entity(score=0)) is False

    def test_bool_true(self):
        pred = compile_rule("item_refundable == true")
        assert pred(self._entity(item_refundable=True)) is True
        assert pred(self._entity(item_refundable=False)) is False

    def test_bool_false(self):
        pred = compile_rule("is_blocked == false")
        assert pred(self._entity(is_blocked=False)) is True
        assert pred(self._entity(is_blocked=True)) is False

    def test_string_eq(self):
        pred = compile_rule("refund_status == none")
        assert pred(self._entity(refund_status="none")) is True
        assert pred(self._entity(refund_status="requested")) is False

    def test_string_neq(self):
        pred = compile_rule("status != blocked")
        assert pred(self._entity(status="active")) is True
        assert pred(self._entity(status="blocked")) is False

    def test_float_value(self):
        pred = compile_rule("confidence >= 0.7")
        assert pred(self._entity(confidence=0.74)) is True
        assert pred(self._entity(confidence=0.5)) is False

    def test_extra_whitespace(self):
        pred = compile_rule("  score  >=  0.8  ")
        assert pred(self._entity(score=0.9)) is True

    def test_invalid_rule_raises(self):
        with pytest.raises(RuleParseError):
            compile_rule("days_since_delivery <= 7 && refund_status == none")

    def test_missing_operator_raises(self):
        with pytest.raises(RuleParseError):
            compile_rule("just_a_field")


# ---------------------------------------------------------------------------
# load_world_from_yaml
# ---------------------------------------------------------------------------


class TestLoadWorldFromYaml:
    def _order(self, **attrs) -> Entity:
        defaults = {
            "days_since_delivery": 5,
            "item_refundable": True,
            "refund_status": "none",
        }
        defaults.update(attrs)
        return Entity(id="order_123", type="Order", state="Delivered", attributes=defaults)

    def test_loads_transitions(self):
        world = load_world_from_yaml(WORLD_YAML, entities=[self._order()])
        assert "RequestRefund" in world.transitions
        assert "ApproveRefund" in world.transitions
        assert "RejectRefund" in world.transitions

    def test_loads_constraints(self):
        world = load_world_from_yaml(WORLD_YAML, entities=[self._order()])
        constraint_names = [c.name for c in world.constraints]
        assert "RefundWithinSevenDays" in constraint_names
        assert "ItemIsRefundable" in constraint_names
        assert "NoDuplicateRefund" in constraint_names

    def test_allow_verdict(self):
        world = load_world_from_yaml(WORLD_YAML, entities=[self._order()])
        verdict = world.propose(entity_id="order_123", transition="RequestRefund")
        assert verdict.status == VerdictStatus.ALLOW
        assert verdict.next_state == "RefundRequested"

    def test_deny_refund_window_exceeded(self):
        order = self._order(days_since_delivery=10)
        world = load_world_from_yaml(WORLD_YAML, entities=[order])
        verdict = world.propose(entity_id="order_123", transition="RequestRefund")
        assert verdict.status == VerdictStatus.DENY
        failed = [g.name for g in verdict.guard_result if not g.passed]
        assert "RefundWithinSevenDays" in failed

    def test_deny_item_not_refundable(self):
        order = self._order(item_refundable=False)
        world = load_world_from_yaml(WORLD_YAML, entities=[order])
        verdict = world.propose(entity_id="order_123", transition="RequestRefund")
        assert verdict.status == VerdictStatus.DENY
        failed = [g.name for g in verdict.guard_result if not g.passed]
        assert "ItemIsRefundable" in failed

    def test_deny_duplicate_refund(self):
        order = self._order(refund_status="requested")
        world = load_world_from_yaml(WORLD_YAML, entities=[order])
        verdict = world.propose(entity_id="order_123", transition="RequestRefund")
        assert verdict.status == VerdictStatus.DENY
        failed = [g.name for g in verdict.guard_result if not g.passed]
        assert "NoDuplicateRefund" in failed

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_world_from_yaml(tmp_path / "nonexistent.yaml")

    def test_empty_entities_loads_world(self):
        world = load_world_from_yaml(WORLD_YAML)
        assert len(world.transitions) == 3
        assert len(world.constraints) == 3
