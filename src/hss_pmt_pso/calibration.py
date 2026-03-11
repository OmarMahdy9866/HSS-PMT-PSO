from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from .config import CalibrationConfig
from .objective import weighted_rmse
from .plaxis_adapter import CommandLinePlaxisRunner, MockPlaxisRunner
from .pmt import read_pmt_curve
from .pso import optimize


@dataclass(frozen=True)
class CalibrationSummary:
    best_parameters: dict[str, float]
    objective_value: float
    history: tuple[float, ...]


def run_calibration(config: CalibrationConfig) -> CalibrationSummary:
    experimental = read_pmt_curve(config.experimental_csv)
    bounds = {b.name: (b.minimum, b.maximum) for b in config.parameter_bounds}
    config.output_dir.mkdir(parents=True, exist_ok=True)

    runner = (
        CommandLinePlaxisRunner(config.command_template, config.output_dir)
        if config.command_template
        else MockPlaxisRunner()
    )

    result = optimize(
        objective=lambda x: weighted_rmse(x, experimental, runner),
        bounds=bounds,
        particles=config.pso_particles,
        iterations=config.pso_iterations,
        w=config.inertia_weight,
        c1=config.cognitive_weight,
        c2=config.social_weight,
        seed=config.random_seed,
        workers=config.workers,
    )

    summary = CalibrationSummary(
        best_parameters=result.best_position,
        objective_value=result.best_score,
        history=result.history,
    )
    _write_outputs(summary, config.output_dir)
    return summary


def _write_outputs(summary: CalibrationSummary, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "best_parameters.json").write_text(
        json.dumps(summary.best_parameters, indent=2, sort_keys=True)
    )
    (output_dir / "calibration_summary.json").write_text(
        json.dumps(asdict(summary), indent=2)
    )
