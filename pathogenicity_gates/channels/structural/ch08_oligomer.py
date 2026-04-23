"""
Ch08_Oligomer: Oligomerization interface disruption (tetramer for p53).

Physics: SCC exposure gate + rigid hub detection.
  - Demand = max(dq, dv/80, dh/6) captures physicochemical perturbation
  - Exposure-dependent thresholds distinguish dimer interface vs. core
  - Rigid Hub: residue contacting >= 2 partner chains = rigid core (Tier S)
"""
from ...physics.constants import AA_CHARGE, AA_VOLUME, AA_HYDRO
from ..registry import register_channel


@register_channel(id="Ch08_Oligomer", regime="structural", order=8)
def gate_ch08_oligomer(pos, wt, mt, ctx):
    """Ch8: Tetramer/oligomer interface disruption."""
    if pos not in ctx.tet_interface:
        return 'O'
    dq = abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0))
    dv = abs(AA_VOLUME.get(mt, 130) - AA_VOLUME.get(wt, 130))
    dh = abs(AA_HYDRO.get(mt, 0) - AA_HYDRO.get(wt, 0))
    demand = max(dq, dv / 80, dh / 6)
    exp = ctx.tet_exposure.get(pos, 0)

    if demand > 0.3 and exp > 0.5 and (dq > 0.5 or dv > 30 or dh > 2.0):
        return 'C'
    if demand > 0.3 and exp > 0.3 and (dq > 0.5 or dv > 30):
        return 'C'
    if exp <= 0.5 and demand > 0.8 and dq > 0.5 and dv > 30:
        return 'C'

    # Rigid Hub Gate (Tier S)
    if ctx.tet_chain_contacts.get(pos, 0) >= 2 and demand > 0.3:
        return 'C'

    return 'O'
