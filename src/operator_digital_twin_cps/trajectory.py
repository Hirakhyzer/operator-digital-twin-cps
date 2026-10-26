"""Temporal analysis for operator digital-twin state evolution."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from .capability import CapabilityPolicy, assess_capability
from .estimation import EstimatorConfig, estimate_operator_state
from .model import CapabilityAssessment, OperatorObservation, OperatorStateEstimate


@dataclass(frozen=True)
class OperatorSnapshot:
    """One time-indexed digital-twin estimate and capability assessment."""

    timestamp_s: float
    state: OperatorStateEstimate
    capability: CapabilityAssessment


@dataclass(frozen=True)
class TrajectorySummary:
    """Summary of capability evolution over an observation sequence."""

    snapshots: tuple[OperatorSnapshot, ...]
    minimum_score: float
    latest_score: float
    score_trend_per_minute: float
    first_critical_unavailable_s: float | None
    recovered_critical_capability_s: float | None

    @property
    def degraded(self) -> bool:
        return self.score_trend_per_minute < 0.0


def analyze_operator_trajectory(
    observations: Sequence[OperatorObservation],
    *,
    estimator_config: EstimatorConfig = EstimatorConfig(),
    capability_policy: CapabilityPolicy = CapabilityPolicy(),
) -> TrajectorySummary:
    """Reconstruct how estimated operator capability evolved over time.

    Only evidence available at each observation timestamp is used, avoiding
    look-ahead leakage. Recovery is reported only after the operator has first
    become unsuitable for critical intervention and later becomes suitable.
    """

    if not observations:
        raise ValueError("at least one observation is required")
    ordered = sorted(observations, key=lambda item: item.timestamp_s)
    timestamps = [item.timestamp_s for item in ordered]
    if len(set(timestamps)) != len(timestamps):
        raise ValueError("observation timestamps must be unique")

    snapshots: list[OperatorSnapshot] = []
    for index, observation in enumerate(ordered):
        history = ordered[: index + 1]
        state = estimate_operator_state(history, now_s=observation.timestamp_s, config=estimator_config)
        capability = assess_capability(state, policy=capability_policy)
        snapshots.append(OperatorSnapshot(observation.timestamp_s, state, capability))

    first = snapshots[0]
    latest = snapshots[-1]
    elapsed_s = latest.timestamp_s - first.timestamp_s
    trend = 0.0 if elapsed_s == 0 else (latest.capability.score - first.capability.score) / (elapsed_s / 60.0)
    if not isfinite(trend):
        raise ValueError("trajectory trend must be finite")

    first_unavailable: float | None = None
    recovered: float | None = None
    for snapshot in snapshots:
        suitable = snapshot.capability.suitable_for_critical_intervention
        if first_unavailable is None and not suitable:
            first_unavailable = snapshot.timestamp_s
        elif first_unavailable is not None and recovered is None and suitable:
            recovered = snapshot.timestamp_s

    return TrajectorySummary(
        snapshots=tuple(snapshots),
        minimum_score=min(item.capability.score for item in snapshots),
        latest_score=latest.capability.score,
        score_trend_per_minute=trend,
        first_critical_unavailable_s=first_unavailable,
        recovered_critical_capability_s=recovered,
    )
