from app.services.policy_engine import ActionContext, evaluate_action


def test_material_action_above_threshold_needs_human_approval():
    result = evaluate_action(ActionContext("supplier_shift", 12_000_000, "procurement_manager", 10_000_000))
    assert result["authorised"] is False
    assert result["reason"] == "human_approval_required"


def test_role_is_checked_independently_of_critic_or_llm_text():
    result = evaluate_action(ActionContext("supplier_shift", 1000, "viewer", 10_000_000, True))
    assert result["authorised"] is False
    assert result["reason"] == "role_not_allowed"


def test_unknown_action_is_denied_by_default():
    result = evaluate_action(ActionContext("arbitrary_external_write", 1, "admin", 10_000_000, True))
    assert result["authorised"] is False
    assert result["reason"] == "action_not_allowed"
