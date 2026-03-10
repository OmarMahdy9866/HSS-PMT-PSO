from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv


@dataclass(frozen=True)
class PMTCurve:
    radial_expansion: tuple[float, ...]
    pressure: tuple[float, ...]


def read_pmt_curve(csv_path: Path) -> PMTCurve:
    """Load PMT test data with two required columns: radial_expansion, pressure."""
    radial: list[float] = []
    pressure: list[float] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"radial_expansion", "pressure"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                "CSV must include headers radial_expansion and pressure. "
                f"Got {reader.fieldnames!r}"
            )

        for idx, row in enumerate(reader, start=2):
            try:
                radial.append(float(row["radial_expansion"]))
                pressure.append(float(row["pressure"]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid PMT row at line {idx}: {row}") from exc

    if len(radial) < 5:
        raise ValueError("PMT curve must contain at least 5 points.")

    if sorted(radial) != radial:
        raise ValueError("radial_expansion must be monotonic increasing.")

    return PMTCurve(radial_expansion=tuple(radial), pressure=tuple(pressure))
