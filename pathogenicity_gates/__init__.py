"""
pathogenicity-gates: Zero-parameter first-principles pathogenicity prediction
via the Gate & Channel framework.

Based on SSOC v3.32 physical primitives (Iizumi 2026).

Reference:
  Iizumi M, Iizumi T. (2026) A zero-parameter first-principles gate framework
  for full-length TP53 missense variant interpretation.
  PLOS Computational Biology (under review).
"""

__version__ = "0.5.0-dev"

from .predictor import Predictor

__all__ = ['Predictor', '__version__']
