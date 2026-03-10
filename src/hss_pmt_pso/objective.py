from __future__ import annotations

from .pmt import PMTCurve
from .plaxis_adapter import PlaxisRunner


def weighted_rmse(
    candidate: dict[str, float],
    experimental: PMTCurve,
    plaxis: PlaxisRunner,
) -> float:
    """Weighted RMSE emphasizing the unload-reload and nonlinear range."""
    simulated = plaxis.run(candidate, experimental)

    total = 0.0
    weight_sum = 0.0
    n = len(experimental.pressure)

    for i, (obs, sim) in enumerate(zip(experimental.pressure, simulated.pressure)):
        x = i / max(n - 1, 1)
        weight = 1.0 + 2.0 * x**2
        error = obs - sim
        total += weight * error * error
        weight_sum += weight

    return (total / max(weight_sum, 1e-12)) ** 0.5
