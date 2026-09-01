# viva-simularium

Generic [Simularium](https://simularium.allencell.org/) adapters for
[viva](https://github.com/vivarium-collective/viva-superpowers) /
[process-bigraph](https://github.com/vivarium-collective/process-bigraph)
workspaces: turn a run's **emitted molecule positions** into a `.simularium`
trajectory you can drop into the Simularium viewer.

It's the shared seam every wrapped simulator targets — a simulator only has to
emit per-step point agents (`{type, x, y, z, radius}`); this package handles the
Simularium encoding.

## What's in it

- **`write_simularium(times, frames, box_size, path, ...)`** — the pure writer.
  `frames` is a per-timestep list of point-agent dicts. Emits binary
  (`SIMULARIUMBINARY` v3, the default) or JSON via
  [`simulariumio`](https://github.com/simularium/simulariumio).
- **`SimulariumAnalysis`** — a `viva_superpowers.post_sim.AnalysisStep`. Wired
  into a study's Evaluate-stage flush, it reads the run's emitted rows (via the
  `ResultsHandle` that `ResultsStep` produces), pulls each row's
  `molecule_positions`, and writes a `.simularium` to `config["output_path"]`.

## Quick start

```python
from viva_simularium import write_simularium

times = [0.0, 1.0, 2.0]
frames = [
    [{"type": "A", "x": 1.0, "y": 2.0, "z": 0.0, "radius": 2.0}],
    [{"type": "A", "x": 1.5, "y": 2.5, "z": 0.0}],
    [{"type": "A", "x": 2.0, "y": 3.0, "z": 0.0}],
]
write_simularium(times, frames, box_size=[100, 100, 100], path="run")
# -> run.simularium
```

As a post-sim analysis, declare it on a composite and let the study flush run it:

```python
from viva_simularium import SimulariumAnalysis   # AnalysisStep, name="simularium"
```

with `config = {"output_path": ".../run", "box_size": [...],
"display": {"A": {"color": "#ff8800", "radius": 3.0}}}`.

## Install

```bash
uv pip install -e .
```

Depends on `simulariumio`, `numpy`, `viva-superpowers`, `process-bigraph`,
`bigraph-schema`.
