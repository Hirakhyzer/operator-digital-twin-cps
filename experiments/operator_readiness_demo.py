from operator_digital_twin_cps import OperatorObservation, assess_capability, estimate_operator_state


def make_observation(t: float, load: float, missed: float, latency: float, success: float, time_on_task: float) -> OperatorObservation:
    return OperatorObservation(
        timestamp_s=t,
        task_load=load,
        secondary_task_error_rate=missed * 0.8,
        missed_alert_rate=missed,
        response_latency_s=latency,
        recent_intervention_success_rate=success,
        time_on_task_s=time_on_task,
    )


scenarios = {
    "nominal": [
        make_observation(0, 0.25, 0.03, 1.4, 0.96, 1200),
        make_observation(10, 0.30, 0.04, 1.5, 0.95, 1800),
        make_observation(20, 0.35, 0.05, 1.6, 0.94, 2400),
    ],
    "overloaded": [
        make_observation(0, 0.85, 0.30, 3.5, 0.75, 9000),
        make_observation(10, 0.90, 0.40, 4.2, 0.65, 9600),
        make_observation(20, 0.95, 0.50, 4.8, 0.55, 10200),
    ],
}

for name, history in scenarios.items():
    state = estimate_operator_state(history, now_s=25)
    capability = assess_capability(state)
    print(
        name,
        {
            "score": round(capability.score, 2),
            "band": capability.band,
            "confidence": round(capability.confidence, 3),
            "effective_response_latency_s": round(capability.effective_response_latency_s, 2),
            "critical_intervention": capability.suitable_for_critical_intervention,
        },
    )
