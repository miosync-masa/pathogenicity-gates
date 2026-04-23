"""
Ch01_DNA: DNA contact disruption.

Physics: Mutations at DNA-contacting residues disrupt sequence-specific
recognition. Fired by charge loss, H-bond loss, or charge introduction
near the DNA double helix.
"""
from ...physics.constants import AA_CHARGE, AA_HBDON, AA_HBACC
from ..registry import register_channel


@register_channel(id="Ch01_DNA", regime="structural", order=1)
def gate_ch01_dna(pos, wt, mt, ctx):
    """Ch1: DNA contact disruption."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'
    d = c['d_dna']
    if d > 8:
        return 'O'
    dq = AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0)
    dhb = (AA_HBDON.get(wt, 0) + AA_HBACC.get(wt, 0)) - (AA_HBDON.get(mt, 0) + AA_HBACC.get(mt, 0))
    if d < 3.5:
        if wt in 'RK' and mt not in 'RK':
            return 'C'
        if dhb >= 1:
            return 'C'
        if abs(dq) > 0.5:
            return 'C'
    if d < 6:
        if dq < -0.5:
            return 'C'
        if wt in 'RK' and mt not in 'RKH':
            return 'C'
        if dhb >= 2:
            return 'C'
    return 'O'
