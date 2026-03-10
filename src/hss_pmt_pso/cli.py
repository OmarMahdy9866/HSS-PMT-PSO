from __future__ import annotations

from pathlib import Path
import argparse
import json

from .calibration import run_calibration
from .config import CalibrationConfig


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate HSS parameters from PMT data using PSO and PLAXIS 2D."
    )
    parser.add_argument("--config", required=True, type=Path, help="Path to calibration json")
    args = parser.parse_args()

    config = CalibrationConfig.from_json(args.config)
    summary = run_calibration(config)
    print(json.dumps({
        "best_parameters": summary.best_parameters,
        "objective_value": summary.objective_value,
        "iterations": len(summary.history),
    }, indent=2))


if __name__ == "__main__":
    main()
