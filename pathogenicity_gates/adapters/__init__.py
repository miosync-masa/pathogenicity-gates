"""Adapters bridging YAML-driven annotations to legacy v17/v18 implementations."""
from .v18_adapter import (
    build_context_from_annotation,
    override_legacy_constants_from_annotation,
    restore_legacy_constants,
)

__all__ = [
    'build_context_from_annotation',
    'override_legacy_constants_from_annotation',
    'restore_legacy_constants',
]
