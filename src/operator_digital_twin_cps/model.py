"""Core data structures for the operator digital twin."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _unit_interval(name: str, value: float) -> float:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and within [0, 1]")
    return float(value)


def _nonnegative(name: str, value: float) -> float:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class OperatorObservation:
    """Observable evidence collected about the operator at one instant.

    These fields are signals, not direct measurements of cognition. The twin uses
    them as evidence when estimating latent operator state.
    """

    timestamp_s: float
    task_load: float
    secondary_task_error_rate: float
    missed_alert_rate: float
    response_latency_s: float
    recent_intervention_success_rate: float
    time_on_task_s: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp_s", _nonnegative("timestamp_s", self.timestamp_s))
        object.__setattr__(self, "task_load", _unit_interval("task_load", self.task_load))
        object.__setattr__(
            self,
            "secondary_task_error_rate",
            _unit_interval("secondary_task_error_rate", self.secondary_task_error_rate),
        )
        object.__setattr__(self, "missed_alert_rate", _unit_interval("missed_alert_rate", self.missed_alert_rate))
        object.__setattr__(
            self, "response_latency_s", _nonnegative("response_latency_s", self.response_latency_s)
        )
        object.__setattr__(
            self,
            "recent_intervention_success_rate",
            _unit_interval("recent_intervention_success_rate", self.recent_intervention_success_rate),
        )
        object.__setattr__(self, "time_on_task_s", _nonnegative("time_on_task_s", self.time_on_task_s))


@dataclass(frozen=True)
class OperatorStateEstimate:
    """Estimated latent operator state with confidence and freshness metadata."""

    workload: float
    fatigue: float
    attention: float
    response_readiness: float
    intervention_reliability: float
    uncertainty: float
    evidence_age_s: float

    def __post_init__(self) -> None:
        for name in (
            "workload",
            "fatigue",
            "attention",
            "response_readiness",
            "intervention_reliability",
            "uncertainty",
        ):
            object.__setattr__(self, name, _unit_interval(name, getattr(self, name)))
        object.__setattr__(self, "evidence_age_s", _nonnegative("evidence_age_s", self.evidence_age_s))


@dataclass(frozen=True)
class CapabilityAssessment:
    """Operational capability summary for CPS decision support."""

    score: float
    band: str
    effective_response_latency_s: float
    confidence: float
    suitable_for_critical_intervention: bool

    def __post_init__(self) -> None:
        if not isfinite(self.score) or not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be finite and within [0, 100]")
        object.__setattr__(self, "effective_response_latency_s", _nonnegative("effective_response_latency_s", self.effective_response_latency_s))
        object.__setattr__(self, "confidence", _unit_interval("confidence", self.confidence))
