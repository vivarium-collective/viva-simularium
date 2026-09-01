"""write_simularium round-trip: point frames -> .simularium -> read back."""
import struct

import numpy as np
import pytest

from viva_simularium.writer import build_trajectory, write_simularium

TIMES = [0.0, 1.0, 2.0]
FRAMES = [
    [{"type": "A", "x": 1.0, "y": 2.0, "z": 0.0, "radius": 2.0},
     {"type": "B", "x": 3.0, "y": 4.0, "z": 5.0}],
    [{"type": "A", "x": 1.5, "y": 2.5, "z": 0.0}],  # ragged: fewer agents
    [{"type": "A", "x": 2.0, "y": 3.0, "z": 0.0},
     {"type": "B", "x": 3.5, "y": 4.5, "z": 5.5},
     {"type": "A", "x": 9.0, "y": 9.0, "z": 9.0}],
]
BOX = [100.0, 100.0, 100.0]


def test_build_trajectory_shapes_and_types():
    traj = build_trajectory(TIMES, FRAMES, BOX, display={"A": {"color": "#ff0000", "radius": 3.0}})
    ad = traj.agent_data
    assert list(ad.times) == TIMES
    assert list(ad.n_agents) == [2, 1, 3]
    # max agents across frames = 3
    assert ad.positions.shape == (3, 3, 3)
    assert ad.radii[0, 0] == 2.0            # explicit radius honored
    assert set(ad.display_data.keys()) == {"A", "B"}
    assert ad.display_data["A"].color == "#ff0000"


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        build_trajectory([0.0], FRAMES, BOX)


def test_write_binary_is_readable(tmp_path):
    out = write_simularium(TIMES, FRAMES, BOX, tmp_path / "traj", title="spike")
    assert out.exists()
    assert out.name == "traj.simularium"
    with open(out, "rb") as fh:
        head = fh.read(16)
    assert head == b"SIMULARIUMBINARY"


def test_write_json_is_valid(tmp_path):
    import json
    out = write_simularium(TIMES, FRAMES, BOX, tmp_path / "traj", fmt="json")
    assert out.exists()
    doc = json.loads(out.read_text())
    assert doc["trajectoryInfo"]["totalSteps"] == 3
    tm = doc["trajectoryInfo"]["typeMapping"]
    names = {v["name"] for v in tm.values()}
    assert names == {"A", "B"}


def test_empty_frames_ok(tmp_path):
    out = write_simularium([0.0], [[]], BOX, tmp_path / "empty")
    assert out.exists()
