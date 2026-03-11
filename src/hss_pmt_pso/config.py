from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class ParameterBound:
    name: str
    minimum: float
    maximum: float

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Parameter name cannot be empty.")
        if self.minimum >= self.maximum:
            raise ValueError(
                f"Invalid bounds for {self.name!r}: min ({self.minimum}) must be < max ({self.maximum})."
            )


@dataclass(frozen=True)
class CalibrationConfig:
    experimental_csv: Path
    output_dir: Path
    parameter_bounds: tuple[ParameterBound, ...]
    pso_particles: int = 24
    pso_iterations: int = 100
    inertia_weight: float = 0.70
    cognitive_weight: float = 1.4
    social_weight: float = 1.6
    random_seed: int = 42
    workers: int = 1
    command_template: str | None = None

    def __post_init__(self) -> None:
        if not self.parameter_bounds:
            raise ValueError("At least one parameter bound is required.")
        seen: set[str] = set()
        for bound in self.parameter_bounds:
            bound.validate()
            if bound.name in seen:
                raise ValueError(f"Duplicate parameter bound name: {bound.name!r}")
            seen.add(bound.name)

        if self.pso_particles < 2:
            raise ValueError("pso_particles must be >= 2.")
        if self.pso_iterations < 1:
            raise ValueError("pso_iterations must be >= 1.")
        if self.workers < 1:
            raise ValueError("workers must be >= 1.")

    @staticmethod
    def from_json(path: Path) -> "CalibrationConfig":
        payload: dict[str, Any] = json.loads(path.read_text())
        base_dir = path.parent

        bounds = tuple(
            ParameterBound(
                name=item["name"],
                minimum=float(item["min"]),
                maximum=float(item["max"]),
            )
            for item in payload["parameter_bounds"]
        )

        experimental_csv = Path(payload["experimental_csv"])
        output_dir = Path(payload["output_dir"])
        if not experimental_csv.is_absolute():
            experimental_csv = base_dir / experimental_csv

        return CalibrationConfig(
            experimental_csv=experimental_csv,
            output_dir=output_dir,
            parameter_bounds=bounds,
            pso_particles=int(payload.get("pso_particles", 24)),
            pso_iterations=int(payload.get("pso_iterations", 100)),
            inertia_weight=float(payload.get("inertia_weight", 0.70)),
            cognitive_weight=float(payload.get("cognitive_weight", 1.4)),
            social_weight=float(payload.get("social_weight", 1.6)),
            random_seed=int(payload.get("random_seed", 42)),
            workers=int(payload.get("workers", 1)),
            command_template=payload.get("command_template"),
        )
