"""
Geometric utility functions for the Gate & Channel framework.

Source: SSOC v3.32 (Iizumi 2026).
"""
import math
import numpy as np


def sigmoid(x, x0, k):
    """Sigmoid function with numerical clipping.

    Used throughout SSOC for smooth thresholding:
      - Burial estimation (x=nc/nc_p90, x0=0.60, k=10.0)
      - Desolvation factor (x=dry_bur, x0=0.40, k=8.0)
      - Gate 4 cavity restoration (x=dVol, x0=45.0, k=0.08)

    Args:
        x:  input value
        x0: midpoint (where sigmoid = 0.5)
        k:  steepness (higher = sharper transition)

    Returns:
        Value in (0, 1).
    """
    z = np.clip(-k * (x - x0), -30, 30)
    return 1.0 / (1.0 + np.exp(z))


def place_virtual_CB(N, CA, C):
    """Place virtual C-beta atom for Gly residues using tetrahedral geometry.

    Used in correction_gly to compute d_CB_min (minimum distance from
    virtual C-beta to neighboring heavy atoms). This captures the "would-be"
    steric clash if Gly were replaced by any other residue.

    Args:
        N, CA, C: np.ndarray (3,), backbone atom coordinates

    Returns:
        np.ndarray (3,): virtual C-beta position (1.52 A from CA)
    """
    v1 = (CA - N) / max(np.linalg.norm(CA - N), 1e-10)
    v2 = (CA - C) / max(np.linalg.norm(CA - C), 1e-10)
    bisect = v1 + v2
    bisect /= max(np.linalg.norm(bisect), 1e-10)
    n_perp = np.cross(v1, v2)
    n_perp /= max(np.linalg.norm(n_perp), 1e-10)
    theta = math.radians(54.75)
    cb_dir = math.cos(theta) * bisect + math.sin(theta) * n_perp
    cb_dir /= max(np.linalg.norm(cb_dir), 1e-10)
    return CA + 1.52 * cb_dir
