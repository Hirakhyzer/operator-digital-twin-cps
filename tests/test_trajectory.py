import pytest

from operator_digital_twin_cps import OperatorObservation
from operator_digital_twin_cps.trajectory import analyze_operator_trajectory


def obs(t: float, load: float, errors: float, misses: float, latency: float, success: float, on_task: float):
    return OperatorObservation(t, load, errors, misses, latency, success, on_task)


def test_trajectory_detects_capability_degradation() -> None:
    observations = [
        obs(0, 0.15, 0.02, 0.01, 1.0, 0.98, 300),
        obs(60, 0.25, 0.04, 0.02, 1.2, 0.96, 900),
        obs(120, 0.85, 0.45, 0.50, 5.5, 0.55, 7200),
        obs(180, 0.95, 0.65, 0.70, 8.0, 0.35, 9000),
    ]
    result = analyze_operator_trajectory(observations)
    assert len(result.snapshots) == 4
    assert result.latest_score < result.snapshots[0].capability.score
    assert result.score_trend_per_minute < 0
    assert result.degraded
    assert result.first_critical_unavailable_s is not None


def test_trajectory_can_report_recovery_after_sustained_good_evidence() -> None:
    observations = [
        obs(0, 0.95, 0.70, 0.70, 8.0, 0.30, 9000),
        obs(60, 0.90, 0.60, 0.60, 7.0, 0.35, 9060),
        obs(120, 0.10, 0.01, 0.01, 0.8, 1.0, 60),
        obs(180, 0.05, 0.00, 0.00, 0.7, 1.0, 120),
        obs(240, 0.05, 0.00, 0.00, 0.7, 1.0, 180),
        obs(300, 0.05, 0.00, 0.00, 0.7, 1.0, 240),
        obs(360, 0.05, 0.00, 0.00, 0.7, 1.0, 300),
    ]
    result = analyze_operator_trajectory(observations)
    assert result.first_critical_unavailable_s == 0
    assert result.recovered_critical_capability_s is not None
    assert result.recovered_critical_capability_s > result.first_critical_unavailable_s
    recovery = next(
        snapshot
        for snapshot in result.snapshots
        if snapshot.timestamp_s == result.recovered_critical_capability_s
    )
    assert recovery.capability.suitable_for_critical_intervention


def test_short_improvement_does_not_falsely_claim_recovery() -> None:
    observations = [
        obs(0, 0.95, 0.70, 0.70, 8.0, 0.30, 9000),
        obs(60, 0.90, 0.60, 0.60, 7.0, 0.35, 9060),
        obs(120, 0.10, 0.01, 0.01, 0.8, 1.0, 60),
    ]
    result = analyze_operator_trajectory(observations)
    assert result.first_critical_unavailable_s == 0
    assert result.recovered_critical_capability_s is None


def test_trajectory_rejects_duplicate_timestamps() -> None:
    observations = [
        obs(10, 0.2, 0.1, 0.1, 1.0, 0.9, 100),
        obs(10, 0.3, 0.1, 0.1, 1.2, 0.9, 110),
    ]
    with pytest.raises(ValueError, match="timestamps must be unique"):
        analyze_operator_trajectory(observations)
