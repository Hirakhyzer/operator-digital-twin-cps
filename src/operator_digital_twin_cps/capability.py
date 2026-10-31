"""Capability and intervention-readiness assessment."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .model import CapabilityAssessment, OperatorStateEstimate


@dataclass(frozen=True)
class CapabilityPolicy:
    critical_score_threshold: float = 70.0
    critical_confidence_threshold: float = 0.65
    max_critical_uncertainty: float = 0.35
    nominal_response_latency_s: float = 2.0

    def __post_init__(self) -> None:
        for name in (
            "critical_score_threshold",
            "critical_confidence_threshold",
            "max_critical_uncertainty",
            "nominal_response_latency_s",
        ):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if not 0.0 <= self.critical_score_threshold <= 100.0:
            raise ValueError("critical_score_threshold must be within [0, 100]")
        if not 0.0 <= self.critical_confidence_threshold <= 1.0:
            raise ValueError("critical_confidence_threshold must be within [0, 1]")
        if not 0.0 <= self.max_critical_uncertainty <= 1.0:
            raise ValueError("max_critical_uncertainty must be within [0, 1]")
        if self.nominal_response_latency_s <= 0:
            raise ValueError("nominal_response_latency_s must be positive")


def assess_capability(
    state: OperatorStateEstimate,
    policy: CapabilityPolicy = CapabilityPolicy(),
) -> CapabilityAssessment:
    """Convert estimated state into an operationally useful capability summary."""

    raw = 100.0 * (
        0.30 * state.attention
        + 0.30 * state.response_readiness
        + 0.25 * state.intervention_reliability
        + 0.15 * (1.0 - state.workload)
    )
    uncertainty_penalty = 25.0 * state.uncertainty
    fatigue_penalty = 10.0 * state.fatigue
    score = min(100.0, max(0.0, raw - uncertainty_penalty - fatigue_penalty))

    if score >= 80.0:
        band = "ready"
    elif score >= 65.0:
        band = "caution"
    elif score >= 45.0:
        band = "degraded"
    else:
        band = "unavailable"

    confidence = 1.0 - state.uncertainty
    effective_latency = policy.nominal_response_latency_s * (
        1.0
        + 0.8 * state.workload
        + 0.8 * state.fatigue
        + 0.7 * (1.0 - state.attention)
        + 0.5 * state.uncertainty
    )
    suitable = (
        score >= policy.critical_score_threshold
        and confidence >= policy.critical_confidence_threshold
        and state.uncertainty <= policy.max_critical_uncertainty
        and band in {"ready", "caution"}
    )

    return CapabilityAssessment(
        score=score,
        band=band,
        effective_response_latency_s=effective_latency,
        confidence=confidence,
        suitable_for_critical_intervention=suitable,
    )
