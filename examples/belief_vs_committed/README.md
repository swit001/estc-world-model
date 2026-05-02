# Belief vs Committed State

**Belief is not fact. Proposal is not commit. Only the symbolic world can close execution.**

## What this example shows

A neural layer interprets a customer message and *believes* an order is `Delivered`. It proposes the transition `RequestRefund`. The symbolic world (SWM) checks the transition against the committed state from the SSOT and finds the order is actually `Shipped` — not yet delivered. The transition is denied. The committed state remains `Shipped`.

```
Belief state:        Delivered (confidence: 0.82)
Committed state:     Shipped
Proposed transition: RequestRefund
Verdict:             DENY
Reason:              transition requires Delivered, committed state is Shipped
Next committed state: Shipped
```

## Why belief and committed state must be separated

Neural language understanding is probabilistic. A model may infer a state from natural language, order history, or context — but that inference is a *belief*, not a ground truth. The committed state is the authoritative record of where the entity actually is right now.

Conflating belief with committed state leads to:

- Executing a transition from a state the entity is not in
- Violating business constraints that depend on real state
- Producing an audit trail that does not reflect what actually happened

The symbolic world exists precisely to adjudicate these cases. It holds the committed state, knows the declared transitions and their required `from_state`, and can enforce constraints before any side effect occurs.

## How this maps to NWM → SWM

```
NWM (neural):    believes state, proposes transition
SWM (symbolic):  validates against committed state, issues verdict
```

The NWM and SWM are complementary. The NWM provides intent and interpretation. The SWM provides structure and authority. Neither is complete without the other — but only the SWM can close execution.

## Scenario

| Layer | Value |
|---|---|
| NWM belief state | `Delivered` (confidence 0.82) |
| SWM committed state | `Shipped` |
| Proposed transition | `RequestRefund` |
| Transition requires | `Delivered` → `RefundRequested` |
| Verdict | `DENY` |

The denial happens at the state-match check, before any constraint guards are evaluated. The committed state is never mutated.

## How to run

From the repository root:

```bash
python examples/belief_vs_committed/demo.py
```

Expected output:

```
Belief state:        Delivered (confidence: 0.82)
Committed state:     Shipped
Proposed transition: RequestRefund
Verdict:             DENY
Reason:              transition requires Delivered, committed state is Shipped
Next committed state: Shipped
```
