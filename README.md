# viva-simularium

Generic [Simularium](https://simularium.allencell.org/) adapters for
[viva](https://github.com/vivarium-collective/viva-superpowers) /
[process-bigraph](https://github.com/vivarium-collective/process-bigraph)
workspaces: turn a run's **emitted molecule positions** into a `.simularium`
trajectory you can drop into the Simularium viewer.

It's the shared seam every wrapped simulator targets — a simulator only has to
emit per-step point agents (`{type, x, y, z, radius}`); this package handles the
Simularium encoding (binary `SIMULARIUMBINARY` v3 by default, JSON optional) via
[`simulariumio`](https://github.com/simularium/simulariumio).

## Install

```bash
pip install git+https://github.com/vivarium-collective/viva-simularium.git
```

Or, for local development from a checkout:

```bash
uv pip install -e .
```

Depends on `simulariumio`, `numpy`, `viva-superpowers`, `process-bigraph`, and
`bigraph-schema`. The pure-writer surface (`write_simularium` /
`build_trajectory`) imports without `viva-superpowers`; `SimulariumAnalysis` is
imported lazily and pulls it in only when used.

## Quick start

Write point-agent frames directly to a `.simularium` file:

```python
from viva_simularium import write_simularium

times = [0.0, 1.0, 2.0]
frames = [
    [{"type": "A", "x": 1.0, "y": 2.0, "z": 0.0, "radius": 2.0}],
    [{"type": "A", "x": 1.5, "y": 2.5, "z": 0.0}],
    [{"type": "A", "x": 2.0, "y": 3.0, "z": 0.0}],
]
out = write_simularium(times, frames, box_size=[100, 100, 100], path="run")
# -> run.simularium
```

`times` and `frames` are aligned per timestep; each agent needs a `type` and
`x`/`y`/`z` (`z` defaults to 0.0 for 2D sims) and may carry a `radius`. Pass
`display={"A": {"color": "#ff8800", "radius": 3.0}}` for per-type styling, or
`fmt="json"` for the JSON encoding.

As a post-sim analysis, declare `SimulariumAnalysis` on a composite and let the
study's Evaluate-stage flush run it:

```python
from viva_simularium import SimulariumAnalysis   # AnalysisStep, name="simularium"
```

with `config = {"output_path": ".../run", "box_size": [...],
"display": {"A": {"color": "#ff8800", "radius": 3.0}}}`. It reads each emitted
row's `molecule_positions` (configurable via `position_field`), uses `time`
(or the row index) as the timestamp, and writes the `.simularium` to
`output_path`, returning `{simularium_path, n_frames, n_agents_max}`.

## Contents

- **`write_simularium(times, frames, box_size, path, ...)`** — the pure writer;
  returns the path of the file written (binary by default, `fmt="json"` for JSON).
- **`build_trajectory(times, frames, box_size, ...)`** — assembles the
  underlying `simulariumio.TrajectoryData` without writing a file, for callers
  that want the object directly.
- **`SimulariumAnalysis`** — a `viva_superpowers.post_sim.AnalysisStep`
  (`name="simularium"`). Wired into a study's Evaluate-stage flush, it reads the
  run's emitted rows (via the `ResultsHandle` that `ResultsStep` produces),
  pulls each row's point-agent list, and writes a `.simularium` to
  `config["output_path"]`. It dedupes consecutive rows sharing a timestamp and
  drops empty leading frames by default (`dedupe_times` / `drop_empty_leading`),
  and infers a bounding `box_size` when config omits one.

Fibers / subpoints are intentionally out of scope — most particle simulators
emit points — though `simulariumio.AgentData` supports subpoints if a future
adapter needs them.

## Links

- [Simularium viewer](https://simularium.allencell.org/)
- [simulariumio](https://github.com/simularium/simulariumio)
- [process-bigraph](https://github.com/vivarium-collective/process-bigraph)
- [viva-superpowers](https://github.com/vivarium-collective/viva-superpowers)
