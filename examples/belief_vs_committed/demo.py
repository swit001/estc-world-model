from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

"""
Belief vs Committed State — NWM → SWM demo.

The neural layer (NWM) interprets a customer request and believes the order is
Delivered. It proposes RequestRefund. The symbolic world (SWM) loads the
committed state from the SSOT, finds the order is actually Shipped, and denies
the transition. The committed state remains Shipped.
"""
from pathlib import Path

from estc_world_model import Entity, load_world_from_yaml

WORLD_FILE = Path(__file__).parent / "world.yaml"

# --- Neural belief (NWM output) ---
neural_belief = {
    "entity": "Order",
    "belief_state": "Delivered",
    "proposed_transition": "RequestRefund",
    "confidence": 0.82,
    "reason": "Customer says the package arrived yesterday and wants a refund.",
}

# --- Committed state (SSOT) ---
committed = {
    "entity": "Order",
    "committed_state": "Shipped",
    "source": "SSOT",
}

# --- SWM: load world and validate against committed state ---
order = Entity(
    id="order_001",
    type="Order",
    state=committed["committed_state"],
    attributes={
        "refund_window_days": 1,
        "item_refundable": True,
    },
)

world = load_world_from_yaml(WORLD_FILE, entities=[order])

verdict = world.propose(
    entity_id="order_001",
    transition=neural_belief["proposed_transition"],
    requested_by="neural_layer",
)

# --- Derive the required from_state for a clear denial reason ---
transition_name = neural_belief["proposed_transition"]
required_state = world.transitions[transition_name].from_state
next_committed = (
    verdict.committed_state.current_state
    if verdict.committed_state
    else committed["committed_state"]
)

print(f"Belief state:        {neural_belief['belief_state']} (confidence: {neural_belief['confidence']})")
print(f"Committed state:     {committed['committed_state']}")
print(f"Proposed transition: {transition_name}")
print(f"Verdict:             {verdict.status.value}")
print(f"Reason:              transition requires {required_state}, committed state is {committed['committed_state']}")
print(f"Next committed state: {next_committed}")
