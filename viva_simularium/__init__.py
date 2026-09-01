"""viva-simularium — generic Simularium adapters for viva/process-bigraph.

Public surface:
  - ``write_simularium`` / ``build_trajectory`` — turn point-agent frames into a
    ``.simularium`` file (binary or JSON) via ``simulariumio``.
  - ``SimulariumAnalysis`` — a ``viva_superpowers`` post-sim ``AnalysisStep`` that
    converts a run's emitted molecule positions into a ``.simularium`` in the
    study Evaluate-stage flush.
"""
from viva_simularium.writer import build_trajectory, write_simularium

__all__ = ["build_trajectory", "write_simularium", "SimulariumAnalysis"]


def __getattr__(name):
    # Lazy so importing the pure-writer surface doesn't require viva_superpowers.
    if name == "SimulariumAnalysis":
        from viva_simularium.analysis import SimulariumAnalysis
        return SimulariumAnalysis
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
