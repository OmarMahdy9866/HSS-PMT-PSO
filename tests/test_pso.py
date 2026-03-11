import pytest

from hss_pmt_pso.pso import optimize


def test_optimize_reduces_simple_quadratic():
    bounds = {"x": (-5.0, 5.0), "y": (-3.0, 3.0)}

    def objective(p):
        return (p["x"] - 2.0) ** 2 + (p["y"] + 1.0) ** 2

    result = optimize(
        objective=objective,
        bounds=bounds,
        particles=18,
        iterations=40,
        w=0.7,
        c1=1.4,
        c2=1.6,
        seed=9,
        workers=1,
    )

    assert result.best_score < 1e-3
    assert abs(result.best_position["x"] - 2.0) < 0.05
    assert abs(result.best_position["y"] + 1.0) < 0.05


def test_optimize_validates_arguments():
    with pytest.raises(ValueError, match="bounds cannot be empty"):
        optimize(
            objective=lambda _: 0.0,
            bounds={},
            particles=4,
            iterations=10,
            w=0.7,
            c1=1.4,
            c2=1.6,
            seed=1,
        )

    with pytest.raises(ValueError, match="particles must be >= 2"):
        optimize(
            objective=lambda _: 0.0,
            bounds={"x": (0.0, 1.0)},
            particles=1,
            iterations=10,
            w=0.7,
            c1=1.4,
            c2=1.6,
            seed=1,
        )
