"""
Physical primitives for the Gate & Channel framework.

These 20 "atoms" were discovered in SSOC v3.32 (Iizumi 2026):
  13 constants (amino acid properties, energy scales)
   2 geometry utilities (sigmoid, virtual C-beta placement)
   5 corrections (Gly, Pro, backbone strain, P_void, helix position)

Reference:
  Iizumi M. (2026) "Stoichiometric SSOC: zero-parameter first-principles
  prediction of thermal stability changes in 600 protein structures."
  Acta Materialia (under review).
"""
from .constants import (
    AA_HYDRO, AA_VOLUME, AA_CHARGE, AA_AROMATIC, AA_SULFUR,
    AA_HBDON, AA_HBACC, POLAR_SET,
    HELIX_PROP, BETA_PROP, CHARGE_AA,
    C_CAVITY, C_HYDRO_TRANSFER, THREE_TO_ONE,
)
from .geometry import sigmoid, place_virtual_CB
from .corrections import (
    correction_gly, correction_pro, calc_backbone_strain,
    compute_pvoid, get_helix_position,
)

__all__ = [
    'AA_HYDRO', 'AA_VOLUME', 'AA_CHARGE', 'AA_AROMATIC', 'AA_SULFUR',
    'AA_HBDON', 'AA_HBACC', 'POLAR_SET',
    'HELIX_PROP', 'BETA_PROP', 'CHARGE_AA',
    'C_CAVITY', 'C_HYDRO_TRANSFER', 'THREE_TO_ONE',
    'sigmoid', 'place_virtual_CB',
    'correction_gly', 'correction_pro', 'calc_backbone_strain',
    'compute_pvoid', 'get_helix_position',
]
