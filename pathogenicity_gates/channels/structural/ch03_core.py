"""
Ch03_Core: Core structural integrity — SYMMETRY COMPLETE.

All gate pairs have their mirror implemented (v16 established, v17 unchanged).
  Volume:    cavity <-> steric clash
  Polarity:  hydro->polar <-> polar->hydro
  H-bond:    loss <-> gain
  Aromatic:  loss <-> gain
  Charge:    loss <-> intro <-> flip

V18 patch embedded: V<->I swap is exempted (beta-branched aliphatic isomer).
"""
from ...physics.constants import (
    AA_HYDRO, AA_VOLUME, AA_CHARGE, AA_HBDON, AA_HBACC,
    CHARGE_AA, C_CAVITY, C_HYDRO_TRANSFER,
)
from ...physics.corrections import compute_pvoid
from ..registry import register_channel

AROMATIC_SET = {'F', 'W', 'Y'}
BETA_BRANCHED = {'V', 'I', 'T'}


@register_channel(id="Ch03_Core", regime="structural", order=3)
def gate_ch03_core(pos, wt, mt, ctx):
    """Ch3: Core integrity — SYMMETRY COMPLETE (v17 + V<->I v18 patch)."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'

    # V18 PATCH: V<->I swap exemption (beta-branched aliphatic isomer)
    if (wt == 'V' and mt == 'I') or (wt == 'I' and mt == 'V'):
        return 'O'

    bur = c['bur']
    ss = c['ss']

    # ═══ Tier S: Backbone/geometry (position-independent) ═══

    if mt == 'G' and wt != 'G' and bur > 0.5:
        return 'C'

    if wt in ('M', 'C') and mt not in ('M', 'C') and c['n_aro'] >= 1 and bur > 0.5:
        return 'C'

    if wt == 'M' and mt not in ('M', 'C') and c['n_sul'] >= 3:
        return 'C'

    if ss == 'E' and wt in BETA_BRANCHED and mt not in BETA_BRANCHED and bur > 0.5:
        return 'C'

    hw = AA_HYDRO.get(wt, 0)
    hm = AA_HYDRO.get(mt, 0)
    if hw < -1 and hm > 1 and bur > 0.7:
        return 'C'

    # ═══ Surface Hydrophobic Exposure Gate ═══
    if bur < 0.5 and hw > 1.0:
        vl_surface = AA_VOLUME.get(wt, 130) - AA_VOLUME.get(mt, 130)
        if vl_surface > 20:
            return 'C'
        if hm < 0:
            return 'C'

    if bur < 0.5:
        return 'O'

    # ═══ Volume change (symmetric) ═══
    vl = max(0, AA_VOLUME.get(wt, 130) - AA_VOLUME.get(mt, 130))
    vg = max(0, AA_VOLUME.get(mt, 130) - AA_VOLUME.get(wt, 130))
    hl = max(0, AA_HYDRO.get(wt, 0) - AA_HYDRO.get(mt, 0))
    pv = compute_pvoid('cavity', c['lf'], c['pf'], c['hnf'], c['bnf'])
    E_cav = C_CAVITY * pv * vl * bur**2 + C_HYDRO_TRANSFER * hl * bur
    E_steric = C_CAVITY * pv * vg * bur**2

    al = wt in AROMATIC_SET and mt not in AROMATIC_SET
    ci = (mt in CHARGE_AA and wt not in CHARGE_AA)
    cl = (wt in CHARGE_AA and mt not in CHARGE_AA)
    dry = bur * (1 - c['pf'])
    dhb = (AA_HBDON.get(wt, 0) + AA_HBACC.get(wt, 0)) - (AA_HBDON.get(mt, 0) + AA_HBACC.get(mt, 0))

    if E_cav > 1.5:
        return 'C'
    if E_cav > 0.5 and al:
        return 'C'
    if E_cav > 0.8 and bur > 0.9:
        return 'C'
    if ss == 'E' and E_cav > 0.5 and bur > 0.85:
        return 'C'

    if E_steric > 1.5:
        return 'C'
    if E_steric > 0.5 and bur > 0.85:
        return 'C'

    if ss in ('C', 'T') and (E_cav + E_steric) > 0.5 and bur > 0.7:
        return 'C'

    # ═══ Charge gates ═══
    if ci and bur > 0.7 and dry > 0.4:
        return 'C'
    elif ci and bur > 0.5 and dry > 0.3:
        return 'C'
    if cl and bur > 0.7:
        return 'C'
    q_w = AA_CHARGE.get(wt, 0)
    q_m = AA_CHARGE.get(mt, 0)
    if abs(q_w) > 0.3 and abs(q_m) > 0.3 and q_w * q_m < 0 and bur > 0.7:
        return 'C'

    # ═══ Hydrophobicity gates ═══
    if hw > 0.5 and hm < 0 and (hw - hm) > 2 and bur > 0.7:
        return 'C'
    if hw < 0 and hm > 1 and (hm - hw) > 2 and bur > 0.7:
        return 'C'

    # ═══ H-bond gates ═══
    if dhb >= 1 and bur > 0.7:
        return 'C'
    if dhb <= -2 and bur > 0.7:
        return 'C'

    # ═══ Aromatic gates ═══
    if wt not in AROMATIC_SET and mt in AROMATIC_SET and bur > 0.7:
        return 'C'

    # ═══ Electrostatic Keystone Gate ═══
    if c['aa'] in 'DEKR' and c['n_charged_nb'] >= 4:
        return 'C'

    if E_cav > 0.5 or E_steric > 0.5:
        return 'P'
    return 'O'
