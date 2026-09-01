"""``SimulariumAnalysis`` — a post-sim Analysis that converts a run's emitted
molecule positions into a Simularium file.

It subclasses ``viva_superpowers.post_sim.AnalysisStep``, so it plugs into the
study Evaluate-stage flush exactly like any other analysis: ``ResultsStep``
hands it the run's emitted rows and it emits an artifact. Each emitted row is
one timepoint carrying a ``time`` and a ``molecule_positions`` list of point
agents (``{type, x, y, z, radius}``) — the shape ``viva_smoldyn.SmoldynProcess``
emits. The written ``.simularium`` path is returned in the analysis result and
written to disk at ``config["output_path"]``.

Config keys (all optional except ``output_path``):
  - ``output_path`` (str): where to write the ``.simularium`` (suffix optional).
  - ``box_size`` (list[float]): simulation bounds as a 3-vector. Falls back to
    a unit box; set it for a correct viewer camera.
  - ``position_field`` (str, default ``"molecule_positions"``): the emitted-row
    key holding the per-step agent list.
  - ``time_field`` (str, default ``"time"``): the emitted-row key holding the
    timestamp. When absent, the row index is used.
  - ``display`` (dict): ``{type_name: {"color": "#rrggbb", "radius": float}}``.
  - ``spatial_unit`` / ``time_unit`` / ``title`` / ``fmt`` / ``default_radius``:
    forwarded to ``write_simularium``.
"""
from __future__ import annotations

from typing import Any

from viva_superpowers.post_sim import AnalysisStep

from viva_simularium.writer import write_simularium

_DEFAULT_POSITION_FIELD = "molecule_positions"
_DEFAULT_TIME_FIELD = "time"


class SimulariumAnalysis(AnalysisStep):
    """Convert a run's emitted molecule positions to a ``.simularium`` file."""

    name = "simularium"
    scale = "single"
    config_schema: dict = {}

    def analyze(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        cfg = dict(self.config or {})
        output_path = cfg.get("output_path")
        if not output_path:
            raise ValueError("SimulariumAnalysis requires config['output_path']")

        position_field = cfg.get("position_field", _DEFAULT_POSITION_FIELD)
        time_field = cfg.get("time_field", _DEFAULT_TIME_FIELD)

        times, frames = _rows_to_frames(
            rows, position_field, time_field,
            dedupe_times=cfg.get("dedupe_times", True),
            drop_empty_leading=cfg.get("drop_empty_leading", True),
        )

        box_size = cfg.get("box_size") or _infer_box_size(frames)
        out = write_simularium(
            times,
            frames,
            box_size,
            output_path,
            display=cfg.get("display"),
            spatial_unit=cfg.get("spatial_unit", "nm"),
            time_unit=cfg.get("time_unit", "s"),
            title=cfg.get("title", ""),
            fmt=cfg.get("fmt", "binary"),
            default_radius=float(cfg.get("default_radius", 1.0)),
        )
        return {
            "simularium_path": str(out),
            "n_frames": len(times),
            "n_agents_max": max((len(f) for f in frames), default=0),
        }


def _rows_to_frames(rows, position_field, time_field, *,
                    dedupe_times=True, drop_empty_leading=True):
    """Split emitted rows into aligned ``(times, frames)``.

    Each row's ``position_field`` is a list of agent dicts; rows lacking it
    contribute an empty frame (a valid, agent-less timestep). ``time_field``
    supplies the timestamp, defaulting to the row index when absent.

    Emitters commonly record the same timestep twice (once when the process
    updates a store, once at the next tick boundary) and an empty state before
    the first step. ``dedupe_times`` collapses consecutive rows sharing a
    timestamp, keeping the last (the settled state); ``drop_empty_leading``
    strips agent-less frames at the head of the trajectory. Both default on —
    they make viewer playback match wall-clock without altering the physics.
    """
    times: list[float] = []
    frames: list[list[dict]] = []
    for i, row in enumerate(rows or []):
        row = row or {}
        agents = row.get(position_field) or []
        # Tolerate a single agent dict emitted un-listed.
        if isinstance(agents, dict):
            agents = [agents]
        t = float(row[time_field]) if row.get(time_field) is not None else float(i)
        if dedupe_times and times and t == times[-1]:
            frames[-1] = list(agents)          # keep the last state at this time
            continue
        times.append(t)
        frames.append(list(agents))

    if drop_empty_leading:
        while len(frames) > 1 and not frames[0]:
            frames.pop(0)
            times.pop(0)

    return times, frames


def _infer_box_size(frames):
    """A cubic box just enclosing all agent positions (fallback when config
    omits ``box_size``). Returns a unit box for an empty trajectory."""
    coords = [
        (float(a.get("x", 0.0)), float(a.get("y", 0.0)), float(a.get("z", 0.0)))
        for frame in frames for a in frame
    ]
    if not coords:
        return [1.0, 1.0, 1.0]
    span = max(abs(c) for xyz in coords for c in xyz) or 1.0
    return [2.0 * span, 2.0 * span, 2.0 * span]
