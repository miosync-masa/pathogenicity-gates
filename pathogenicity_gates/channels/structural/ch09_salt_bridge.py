"""
Ch09_SaltBridge: Surface salt bridge network disruption.

Physics: Tier S (benign=0) — surface residue with salt-bridge partner
plus charge change > 0.5 = CLOSED.
"""
from ...physics.constants import AA_CHARGE
from ..registry import register_channel


@register_channel(id="Ch09_SaltBridge", regime="structural", order=9)
def gate_ch09_salt_bridge(pos, wt, mt, ctx):
    """Ch9: Surface salt bridge network disruption."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'
    if c['bur'] > 0.5:
        return 'O'
    sb_partners = ctx.sb_partners
    if pos not in sb_partners or len(sb_partners[pos]) == 0:
        return 'O'
    if abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0)) > 0.5:
        return 'C'
    return 'O'
