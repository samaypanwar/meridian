import pytest

from meridian.scoring import priority


def test_priority_is_value_per_effort_scaled_by_urgency() -> None:
    assert priority.compute(relevance=8, urgency=5, effort=2) == 20.0


def test_priority_rejects_zero_effort() -> None:
    with pytest.raises(ValueError):
        priority.compute(relevance=8, urgency=5, effort=0)


def test_evergreen_urgency_does_not_decay() -> None:
    assert priority.decay(urgency0=5, lam=0.0, age_days=30) == 5.0


def test_timely_urgency_decays_monotonically() -> None:
    assert priority.decay(5, 0.1, 10) < priority.decay(5, 0.1, 1)
