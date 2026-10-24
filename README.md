# Operator Digital Twin for Cyber-Physical Systems

A transparent research framework for estimating the **current operational capability of a human operator** from observable evidence.

The project asks:

> What is the operator's current capability to safely supervise, understand, and intervene in a cyber-physical system?

Rather than treating workload, fatigue, attention, or readiness as directly measurable facts, the framework models them as **latent estimates** derived from observable signals. Every estimate carries explicit uncertainty and evidence freshness.

## Why this matters

Human-in-the-loop CPS designs often assume a human is available and capable whenever escalation occurs. That assumption can fail under overload, fatigue, stale telemetry, slow response, or recent poor intervention performance.

This repository provides a small, auditable baseline for making operator capability part of CPS decision logic.

## Pipeline

```text
Observable operator evidence
        |
        v
Transparent state estimator
        |
        v
Operator digital twin
(workload, fatigue, attention,
 readiness, reliability, uncertainty)
        |
        v
Capability assessment
        |
        +--> score and capability band
        +--> effective response latency
        +--> confidence
        +--> critical-intervention suitability
```

## Current evidence model

`OperatorObservation` uses signals that can be observed or computed from system interaction data:

- task load
- secondary-task error rate
- missed-alert rate
- response latency
- recent intervention success rate
- time on task
- observation timestamp

These are not interpreted as direct measurements of cognition. They are evidence used by a transparent baseline estimator.

## Estimated state

The current twin estimates:

- **workload**
- **fatigue**
- **attention**
- **response readiness**
- **intervention reliability**
- **uncertainty**
- **evidence age**

Uncertainty grows when observations are stale, history is sparse, or signals disagree.

## Capability assessment

The capability layer converts the latent state estimate into operational quantities:

- capability score from 0 to 100
- capability band: `ready`, `caution`, `degraded`, or `unavailable`
- effective human response latency
- confidence in the assessment
- whether the operator is currently suitable for a critical intervention under the configured policy

This is decision support, not a medical or psychological diagnosis.

## Example

```python
from operator_digital_twin_cps import (
    OperatorObservation,
    assess_capability,
    estimate_operator_state,
)

history = [
    OperatorObservation(0, 0.25, 0.05, 0.03, 1.4, 0.96, 1200),
    OperatorObservation(10, 0.30, 0.06, 0.04, 1.5, 0.95, 1800),
    OperatorObservation(20, 0.35, 0.07, 0.05, 1.6, 0.94, 2400),
]

state = estimate_operator_state(history, now_s=25)
assessment = assess_capability(state)

print(state)
print(assessment)
```

## Reproducible experiment

```bash
python experiments/operator_readiness_demo.py
```

The experiment compares nominal and overloaded operator histories using the same estimator and capability policy.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Research direction

The v0.1 implementation is intentionally interpretable. Strong next steps include temporal filtering, multi-sensor evidence fusion, uncertainty calibration, operator-specific baselines, recovery after overload, handover readiness, intervention outcome prediction, and closed-loop coupling with runtime assurance and reachability analysis.

A later version should also compare alternative estimators against labeled human-performance data rather than treating the current hand-designed estimator as ground truth.

## Scope and limitations

- The framework estimates operational capability from configured evidence; it does not infer protected or clinical characteristics.
- Capability scores are model outputs, not ground truth.
- Weightings and thresholds are transparent baseline assumptions and should be calibrated for each deployment domain.
- The current estimator is deterministic and one-operator-at-a-time.
- Safety-critical use requires independent validation with domain-specific data and procedures.

## License

MIT
