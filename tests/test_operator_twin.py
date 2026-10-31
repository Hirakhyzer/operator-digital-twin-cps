from __future__ import annotations

import pytest

from operator_digital_twin_cps import (
    CapabilityPolicy,
    EstimatorConfig,
    OperatorObservation,
    assess_capability,
    estimate_operator_state,
)


def obs(
    t: float,
    task_load: float = 0.3,
    errors: float = 0.1,
    missed: float = 0.05,
    latency: float = 1.5,
    success: float = 0.95,
    time_on_task: float = 1_800,
) -> OperatorObservation:
    return OperatorObservation(
        timestamp_s=t,
        task_load=task_load,
        secondary_task_error_rate=errors,
        missed_alert_rate=missed,
        response_latency_s=latency,
        recent_intervention_success_rate=success,
        time_on_task_s=time_on_task,
    )


def test_ready_operator_is_suitable_for_critical_intervention() -> None:
    history = [obs(0), obs(10), obs(20)]
    state = estimate_operator_state(history, now_s=25)
    assessment = assess_capability(state)
    assert assessment.band in {"ready", "caution"}
    assert assessment.suitable_for_critical_intervention
    assert assessment.confidence > 0.65


def test_degraded_operator_is_not_suitable() -> None:
    history = [
        obs(0, 0.95, 0.6, 0.7, 5.0, 0.5, 18_000),
        obs(10, 0.95, 0.7, 0.8, 5.5, 0.4, 18_600),
        obs(20, 1.0, 0.8, 0.9, 6.0, 0.3, 19_200),
    ]
    state = estimate_operator_state(history, now_s=25)
    assessment = assess_capability(state)
    assert assessment.band in {"degraded", "unavailable"}
    assert not assessment.suitable_for_critical_intervention
    assert assessment.effective_response_latency_s > 2.0


def test_stale_evidence_increases_uncertainty() -> None:
    history = [obs(0), obs(10), obs(20)]
    fresh = estimate_operator_state(history, now_s=20)
    stale = estimate_operator_state(history, now_s=320)
    assert stale.uncertainty > fresh.uncertainty
    assert assess_capability(stale).confidence < assess_capability(fresh).confidence


def test_sparse_history_is_penalized() -> None:
    state = estimate_operator_state([obs(10)], now_s=10)
    assert state.uncertainty > 0.0


def test_observation_validation_rejects_invalid_rates() -> None:
    with pytest.raises(ValueError):
        obs(0, task_load=1.2)


def test_strict_policy_can_reject_otherwise_acceptable_operator() -> None:
    history = [obs(0), obs(10), obs(20)]
    state = estimate_operator_state(history, now_s=25)
    assessment = assess_capability(
        state,
        CapabilityPolicy(critical_score_threshold=95.0),
    )
    assert not assessment.suitable_for_critical_intervention


def test_minimum_history_must_be_an_integer() -> None:
    with pytest.raises(ValueError, match="integer"):
        EstimatorConfig(minimum_history=2.5)  # type: ignore[arg-type]


def test_estimator_config_rejects_nonfinite_parameters() -> None:
    with pytest.raises(ValueError, match="finite"):
        EstimatorConfig(freshness_half_life_s=float("nan"))


def test_capability_policy_rejects_nonfinite_parameters() -> None:
    with pytest.raises(ValueError, match="finite"):
        CapabilityPolicy(critical_score_threshold=float("nan"))


def test_estimator_rejects_nonfinite_analysis_time() -> None:
    with pytest.raises(ValueError, match="now_s must be finite"):
        estimate_operator_state([obs(0)], now_s=float("nan"))
