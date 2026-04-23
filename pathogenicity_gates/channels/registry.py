"""
Channel registry with regime-based dispatch.

Channels register themselves via @register_channel decorator with an
explicit physical regime ('structural', 'idr', 'universal'). The
Predictor queries this registry to determine which Channels are
applicable to each residue position.
"""
from typing import Callable, Dict, List, Tuple

VALID_REGIMES = {'structural', 'idr', 'universal'}

_REGISTRY: Dict[str, Dict] = {}


def register_channel(id: str, regime: str, order: int):
    """Register a Channel function with its physical regime.

    Args:
        id:     Channel identifier (e.g., "Ch03_Core")
        regime: Physical regime. One of 'structural', 'idr', 'universal'.
        order:  Execution order (int, lower = earlier). Deterministic output.

    Returns:
        Decorator that registers the function.

    Raises:
        ValueError: if regime not in VALID_REGIMES or id already registered.
    """
    if regime not in VALID_REGIMES:
        raise ValueError(f"Invalid regime '{regime}'. Must be one of {VALID_REGIMES}")

    def decorator(fn: Callable) -> Callable:
        if id in _REGISTRY:
            raise ValueError(f"Channel '{id}' already registered")
        _REGISTRY[id] = {
            'fn': fn,
            'regime': regime,
            'order': order,
            'module': fn.__module__,
        }
        return fn
    return decorator


def get_applicable_channels(regime: str) -> List[Tuple[str, Dict]]:
    """Return channels applicable to the given regime, sorted by order.

    Applicable = regime matches OR channel is 'universal'.
    Returns empty list if regime == 'unknown'.
    """
    if regime == 'unknown':
        return []

    result = []
    for ch_id, ch_info in _REGISTRY.items():
        if ch_info['regime'] == regime or ch_info['regime'] == 'universal':
            result.append((ch_id, ch_info))

    return sorted(result, key=lambda x: x[1]['order'])


def get_all_channels() -> List[Tuple[str, Dict]]:
    """Return all registered channels, sorted by order."""
    return sorted(_REGISTRY.items(), key=lambda x: x[1]['order'])


def list_channels_by_regime() -> Dict[str, List[str]]:
    """Return channels grouped by regime, sorted within each regime."""
    result = {r: [] for r in VALID_REGIMES}
    for ch_id, ch_info in _REGISTRY.items():
        result[ch_info['regime']].append(ch_id)
    return {r: sorted(ids) for r, ids in result.items()}


def clear_registry():
    """Clear the channel registry. USE ONLY FOR TESTING."""
    global _REGISTRY
    _REGISTRY = {}
