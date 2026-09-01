"""Write a point-agent trajectory to a Simularium file.

``write_simularium`` takes a plain, simulator-agnostic description of a
trajectory — per-timestep lists of point agents (``type``, position, radius) —
and emits a ``.simularium`` file (binary v3 by default, JSON optional) via
``simulariumio``. This is the generic seam every viva adapter targets: a
wrapped simulator only has to produce ``frames`` in this shape.

Fibers/subpoints are intentionally out of scope here (Smoldyn and most
particle simulators emit points); ``simulariumio.AgentData`` supports subpoints
if a future adapter needs them.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from simulariumio import (
    AgentData,
    BinaryWriter,
    DisplayData,
    JsonWriter,
    MetaData,
    TrajectoryData,
    UnitData,
)
from simulariumio.constants import DISPLAY_TYPE, VIZ_TYPE

# A point agent for one frame: a type name, an (x, y, z) position, and a radius.
Agent = Mapping[str, Any]
Frame = Sequence[Agent]

_DEFAULT_RADIUS = 1.0


def _agent_xyz(agent: Agent) -> list[float]:
    """Pull (x, y, z) from an agent dict. ``z`` defaults to 0.0 (2D sims)."""
    return [float(agent.get("x", 0.0)),
            float(agent.get("y", 0.0)),
            float(agent.get("z", 0.0))]


def build_trajectory(
    times: Sequence[float],
    frames: Sequence[Frame],
    box_size: Sequence[float],
    *,
    display: "Mapping[str, Mapping[str, Any]] | None" = None,
    spatial_unit: str = "nm",
    time_unit: str = "s",
    title: str = "",
    default_radius: float = _DEFAULT_RADIUS,
) -> TrajectoryData:
    """Assemble a ``simulariumio.TrajectoryData`` from point-agent frames.

    ``times`` and ``frames`` are aligned per-timestep (``len(times) ==
    len(frames)``). Each frame is a list of agent dicts with ``type`` and
    ``x``/``y``/``z`` (``z`` optional) and an optional ``radius``. ``box_size``
    is a 3-vector. ``display`` maps a type name to ``{"color": "#rrggbb",
    "radius": float}`` overrides (both optional).
    """
    if len(times) != len(frames):
        raise ValueError(
            f"times/frames length mismatch: {len(times)} != {len(frames)}")
    n_timesteps = len(times)
    max_agents = max((len(f) for f in frames), default=0)
    # simulariumio requires a positive agent dimension even for empty frames.
    width = max(max_agents, 1)

    n_agents = np.zeros(n_timesteps, dtype=float)
    viz_types = np.full((n_timesteps, width), VIZ_TYPE.DEFAULT, dtype=float)
    unique_ids = np.zeros((n_timesteps, width), dtype=float)
    positions = np.zeros((n_timesteps, width, 3), dtype=float)
    radii = np.ones((n_timesteps, width), dtype=float)
    types: list[list[str]] = []

    seen_types: set[str] = set()
    for t, frame in enumerate(frames):
        n_agents[t] = len(frame)
        row_types: list[str] = []
        for i, agent in enumerate(frame):
            name = str(agent.get("type", "agent"))
            seen_types.add(name)
            row_types.append(name)
            unique_ids[t, i] = i
            positions[t, i] = _agent_xyz(agent)
            radii[t, i] = float(agent.get("radius", default_radius))
        types.append(row_types)

    display_data = _build_display_data(seen_types, display or {}, default_radius)

    agent_data = AgentData(
        times=np.asarray(times, dtype=float),
        n_agents=n_agents,
        viz_types=viz_types,
        unique_ids=unique_ids,
        types=types,
        positions=positions,
        radii=radii,
        display_data=display_data,
    )
    return TrajectoryData(
        meta_data=MetaData(
            box_size=np.asarray(box_size, dtype=float),
            trajectory_title=title,
        ),
        agent_data=agent_data,
        time_units=UnitData(time_unit),
        spatial_units=UnitData(spatial_unit),
    )


def _build_display_data(
    type_names: Iterable[str],
    display: Mapping[str, Mapping[str, Any]],
    default_radius: float,
) -> dict[str, DisplayData]:
    out: dict[str, DisplayData] = {}
    for name in sorted(type_names):
        override = display.get(name, {})
        out[name] = DisplayData(
            name=name,
            display_type=DISPLAY_TYPE.SPHERE,
            radius=float(override.get("radius", default_radius)),
            color=str(override.get("color", "")),
        )
    return out


def write_simularium(
    times: Sequence[float],
    frames: Sequence[Frame],
    box_size: Sequence[float],
    path: "str | Path",
    *,
    display: "Mapping[str, Mapping[str, Any]] | None" = None,
    spatial_unit: str = "nm",
    time_unit: str = "s",
    title: str = "",
    fmt: str = "binary",
    default_radius: float = _DEFAULT_RADIUS,
) -> Path:
    """Write ``frames`` to a ``.simularium`` file and return its path.

    ``fmt`` is ``"binary"`` (default, the compact ``SIMULARIUMBINARY`` v3 format
    the viewer prefers) or ``"json"``. ``path`` may include or omit the
    ``.simularium`` suffix — ``simulariumio`` appends it — and the returned path
    is the actual file written.
    """
    traj = build_trajectory(
        times, frames, box_size, display=display, spatial_unit=spatial_unit,
        time_unit=time_unit, title=title, default_radius=default_radius)

    path = Path(path)
    # simulariumio's writers take a path stem and append ".simularium".
    stem = path.with_suffix("") if path.suffix == ".simularium" else path
    stem.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "binary":
        BinaryWriter.save(traj, str(stem), validate_ids=False)
    elif fmt == "json":
        JsonWriter.save(traj, str(stem), validate_ids=False)
    else:
        raise ValueError(f"unknown fmt {fmt!r}; expected 'binary' or 'json'")

    return stem.with_suffix(".simularium")
