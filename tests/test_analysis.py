"""SimulariumAnalysis: emitted rows -> .simularium, wired as an AnalysisStep."""
import numpy as np
from bigraph_schema import allocate_core

from viva_simularium import SimulariumAnalysis
from viva_simularium.analysis import _rows_to_frames

ROWS = [
    {"time": 0.0, "molecule_counts": {"A": 2},
     "molecule_positions": [{"type": "A", "x": 1.0, "y": 2.0, "z": 0.0},
                            {"type": "A", "x": 5.0, "y": 5.0, "z": 5.0}]},
    {"time": 0.5, "molecule_counts": {"A": 1},
     "molecule_positions": [{"type": "A", "x": 1.2, "y": 2.2, "z": 0.0}]},
]


def test_registers_as_analysis():
    from viva_superpowers.post_sim import ANALYSIS_REGISTRY, POST_SIM_REGISTRY
    assert ANALYSIS_REGISTRY.get("simularium") is SimulariumAnalysis
    assert POST_SIM_REGISTRY["simularium"]["kind"] == "analysis"


def test_rows_to_frames_alignment():
    times, frames = _rows_to_frames(ROWS, "molecule_positions", "time")
    assert times == [0.0, 0.5]
    assert [len(f) for f in frames] == [2, 1]


def test_analyze_writes_simularium(tmp_path):
    out = tmp_path / "smoldyn_run"
    step = SimulariumAnalysis(
        {"output_path": str(out), "box_size": [10.0, 10.0, 10.0],
         "title": "smoldyn"},
        core=allocate_core(),
    )
    result = step.analyze(ROWS)
    written = tmp_path / "smoldyn_run.simularium"
    assert written.exists()
    assert result["simularium_path"] == str(written)
    assert result["n_frames"] == 2
    assert result["n_agents_max"] == 2
    with open(written, "rb") as fh:
        assert fh.read(16) == b"SIMULARIUMBINARY"


def test_update_reads_results_handle_records(tmp_path):
    """End-to-end via the AnalysisStep contract: a ResultsHandle-like object in
    the `results` store whose .records() returns the emitted rows."""
    class FakeHandle:
        def records(self, scale=None):
            return ROWS

    out = tmp_path / "viahandle"
    step = SimulariumAnalysis(
        {"output_path": str(out), "box_size": [10.0, 10.0, 10.0]},
        core=allocate_core(),
    )
    update = step.update({"results": FakeHandle()})
    assert update["analysis"]["n_frames"] == 2
    assert (tmp_path / "viahandle.simularium").exists()


def test_missing_output_path_raises(tmp_path):
    step = SimulariumAnalysis({}, core=allocate_core())
    try:
        step.analyze(ROWS)
        assert False, "expected ValueError"
    except ValueError:
        pass
