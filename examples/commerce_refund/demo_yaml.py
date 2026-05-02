from pathlib import Path

from estc_world_model import Entity, load_world_from_yaml

WORLD_FILE = Path(__file__).parent / "world.yaml"

order = Entity(
    id="order_123",
    type="Order",
    state="Delivered",
    attributes={
        "days_since_delivery": 5,
        "item_refundable": True,
        "refund_status": "none",
    },
)

world = load_world_from_yaml(WORLD_FILE, entities=[order])

verdict = world.propose(
    entity_id="order_123",
    transition="RequestRefund",
    requested_by="customer_456",
)

print(verdict.model_dump_json(indent=2))
