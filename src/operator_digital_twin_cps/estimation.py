"""Transparent baseline estimator for latent operator state."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from statistics import fmean
from typing import Sequence

from .model import OperatorObservation, OperatorStateEstimate


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


@dataclass(frozen=True)
class EstimatorConfig:
    nominal_response_latency_s: float = 2.0
    fatigue_time_constant_s: float = 14_400.0
    freshness_half_life_s: float = 60.0
    minimum_history: int = 3

    def __post_init__(self) -> None:
        if self.nominal_response_latency_s <= 0:
            raise ValueError("nominal_response_latency_s must be positive")
        if self.fatigue_time_constant_s <= 0:
            raise ValueError("fatigue_time_constant_s must be positive")
        if self.freshness_half_life_s <= 0:
            raise ValueError("freshness_half_life_s must be positive")
        if isinstance(self.minimum_history, bool) or self.minimum_history < 1:
            raise ValueError("minimum_history must be an integer >= 1")


def estimate_operator_state(
    observations: Sequence[OperatorObservation],
    now_s: float,
    config: EstimatorConfig = EstimatorConfig(),
) -> OperatorStateEstimate:
    """Estimate operator state using interpretable normalized evidence.

    The implementation is deliberately transparent: it does not claim to measure
    cognitive state directly. It combines observable workload/performance signals
    into conservative latent-state estimates and reports uncertainty explicitly.
    """

    if not observations:
        raise ValueError("at least one observation is required")
    ordered = sorted(observations, key=lambda item: item.timestamp_s)
    latest = ordered[-1]
    if now_s < latest.timestamp_s:
        raise ValueError("now_s cannot precede the latest observation")

    recent = ordered[-max(config.minimum_history, min(len(ordered), 5)) :]
    workload = _clamp01(
        0.55 * fmean(item.task_load for item in recent)
        + 0.25 * fmean(item.secondary_task_error_rate for item in recent)
        + 0.20 * fmean(item.missed_alert_rate for item in recent)
    )

    max_time_on_task = max(item.time_on_task_s for item in recent)
    fatigue_time = 1.0 - exp(-max_time_on_task / config.fatigue_time_constant_s)
    latency_penalty = _clamp01(
        fmean(item.response_latency_s for item in recent) / (2.5 * config.nominal_response_latency_s)
    )
    fatigue = _clamp01(0.65 * fatigue_time + 0.35 * latency_penalty)

    attention = _clamp01(
        1.0
        - (
            0.45 * fmean(item.missed_alert_rate for item in recent)
            + 0.35 * fmean(item.secondary_task_error_rate for item in recent)
            + 0.20 * workload
        )
    )

    mean_latency = fmean(item.response_latency_s for item in recent)
    response_readiness = _clamp01(
        1.0 - 0.65 * _clamp01(mean_latency / (3.0 * config.nominal_response_latency_s)) - 0.35 * fatigue
    )
    intervention_reliability = _clamp01(
        0.75 * fmean(item.recent_intervention_success_rate for item in recent)
        + 0.25 * attention
    )

    evidence_age_s = now_s - latest.timestamp_s
    freshness = 0.5 ** (evidence_age_s / config.freshness_half_life_s)
    history_confidence = min(1.0, len(ordered) / config.minimum_history)
    signal_disagreement = max(
        abs(workload - (1.0 - attention)),
        abs(fatigue - (1.0 - response_readiness)),
    )
    uncertainty = _clamp01(
        0.45 * (1.0 - freshness)
        + 0.35 * (1.0 - history_confidence)
        + 0.20 * signal_disagreement
    )

    return OperatorStateEstimate(
        workload=workload,
        fatigue=fatigue,
        attention=attention,
        response_readiness=response_readiness,
        intervention_reliability=intervention_reliability,
        uncertainty=uncertainty,
        evidence_age_s=evidence_age_s,
    )
