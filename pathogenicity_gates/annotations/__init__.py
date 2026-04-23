"""
YAML-based protein annotation loader.

Provides data-driven configuration for Gate & Channel prediction,
separating protein-specific information from framework code.
"""
from .loader import load_annotation, ProteinAnnotation

__all__ = ['load_annotation', 'ProteinAnnotation']
