from estc_world_model import Constraint, Entity, Transition, VerdictStatus, WorldModel


def test_refund_allowed_and_committed():
    order = Entity(
        id="order_123",
        type="Order",
        state="Delivered",
        attributes={"days_since_delivery": 5, "refundable": True},
    )
    transition = Transition(
        name="RequestRefund",
        entity_type="Order",
        from_state="Delivered",
        to_state="RefundRequested",
    )
    constraint = Constraint(
        name="RefundWithinSevenDays",
        applies_to="RequestRefund",
        predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
    )
    world = WorldModel(entities=[order], transitions=[transition], constraints=[constraint])

    verdict = world.propose(entity_id="order_123", transition="RequestRefund")

    assert verdict.status == VerdictStatus.ALLOW
    assert verdict.next_state == "RefundRequested"
    assert world.entities["order_123"].state == "RefundRequested"


def test_refund_denied_by_constraint():
    order = Entity(
        id="order_123",
        type="Order",
        state="Delivered",
        attributes={"days_since_delivery": 10, "refundable": True},
    )
    transition = Transition(
        name="RequestRefund",
        entity_type="Order",
        from_state="Delivered",
        to_state="RefundRequested",
    )
    constraint = Constraint(
        name="RefundWithinSevenDays",
        applies_to="RequestRefund",
        description="Refund window exceeded.",
        predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
    )
    world = WorldModel(entities=[order], transitions=[transition], constraints=[constraint])

    verdict = world.propose(entity_id="order_123", transition="RequestRefund")

    assert verdict.status == VerdictStatus.DENY
    assert verdict.rejected_action == "RequestRefund"
    assert world.entities["order_123"].state == "Delivered"


def test_refund_denied_when_duplicate_exists():
    order = Entity(
        id="order_123",
        type="Order",
        state="Delivered",
        attributes={
            "days_since_delivery": 5,
            "refundable": True,
            "refund_status": "requested",
        },
    )
    transition = Transition(
        name="RequestRefund",
        entity_type="Order",
        from_state="Delivered",
        to_state="RefundRequested",
    )
    refund_within_seven_days = Constraint(
        name="RefundWithinSevenDays",
        applies_to="RequestRefund",
        description="Refund window exceeded.",
        predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
    )
    item_is_refundable = Constraint(
        name="ItemIsRefundable",
        applies_to="RequestRefund",
        description="The item must be marked as refundable.",
        predicate=lambda entity: entity.attributes["refundable"] is True,
    )
    no_duplicate_refund = Constraint(
        name="NoDuplicateRefund",
        applies_to="RequestRefund",
        description="A refund request must not already exist.",
        predicate=lambda entity: entity.attributes["refund_status"] == "none",
    )
    world = WorldModel(
        entities=[order],
        transitions=[transition],
        constraints=[refund_within_seven_days, item_is_refundable, no_duplicate_refund],
    )

    verdict = world.propose(entity_id="order_123", transition="RequestRefund")

    assert verdict.status == VerdictStatus.DENY
    assert verdict.rejected_action == "RequestRefund"
    assert world.entities["order_123"].state == "Delivered"
    assert any(result.name == "NoDuplicateRefund" and not result.passed for result in verdict.guard_result)
