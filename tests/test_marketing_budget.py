from estc_world_model import Constraint, Entity, Transition, WorldModel


def build_marketing_world(
    remaining_budget: int = 1200,
    requested_spend: int = 500,
    today_spend: int = 1000,
    daily_budget_limit: int = 2000,
) -> WorldModel:
    campaign = Entity(
        id="campaign_001",
        type="Campaign",
        state="Active",
        attributes={
            "remaining_budget": remaining_budget,
            "requested_spend": requested_spend,
            "today_spend": today_spend,
            "daily_budget_limit": daily_budget_limit,
        },
    )

    transition = Transition(
        name="AllocateBudget",
        entity_type="Campaign",
        from_state="Active",
        to_state="BudgetAllocated",
    )

    budget_available = Constraint(
        name="BudgetAvailable",
        applies_to="AllocateBudget",
        predicate=lambda entity: entity.attributes["requested_spend"]
        <= entity.attributes["remaining_budget"],
    )

    daily_budget_limit_guard = Constraint(
        name="DailyBudgetLimit",
        applies_to="AllocateBudget",
        predicate=lambda entity: entity.attributes["today_spend"]
        + entity.attributes["requested_spend"]
        <= entity.attributes["daily_budget_limit"],
    )

    return WorldModel(
        entities=[campaign],
        transitions=[transition],
        constraints=[budget_available, daily_budget_limit_guard],
    )


def test_budget_allocation_allowed_when_constraints_pass():
    world = build_marketing_world()

    verdict = world.propose(
        entity_id="campaign_001",
        transition="AllocateBudget",
        requested_by="marketing_agent",
    )

    assert verdict.status == "ALLOW"
    assert verdict.approved_action == "AllocateBudget"
    assert verdict.committed_state.current_state == "BudgetAllocated"
    assert "BudgetAvailable" in verdict.guards_passed
    assert "DailyBudgetLimit" in verdict.guards_passed


def test_budget_allocation_denied_when_remaining_budget_is_insufficient():
    world = build_marketing_world(
        remaining_budget=300,
        requested_spend=500,
    )

    verdict = world.propose(
        entity_id="campaign_001",
        transition="AllocateBudget",
        requested_by="marketing_agent",
    )

    assert verdict.status == "DENY"
    assert verdict.rejected_action == "AllocateBudget"
    assert any(result.name == "BudgetAvailable" and not result.passed for result in verdict.guard_result)


def test_budget_allocation_denied_when_daily_limit_exceeded():
    world = build_marketing_world(
        today_spend=1800,
        requested_spend=500,
        daily_budget_limit=2000,
    )

    verdict = world.propose(
        entity_id="campaign_001",
        transition="AllocateBudget",
        requested_by="marketing_agent",
    )

    assert verdict.status == "DENY"
    assert verdict.rejected_action == "AllocateBudget"
    assert any(result.name == "DailyBudgetLimit" and not result.passed for result in verdict.guard_result)
