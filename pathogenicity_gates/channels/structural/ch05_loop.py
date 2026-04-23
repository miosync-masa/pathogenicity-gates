"""
Ch05_Loop: Loop Ramachandran constraints.

Physics: Tier S — Pro->X ANYWHERE releases Ramachandran constraint.
Gly->X in L2/L3 loops = catastrophic. X->Pro in secondary structure =
catastrophic. Loop anchor positions demand specific properties.

NOTE: LOOP_L2_L3 and LOOP_ANCHORS are currently p53-hardcoded.
Phase 4 will move them to YAML (annotation.loop_ranges).
"""
from ...physics.constants import AA_CHARGE, AA_VOLUME
from ...physics.corrections import correction_gly, correction_pro
from ..registry import register_channel

# p53-specific. TODO(Phase 4): move to annotation.yaml.
LOOP_L2_L3 = set(range(163, 176)) | set(range(237, 251))
LOOP_ANCHORS = {245, 249, 163, 236, 164, 248, 175, 242, 176}


@register_channel(id="Ch05_Loop", regime="structural", order=5)
def gate_ch05_loop(pos, wt, mt, ctx):
    """Ch5: Loop / Ramachandran gate."""
    c = ctx.get_residue(pos)
    if c is None:
        return 'O'
    ss = c['ss']

    # Gly->X in loop
    if wt == 'G' and mt != 'G' and pos in LOOP_L2_L3:
        return 'C'
    if wt == 'G' and mt != 'G':
        eg = correction_gly('G', mt, c['dcb'], 90, c['nbr'])
        if abs(eg) > 0.5:
            return 'C'

    # X->Pro introduction
    if mt == 'P' and wt != 'P':
        if ss in 'HE':
            return 'C'
        elif pos in LOOP_L2_L3:
            return 'C'
        else:
            ep = correction_pro(wt, 'P')
            if abs(ep) > 0.3:
                return 'P'

    # Tier S: Pro->X ANYWHERE
    if wt == 'P' and mt != 'P':
        return 'C'

    # Loop anchors
    if pos in LOOP_ANCHORS:
        dq = abs(AA_CHARGE.get(mt, 0) - AA_CHARGE.get(wt, 0))
        dv = abs(AA_VOLUME.get(mt, 130) - AA_VOLUME.get(wt, 130))
        if dq > 0.5 or dv > 50:
            return 'C'
        if dq > 0.05 or dv > 20:
            return 'P'

    return 'O'
