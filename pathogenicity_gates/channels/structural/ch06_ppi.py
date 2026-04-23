"""
Ch06_PPI: Protein-protein interface disruption.

Physics: Sub-gate architecture based on 16 PDB complexes.
  A: Multi-structure confirmed (n_pdbs >= 3)
  B: Direct contact (min_d < 3.5 A)
  C: Interface core (ppi_nb_count >= 5)
"""
from ...physics.constants import AA_CHARGE, AA_VOLUME, AA_HYDRO
from ..registry import register_channel


@register_channel(id="Ch06_PPI", regime="structural", order=6)
def gate_ch06_ppi(pos, wt, mt, ctx):
    """Ch6: PPI interface disruption."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'
    if c['bur'] > 0.7:
        return 'O'
    PPI = ctx.ppi_union
    if pos not in PPI:
        return 'O'

    n_pdbs = len(PPI[pos])
    min_d = min(PPI[pos].values())
    pnb = ctx.ppi_nb_count.get(pos, 0)
    dq = abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0))
    dv = abs(AA_VOLUME.get(mt, 130) - AA_VOLUME.get(wt, 130))
    dh = abs(AA_HYDRO.get(mt, 0) - AA_HYDRO.get(wt, 0))

    if n_pdbs >= 3 and (dq > 0.5 or dh > 2.0 or dv > 30):
        return 'C'
    if min_d < 3.5 and (dq > 0.5 or dh > 2.5):
        return 'C'
    if pnb >= 5 and (dq > 0.5 or dv > 30):
        return 'C'

    return 'O'
