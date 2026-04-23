"""
Physics-based corrections discovered in SSOC v3.32.

These 5 functions and their supporting constants form the core
"discovered physics" of the Gate & Channel framework:

  - correction_gly:       Gly conformational freedom (discovered v3.6)
  - correction_pro:       Pro ring constraint (discovered v3.6)
  - calc_backbone_strain: SS-propensity strain (discovered v3.7)
  - compute_pvoid:        Phase-dependent void plasticity (discovered v3.12)
  - get_helix_position:   Helix cap/core classification (discovered v3.7)

Source: SSOC v3.32 (Iizumi 2026, under review at Acta Materialia).
"""
import math
from .constants import (
    AA_HYDRO, AA_VOLUME, AA_HBDON, AA_HBACC,
    HELIX_PROP, BETA_PROP, CHARGE_AA,
)

# ─────────────────────────────────────────────────────────────
# Backbone strain constants (SSOC v3.7)
# ─────────────────────────────────────────────────────────────
POLAR_AA_STRAIN = {'S', 'T', 'N', 'Q', 'D', 'E', 'K', 'R', 'H', 'Y', 'W', 'C'}
W_STRAIN_H = 1.1
W_STRAIN_E = 1.1
PRO_CAP = +0.7
PRO_CORE = -1.5
GLY_H = +0.4
BETA_CHARGE = +0.2
BETA_POLAR = -0.7
SAT_H = 1.2
SAT_E = 0.8
B_E = +0.20

# ─────────────────────────────────────────────────────────────
# Gly/Pro correction constants (SSOC v3.6)
# ─────────────────────────────────────────────────────────────
E_GLY = 0.7
E_PRO = 0.65
E_NH = 1.0

# ─────────────────────────────────────────────────────────────
# Phase-dependent P_void (SSOC v3.12)
# ─────────────────────────────────────────────────────────────
PVOID_PARAMS = {
    'cavity': {'P0': 0.60, 'a_pack': -0.3, 'a_comp': -0.2, 'a_backbone': +0.2, 'ss_key': 'helix_nf'},
    'strain': {'P0': 0.70, 'a_pack': -0.2, 'a_comp': -0.3, 'a_backbone': +0.1, 'ss_key': 'beta_nf'},
    'charge': {'P0': 1.00, 'a_pack': 0.0,  'a_comp': 0.0,  'a_backbone': 0.0,  'ss_key': None},
}
PVOID_CLAMP = (0.30, 1.50)


# ═════════════════════════════════════════════════════════════
# Correction functions (byte-for-byte copy from ssoc_v332.py)
# ═════════════════════════════════════════════════════════════

def correction_gly(wa, ma, d_CB_min=999.0, kappa=90.0, n_branch=0):
    """Gly<->X conformational freedom correction.

    Physics: Gly has uniquely broad phi/psi access due to no sidechain.
    Gain/loss of this freedom is modulated by local steric constraint.
    """
    if wa != 'G' and ma != 'G':
        return 0.0
    if wa == 'G':
        s1 = 1 / (1 + math.exp(-5 * (d_CB_min - 2.6)))
        s2 = 1 / (1 + math.exp(0.05 * (kappa - 80)))
        s3 = 1 / (1 + math.exp(1.5 * (n_branch - 3)))
        return -1.0 * (1 - s1 * s2 * s3) + E_GLY
    else:
        return -E_GLY


def correction_pro(wa, ma):
    """Pro<->X ring constraint correction.

    Physics: Pro's cyclic sidechain constrains phi to ~-60 deg.
    Loss (Pro->X) releases constraint; gain (X->Pro) imposes constraint
    and removes amide H (H-bond donor loss).
    """
    if wa != 'P' and ma != 'P':
        return 0.0
    return -E_PRO if wa == 'P' else E_PRO - E_NH


def calc_backbone_strain(wa, ma, ss, hpos='none',
                         is_charge_intro=False, is_polar_intro=False):
    """Secondary-structure dependent backbone strain.

    Physics: HELIX_PROP/BETA_PROP differences drive local backbone
    strain in SS-constrained environments. Special terms for Pro cap,
    Pro core, Gly in helix, charge/polar intro in beta-sheet.
    """
    if ss == 'H':
        dp = HELIX_PROP.get(ma, 0.3) - HELIX_PROP.get(wa, 0.3)
        raw = W_STRAIN_H * dp
        if ma == 'P':
            raw += PRO_CAP if hpos == 'cap' else PRO_CORE
        if ma == 'G' and wa != 'G':
            raw += GLY_H
        return SAT_H * math.tanh(raw / SAT_H)
    elif ss == 'E':
        dp = BETA_PROP.get(ma, 0.3) - BETA_PROP.get(wa, 0.3)
        raw = W_STRAIN_E * dp
        if is_charge_intro:
            raw += BETA_CHARGE
        if is_polar_intro:
            raw += BETA_POLAR
        return SAT_E * math.tanh(raw / SAT_E) + B_E
    return 0.0


def compute_pvoid(phase, large_frac, polar_frac, helix_nf, beta_nf):
    """Compute phase-dependent void plasticity coefficient.

    Physics: Effective "void persistence" depends on local lattice:
      - cavity phase (FCC-like): sidechain reorientation dominant
      - strain phase (BCC-like): backbone constraint dominant
      - charge phase: neutral, SCC territory

    Used as multiplier on cavity formation energy.
    """
    params = PVOID_PARAMS[phase]
    if params['ss_key'] == 'helix_nf':
        ss_nf = helix_nf
    elif params['ss_key'] == 'beta_nf':
        ss_nf = beta_nf
    else:
        ss_nf = 0.0
    p_void = params['P0'] + params['a_pack'] * large_frac + \
             params['a_comp'] * polar_frac + params['a_backbone'] * ss_nf
    return max(PVOID_CLAMP[0], min(PVOID_CLAMP[1], p_void))


def get_helix_position(ss_map, pos):
    """Classify helix residue as 'cap' (terminal 2) or 'core' (interior).

    Used by calc_backbone_strain to apply PRO_CAP vs PRO_CORE.
    """
    srnums = sorted(ss_map.keys())
    if ss_map.get(pos) != 'H':
        return 'none'
    try:
        idx = srnums.index(pos)
    except ValueError:
        return 'none'
    left = idx
    while left > 0 and ss_map.get(srnums[left - 1]) == 'H':
        left -= 1
    right = idx
    while right < len(srnums) - 1 and ss_map.get(srnums[right + 1]) == 'H':
        right += 1
    pos_in_helix = idx - left
    helix_len = right - left + 1
    if pos_in_helix <= 1 or pos_in_helix >= helix_len - 2:
        return 'cap'
    return 'core'
