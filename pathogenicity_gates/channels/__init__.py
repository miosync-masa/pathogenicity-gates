"""
Channel registry initialization.

Importing this module triggers registration of all built-in Channels
via their @register_channel decorators.

Experimental Channels are NOT auto-registered; import them explicitly.
"""
# Structural regime (8 channels)
from .structural import (  # noqa: F401
    ch01_dna, ch02_zn, ch03_core, ch04_ss, ch05_loop,
    ch06_ppi, ch08_oligomer, ch09_salt_bridge,
)

# IDR regime (3 channels)
from .idr import (  # noqa: F401
    ch10_slim, ch11_idr_pro, ch12_idr_gly,
)

# Universal regime (1 channel)
from .universal import ch07_ptm  # noqa: F401

from . import registry
from .context import PredictionContext

__all__ = ['registry', 'PredictionContext']
