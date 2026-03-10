# HSS-PMT-PSO

Structured and scalable workflow for identifying **Hardening Soil Small (HSS)** parameters from **Pressuremeter Test (PMT)** curves using inverse analysis and **Particle Swarm Optimization (PSO)**, with a direct integration hook for **PLAXIS 2D**.

## What is included

- Clean modular architecture (`config`, `data`, `objective`, `optimizer`, `runner`, `pipeline`)
- Deterministic PSO engine with bounded particles and optional parallel scoring
- PMT CSV validation and loading
- Objective function (`weighted RMSE`) tailored to PMT curve fitting
- PLAXIS execution abstraction:
  - `CommandLinePlaxisRunner` for real PLAXIS coupling
  - `MockPlaxisRunner` for dry-runs and CI validation
- CLI entrypoint for repeatable calibration runs
- Output artifacts (`best_parameters.json`, `calibration_summary.json`)

---

## Project structure

```text
src/hss_pmt_pso/
  calibration.py      # End-to-end orchestration
  cli.py              # Command-line entrypoint
  config.py           # Typed config model and JSON loader
  objective.py        # Weighted RMSE objective
  plaxis_adapter.py   # PLAXIS runner interfaces (real + mock)
  pmt.py              # PMT data loading and validation
  pso.py              # PSO algorithm engine
examples/
  pmt_sample.csv
  calibration_config.json
tests/
  test_pso.py
  test_pipeline.py
```

---

## HSS parameters typically calibrated from PMT

You can calibrate any parameter set, but common ones for PMT inverse analysis are:

- `E50ref` – secant stiffness in standard drained triaxial test
- `Eurref` – unloading/reloading stiffness
- `m` – stress dependency exponent
- `pref` – reference pressure (or proxy used in your chosen constitutive setup)

Add/remove parameters in `parameter_bounds` as needed.

---

## Input data format (PMT)

CSV must contain:

- `radial_expansion`
- `pressure`

Example:

```csv
radial_expansion,pressure
0.0005,102
0.0010,108
0.0015,115
```

Validation rules currently enforced:

- required headers must exist
- all rows numeric
- at least 5 points
- `radial_expansion` monotonic increasing

---

## Configuration

Use a JSON file (see `examples/calibration_config.json`).

```json
{
  "experimental_csv": "examples/pmt_sample.csv",
  "output_dir": "outputs/demo_run",
  "parameter_bounds": [
    {"name": "E50ref", "min": 8000, "max": 60000},
    {"name": "Eurref", "min": 24000, "max": 180000},
    {"name": "m", "min": 0.3, "max": 1.2},
    {"name": "pref", "min": 70, "max": 160}
  ],
  "pso_particles": 20,
  "pso_iterations": 60,
  "inertia_weight": 0.7,
  "cognitive_weight": 1.4,
  "social_weight": 1.6,
  "workers": 4,
  "random_seed": 42
}
```

### PLAXIS integration mode

By default, the pipeline uses a local deterministic mock solver.

To connect PLAXIS, provide `command_template` in config. The command receives a JSON payload injected into `{payload}` and must print a JSON list of simulated pressures with same length as PMT points.

Example concept:

```json
"command_template": "python plaxis_batch_runner.py --payload '{payload}'"
```

Where `plaxis_batch_runner.py` should:

1. Parse payload with candidate HSS parameters
2. Set parameters in PLAXIS model (via remote scripting API)
3. Run calculation
4. Extract pressure response at PMT steps
5. Print `[...]` JSON array to stdout

---

## Run

```bash
python -m pip install -e .
hss-pmt-calibrate --config examples/calibration_config.json
```

Outputs are written to `output_dir`:

- `best_parameters.json`
- `calibration_summary.json`

---

## Algorithm design (scalable and structured)

1. **Load + validate PMT curve**
2. **Define parameter bounds**
3. **Initialize PSO swarm** within bounds
4. **Evaluate objective in parallel** (`workers` threads)
5. **Update personal/global bests**
6. **Update velocities + bounded positions**
7. **Repeat** for `pso_iterations`
8. **Persist calibrated result** and optimization history

Scalability levers:

- Increase `workers` to evaluate particles concurrently
- Increase/decrease swarm size and iteration budget
- Swap `MockPlaxisRunner` with command-based PLAXIS runner without touching optimizer core

---

## Next practical improvements for production PLAXIS usage

- Add a robust PLAXIS Python API adapter (session management, retries, timeout handling)
- Add penalty terms for unrealistic HSS combinations
- Support multi-test joint inversion (several PMT curves / depths)
- Add checkpointing for long optimization runs
- Add Bayesian post-analysis around PSO optimum (uncertainty bands)

