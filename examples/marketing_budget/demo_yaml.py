from estc_world_model import Entity, load_world_from_yaml


campaign = Entity(
    id="campaign_001",
    type="Campaign",
    state="Active",
    attributes={
        "remaining_budget": 1200,
        "requested_spend": 500,
        "today_spend": 1000,
        "daily_budget_limit": 2000,
    },
)

world = load_world_from_yaml(
    "examples/marketing_budget/world.yaml",
    entities=[campaign],
)

verdict = world.propose(
    entity_id="campaign_001",
    transition="AllocateBudget",
    requested_by="marketing_agent",
)

print(verdict)
