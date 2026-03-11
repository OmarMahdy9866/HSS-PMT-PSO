from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess

from .pmt import PMTCurve


@dataclass(frozen=True)
class SimulationResult:
    pressure: tuple[float, ...]


class PlaxisRunner:
    """Interface for solving a PLAXIS model given candidate HSS parameters."""

    def run(self, parameters: dict[str, float], experimental_curve: PMTCurve) -> SimulationResult:
        raise NotImplementedError


class CommandLinePlaxisRunner(PlaxisRunner):
    """Run a user-provided command that returns a json array of pressure values."""

    def __init__(self, command_template: str, working_directory: Path) -> None:
        self._command_template = command_template
        self._working_directory = working_directory

    def run(self, parameters: dict[str, float], experimental_curve: PMTCurve) -> SimulationResult:
        payload = json.dumps({"parameters": parameters, "n": len(experimental_curve.pressure)})
        cmd = self._command_template.format(payload=payload)

        completed = subprocess.run(
            cmd,
            shell=True,
            cwd=self._working_directory,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "PLAXIS command failed "
                f"(code={completed.returncode}). stderr: {completed.stderr.strip()}"
            )

        values = json.loads(completed.stdout)
        if not isinstance(values, list) or len(values) != len(experimental_curve.pressure):
            raise ValueError("PLAXIS command must return a json list matching PMT points count")
        return SimulationResult(pressure=tuple(float(v) for v in values))


class MockPlaxisRunner(PlaxisRunner):
    """Deterministic runner for dry-run and testing without PLAXIS installation."""

    def run(self, parameters: dict[str, float], experimental_curve: PMTCurve) -> SimulationResult:
        e50 = parameters.get("E50ref", 15000.0)
        eur = parameters.get("Eurref", e50 * 3.0)
        m = parameters.get("m", 0.7)
        pref = parameters.get("pref", 100.0)

        simulated = []
        for eps_r in experimental_curve.radial_expansion:
            strain_factor = (1.0 + eps_r * 30.0) ** max(m, 0.1)
            stiffness = 0.6 * e50 + 0.4 * eur
            pressure = pref + stiffness * eps_r / strain_factor
            simulated.append(pressure)

        return SimulationResult(pressure=tuple(simulated))
