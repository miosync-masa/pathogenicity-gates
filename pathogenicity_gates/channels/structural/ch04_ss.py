"""
Ch04_SS: Secondary structure disruption.

Physics: Helix/Beta propensity changes + backbone strain energy + Pro
introduction/loss constraints on SS-dependent backbone stability.
"""
from ...physics.constants import HELIX_PROP, BETA_PROP, CHARGE_AA
from ...physics.corrections import calc_backbone_strain
from ..registry import register_channel


@register_channel(id="Ch04_SS", regime="structural", order=4)
def gate_ch04_ss(pos, wt, mt, ctx):
    """Ch4: Secondary structure disruption."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'
    ss = c['ss']
    bur = c['bur']

    if ss == 'H':
        dp = HELIX_PROP.get(mt, 0.3) - HELIX_PROP.get(wt, 0.3)
        ici = (mt in CHARGE_AA and wt not in CHARGE_AA)
        ipi = (mt in {'S', 'T', 'N', 'Q', 'D', 'E', 'K', 'R', 'H', 'Y', 'W', 'C'}
               and wt not in {'S', 'T', 'N', 'Q', 'D', 'E', 'K', 'R', 'H', 'Y', 'W', 'C'})
        st = calc_backbone_strain(wt, mt, 'H', c['hpos'], ici, ipi)
        if dp < -0.30 and bur > 0.3:
            return 'C'
        if st < -0.5 and bur > 0.3:
            return 'C'
        if mt == 'P' and c['hpos'] == 'core':
            return 'C'
        if wt == 'P' and mt != 'P' and c['hpos'] in ('cap', 'core'):
            return 'C'
        if dp < -0.15 and bur > 0.5:
            return 'P'

    elif ss == 'E':
        dp = BETA_PROP.get(mt, 0.3) - BETA_PROP.get(wt, 0.3)
        if dp < -0.30 and bur > 0.5 and c['bnf'] > 0.3:
            return 'C'
        if dp < -0.50 and bur > 0.3:
            return 'C'
        if wt == 'P' and mt != 'P' and bur > 0.5:
            return 'C'
        if dp < -0.20 and bur > 0.5:
            return 'P'

    return 'O'
