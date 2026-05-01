# estc-world-model

**Entity-State-Transition-Constraint runtime for production-grade AI agents.**

Most AI agent projects start with prompts and tools. Production agentic systems should start with a world.

`estc-world-model` is a lightweight Python package for turning an agentic world model into executable code. It lets you define entities, states, transitions, and constraints, then validate agent-proposed transitions, commit allowed state changes, and return structured `VerdictOutcome` objects.

```text
Prompt → Candidate Transition → Guard → Commit → VerdictOutcome
```

## Why this exists

Tool-calling alone does not make an AI agent production-ready. A tool call can change the world, but it does not by itself know:

- what entity is being changed,
- what the current committed state is,
- which transitions are allowed,
- which constraints must be enforced,
- what should be recorded after execution.

`estc-world-model` provides a minimal runtime for that missing layer.

## Runtime flow

```mermaid
flowchart TD
    A["WorldModel.propose()"] --> B["Validate<br/>entity · transition · state"]
    B -->|valid| C["Constraint guards"]
    B -->|fails| DENY["DENY"]
    C -->|passed| D["Commit state"]
    C -->|fails| DE["DENY / ESCALATE"]
    D --> ALLOW["ALLOW · VerdictOutcome"]

    style A fill:#F2F2EA,stroke:#307FE2,color:#1E2549,stroke-width:2px
    style B fill:#F2F2EA,stroke:#1E2549,color:#1E2549,stroke-width:1.5px
    style C fill:#F2F2EA,stroke:#1E2549,color:#1E2549,stroke-width:1.5px
    style D fill:#F2F2EA,stroke:#1E2549,color:#1E2549,stroke-width:1.5px
    style ALLOW fill:#EAF8F1,stroke:#26C981,color:#1E2549,stroke-width:2px
    style DENY fill:#FFF0EC,stroke:#F7694C,color:#1E2549,stroke-width:2px
    style DE fill:#FFF8D6,stroke:#FFDD29,color:#1E2549,stroke-width:2px
```

## Installation

```bash
pip install estc-world-model
```

For local development:

```bash
git clone https://github.com/swit001/estc-world-model.git
cd estc-world-model
pip install -e .
```

## Quick start

```python
from estc_world_model import Constraint, Entity, Transition, WorldModel

order = Entity(
    id="order_123",
    type="Order",
    state="Delivered",
    attributes={
        "days_since_delivery": 5,
        "refundable": True,
    },
)

request_refund = Transition(
    name="RequestRefund",
    entity_type="Order",
    from_state="Delivered",
    to_state="RefundRequested",
)

refund_within_seven_days = Constraint(
    name="RefundWithinSevenDays",
    applies_to="RequestRefund",
    description="Refunds are allowed only within 7 days after delivery.",
    predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
)

world = WorldModel(
    entities=[order],
    transitions=[request_refund],
    constraints=[refund_within_seven_days],
)

verdict = world.propose(
    entity_id="order_123",
    transition="RequestRefund",
    requested_by="customer_456",
)

print(verdict.model_dump_json(indent=2))
```

Example output:

```json
{
  "status": "ALLOW",
  "requested_transition": "RequestRefund",
  "entity_id": "order_123",
  "approved_action": "RequestRefund",
  "rejected_action": null,
  "next_state": "RefundRequested",
  "guards_passed": [
    "RefundWithinSevenDays"
  ],
  "guard_result": [
    {
      "name": "RefundWithinSevenDays",
      "passed": true,
      "reason": null
    }
  ],
  "committed_state": {
    "entity_id": "order_123",
    "entity_type": "Order",
    "previous_state": "Delivered",
    "current_state": "RefundRequested"
  },
  "alternatives": [],
  "audit_ref": "audit_...",
  "message": "Transition committed by customer_456."
}
```

## ESTC relationship

```mermaid
graph TD
    E["Entity<br/>executable object"] -->|occupies| S["State<br/>committed coordinate"]
    T["Transition<br/>declared path"] -->|entity_type| E
    T -->|from / to| S
    C["Constraint<br/>guard predicate"] -->|guards| T
    C -->|evaluates| E

    style E fill:#F2F2EA,stroke:#307FE2,color:#1E2549,stroke-width:2px
    style S fill:#EAF8F1,stroke:#26C981,color:#1E2549,stroke-width:2px
    style T fill:#F2F2EA,stroke:#1E2549,color:#1E2549,stroke-width:1.5px
    style C fill:#FFF8D6,stroke:#FFDD29,color:#1E2549,stroke-width:2px
```

## Core concepts

### Entity

An entity is the executable object whose state can be changed.

```python
Entity(id="order_123", type="Order", state="Delivered")
```

### State

A state is the committed coordinate of an entity. The runtime treats `entity.state` as the current committed state.

### Transition

A transition is a declared path from one state to another.

```python
Transition(
    name="RequestRefund",
    entity_type="Order",
    from_state="Delivered",
    to_state="RefundRequested",
)
```

### Constraint

A constraint is a guard that determines whether a transition can proceed.

```python
Constraint(
    name="RefundWithinSevenDays",
    applies_to="RequestRefund",
    predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
)
```

### VerdictOutcome

A `VerdictOutcome` is the structured result returned by the world model after evaluating a transition candidate.

Possible statuses:

- `ALLOW`
- `DENY`
- `ESCALATE`

## Canvas to code

The package is designed as the executable companion to a World Model Canvas.

```text
World Model Canvas
    ↓
ESTC specification
    ↓
Python runtime
    ↓
VerdictOutcome
```

A canvas cell such as:

```yaml
entity: Order
state: Delivered
transition: RequestRefund
constraint: days_since_delivery <= 7
```

becomes:

```python
order = Entity(id="order_123", type="Order", state="Delivered")
request_refund = Transition(
    name="RequestRefund",
    entity_type="Order",
    from_state="Delivered",
    to_state="RefundRequested",
)
refund_rule = Constraint(
    name="RefundWithinSevenDays",
    applies_to="RequestRefund",
    predicate=lambda entity: entity.attributes["days_since_delivery"] <= 7,
)
```

## Example domains

This repository starts with a minimal commerce refund example implemented entirely in Python:

```bash
python examples/commerce_refund/demo.py
```

Declarative YAML world definitions are intentionally not included in `examples/` yet. A YAML loader is planned for `0.2.0`; until then, the executable source of truth is the Python API.

Planned examples:

- Commerce: order cancellation, refund request, partial return
- Marketing: campaign budget exhaustion, creative approval, audience overlap
- HR: candidate pipeline, interview scheduling, offer approval

## Roadmap

- [x] Pydantic models for Entity, Transition, Constraint, VerdictOutcome
- [x] Minimal transition validation and commit runtime
- [x] Commerce refund example
- [ ] YAML loader for declarative world definitions
- [ ] JSON Schema export
- [ ] Belief vs committed state example
- [ ] NWM → SWM runtime demo
- [ ] CLI: `estc validate world.yaml`
- [ ] Domain templates for commerce, marketing, and HR

## Relationship to Agentic World Model

`agentic-world-model` is the map. `estc-world-model` is the engine.

The Agentic World Model framework defines the methodology, canvas, and design language for agentic systems. `estc-world-model` implements the minimal executable layer: entities, states, transitions, constraints, commits, and verdicts.

## License

Apache 2.0
