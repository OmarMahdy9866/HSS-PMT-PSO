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
  "experimental_csv": "pmt_sample.csv",
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

## Detailed algorithm (inverse analysis from PMT to HSS)

This section describes the implemented algorithm exactly as executed in code.

### 1) Inputs and search space definition

- Experimental signal: PMT curve pairs `(radial_expansion_i, pressure_i)`.
- Decision variables: bounded parameter vector `theta = [theta_1 ... theta_d]`.
- Typical variables: `E50ref`, `Eurref`, `m`, `pref`.
- Bounds: each variable satisfies `theta_j in [theta_j_min, theta_j_max]`.

The optimization is derivative-free and suitable for black-box PLAXIS calculations.

### 2) Forward model abstraction

For every candidate `theta`, the optimizer calls a forward model to produce simulated pressure values over the same PMT expansion points.

Implemented runners:

- `CommandLinePlaxisRunner`: executes an external command and expects a JSON list of simulated pressures.
- `MockPlaxisRunner`: deterministic local surrogate for test/dev use when PLAXIS is unavailable.

This keeps the optimizer independent from the concrete PLAXIS integration details.

### 3) Objective function

Given observed pressure `p_i`, simulated pressure `p_hat_i`, and weights `w_i`, the minimized error is weighted RMSE:

`J(theta) = sqrt( sum_i w_i * (p_i - p_hat_i)^2 / sum_i w_i )`

Weighting used in code:

- `x_i = (i - 1) / (n - 1)`
- `w_i = 1 + 2 * x_i^2`

So later PMT points receive larger influence (typically where nonlinearity is more pronounced).

### 4) PSO state per particle

Each particle stores:

- `position` (candidate parameter vector)
- `velocity`
- `personal best position` and `personal best score`

The swarm also stores a `global best position` and `global best score`.

Initialization:

- positions sampled uniformly inside bounds
- velocities initialized to zero

### 5) Iterative PSO loop

For iteration `t = 1..T`:

1. Evaluate objective for every particle (parallelized with threads if `workers > 1`).
2. Update personal bests if current score improves particle history.
3. Update global best if any particle improves swarm history.
4. Update velocity and position component-wise:

`v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)`

`x_next = x + v`

Where:

- `w` = inertia weight
- `c1` = cognitive coefficient
- `c2` = social coefficient
- `r1`, `r2` are random values in `[0, 1]`

5. Apply bounds:

- clamp if `x_next` goes out of range
- reverse/damp velocity with factor `-0.3` on boundary hit (simple bounce-back)

The algorithm records best score per iteration as convergence history.

### 6) Output artifacts

After optimization:

- `best_parameters.json` contains best parameter vector.
- `calibration_summary.json` contains best score and optimization history.

These outputs make runs reproducible and auditable.

### 7) Scalability characteristics

- Particle evaluations are independent and naturally parallel.
- Forward model is pluggable (mock/local command/remote executor).
- Budget is configurable (`particles`, `iterations`, `workers`).
- Fixed random seed provides deterministic replay.

### 8) Practical tuning recommendations

- Start with `20-30` particles and `50-100` iterations.
- Expand particle count first if convergence is unstable.
- Keep physically realistic bounds to avoid wasting objective calls.
- Add geotechnical penalty terms (future step) for implausible parameter combinations.

---

## Next practical improvements for production PLAXIS usage

- Add a robust PLAXIS Python API adapter (session management, retries, timeout handling)
- Add penalty terms for unrealistic HSS combinations
- Support multi-test joint inversion (several PMT curves / depths)
- Add checkpointing for long optimization runs
- Add Bayesian post-analysis around PSO optimum (uncertainty bands)

