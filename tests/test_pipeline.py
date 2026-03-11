from pathlib import Path

from hss_pmt_pso.calibration import run_calibration
from hss_pmt_pso.config import CalibrationConfig, ParameterBound


def test_full_pipeline_writes_outputs(tmp_path: Path):
    csv = tmp_path / "curve.csv"
    csv.write_text(
        "radial_expansion,pressure\n"
        "0.001,104\n"
        "0.002,110\n"
        "0.003,117\n"
        "0.004,123\n"
        "0.005,127\n"
    )

    output = tmp_path / "out"
    config = CalibrationConfig(
        experimental_csv=csv,
        output_dir=output,
        parameter_bounds=(
            ParameterBound("E50ref", 5000, 50000),
            ParameterBound("Eurref", 15000, 150000),
            ParameterBound("m", 0.3, 1.2),
            ParameterBound("pref", 60, 180),
        ),
        pso_particles=12,
        pso_iterations=20,
        workers=2,
    )

    summary = run_calibration(config)
    assert summary.objective_value >= 0
    assert (output / "best_parameters.json").exists()
    assert (output / "calibration_summary.json").exists()


def test_commandline_runner_works_with_new_output_dir(tmp_path: Path):
    csv = tmp_path / "curve.csv"
    csv.write_text(
        "radial_expansion,pressure\n"
        "0.001,104\n"
        "0.002,110\n"
        "0.003,117\n"
        "0.004,123\n"
        "0.005,127\n"
    )

    output = tmp_path / "missing_dir"
    config = CalibrationConfig(
        experimental_csv=csv,
        output_dir=output,
        parameter_bounds=(
            ParameterBound("E50ref", 5000, 50000),
            ParameterBound("Eurref", 15000, 150000),
            ParameterBound("m", 0.3, 1.2),
            ParameterBound("pref", 60, 180),
        ),
        pso_particles=4,
        pso_iterations=3,
        workers=1,
        command_template='python -c "import json; print(json.dumps([100,110,120,130,140]))"',
    )

    summary = run_calibration(config)
    assert summary.objective_value >= 0
    assert output.exists()
