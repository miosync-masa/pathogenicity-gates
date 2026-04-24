"""Adapters bridging YAML-driven annotations to prediction contexts.

Two paths:
  - `v18_adapter.build_context_from_annotation`: routes via legacy v17/v18
    setup_*() functions. Required for `Predictor.predict(..., mode='legacy')`
    (calls v17.predict_pathogenicity).
  - `direct_builder.build_context_direct`: pure path for channels mode,
    uses only physics/ and structure/ modules. No legacy import.
"""
from .v18_adapter import (
    build_context_from_annotation,
    override_legacy_constants_from_annotation,
    restore_legacy_constants,
)
from .direct_builder import build_context_direct

__all__ = [
    'build_context_from_annotation',
    'override_legacy_constants_from_annotation',
    'restore_legacy_constants',
    'build_context_direct',
]
