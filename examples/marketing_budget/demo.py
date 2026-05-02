from estc_world_model import Constraint, Entity, Transition, WorldModel


def build_world() -> WorldModel:
    campaign = Entity(
        id="campaign_001",
        type="Campaign",
        state="Active",
        attributes={
            "remaining_budget": 1200,
            "requested_spend": 500,
            "daily_budget_limit": 2000,
            "today_spend": 1000,
        },
    )

    allocate_budget = Transition(
        name="AllocateBudget",
        entity_type="Campaign",
        from_state="Active",
        to_state="BudgetAllocated",
    )

    budget_available = Constraint(
        name="BudgetAvailable",
        applies_to="AllocateBudget",
        description="Requested spend must not exceed remaining budget.",
        predicate=lambda entity: entity.attributes["requested_spend"]
        <= entity.attributes["remaining_budget"],
    )

    daily_budget_limit = Constraint(
        name="DailyBudgetLimit",
        applies_to="AllocateBudget",
        description="Today spend plus requested spend must not exceed daily budget limit.",
        predicate=lambda entity: entity.attributes["today_spend"]
        + entity.attributes["requested_spend"]
        <= entity.attributes["daily_budget_limit"],
    )

    return WorldModel(
        entities=[campaign],
        transitions=[allocate_budget],
        constraints=[budget_available, daily_budget_limit],
    )


if __name__ == "__main__":
    world = build_world()

    verdict = world.propose(
        entity_id="campaign_001",
        transition="AllocateBudget",
        requested_by="marketing_agent",
    )

    print(verdict.model_dump_json(indent=2))
