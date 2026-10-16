import pytest
from app.services.critic import CriticEvidence, composite_support


def test_blueprint_example_raw_material_score():
    evidence = CriticEvidence(0.91, 0.85, 0.78, 0.08, 0.94)
    assert composite_support(evidence) == 0.878


def test_critic_rejects_values_outside_unit_interval():
    evidence = CriticEvidence(1.2, 0.85, 0.78, 0.08, 0.94)
    with pytest.raises(ValueError):
        composite_support(evidence)
