import json
from pathlib import Path

import pytest

from hss_pmt_pso.config import CalibrationConfig, ParameterBound


def test_from_json_resolves_paths_relative_to_config_file(tmp_path: Path):
    data_dir = tmp_path / "case"
    data_dir.mkdir()
    (data_dir / "curve.csv").write_text(
        "radial_expansion,pressure\n0.001,100\n0.002,110\n0.003,120\n0.004,125\n0.005,130\n"
    )

    config_path = data_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "experimental_csv": "curve.csv",
                "output_dir": "outputs",
                "parameter_bounds": [{"name": "E50ref", "min": 1, "max": 2}],
            }
        )
    )

    cfg = CalibrationConfig.from_json(config_path)
    assert cfg.experimental_csv == data_dir / "curve.csv"
    assert cfg.output_dir == Path("outputs")


def test_config_validation_rejects_duplicate_or_invalid_bounds(tmp_path: Path):
    with pytest.raises(ValueError, match="Duplicate parameter bound name"):
        CalibrationConfig(
            experimental_csv=tmp_path / "x.csv",
            output_dir=tmp_path / "out",
            parameter_bounds=(
                ParameterBound("E50ref", 1.0, 2.0),
                ParameterBound("E50ref", 2.0, 3.0),
            ),
        )

    with pytest.raises(ValueError, match="must be < max"):
        CalibrationConfig(
            experimental_csv=tmp_path / "x.csv",
            output_dir=tmp_path / "out",
            parameter_bounds=(ParameterBound("E50ref", 3.0, 3.0),),
        )
