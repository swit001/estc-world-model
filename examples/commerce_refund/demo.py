from estc_world_model import Constraint, Entity, Transition, VerdictStatus, WorldModel


order = Entity(
    id="order_123",
    type="Order",
    state="Delivered",
    attributes={
        "days_since_delivery": 5,
        "refundable": True,
        "refund_status": "none",
    },
)

request_refund = Transition(
    name="RequestRefund",
    entity_type="Order",
    from_state="Delivered",
    to_state="RefundRequested",
    description="Customer requests a refund after delivery.",
)

refund_within_seven_days = Constraint(
    name="RefundWithinSevenDays",
    applies_to="RequestRefund",
    description="Refunds are allowed only within 7 days after delivery.",
    on_violation=VerdictStatus.DENY,
    predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
)

item_is_refundable = Constraint(
    name="ItemIsRefundable",
    applies_to="RequestRefund",
    description="The item must be marked as refundable.",
    on_violation=VerdictStatus.DENY,
    predicate=lambda entity: entity.attributes["refundable"] is True,
)

no_duplicate_refund = Constraint(
    name="NoDuplicateRefund",
    applies_to="RequestRefund",
    description="A refund request must not already exist.",
    on_violation=VerdictStatus.DENY,
    predicate=lambda entity: entity.attributes["refund_status"] == "none",
)

world = WorldModel(
    entities=[order],
    transitions=[request_refund],
    constraints=[refund_within_seven_days, item_is_refundable, no_duplicate_refund],
)

verdict = world.propose(
    entity_id="order_123",
    transition="RequestRefund",
    requested_by="customer_456",
)

print(verdict.model_dump_json(indent=2))
